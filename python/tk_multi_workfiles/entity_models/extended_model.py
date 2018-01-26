# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtGui, QtCore

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

logger = sgtk.platform.get_logger(__name__)


class ShotgunExtendedEntityModel(ShotgunEntityModel):
    """
    A Shotgun Entity model with updatable filters and a couple of added methods.
    """
    # Define a custom role used for sorting, we use the highest ShotgunModel role
    # value with a bit of margin in case roles are added later to ShotgunModel
    _SG_ITEM_SORT_ROLE = ShotgunEntityModel._SG_ITEM_UNIQUE_ID + 20

    def __init__(self, entity_type, filters, hierarchy, fields, *args, **kwargs):
        """
        :param entity_type: The type of the entities that should be loaded into this model.
        :param filters: A list of filters to be applied to entities in the model - these
                        will be passed to the Shotgun API find() call when populating the
                        model
        :param hierarchy: List of Shotgun fields that will be used to define the structure
                          of the items in the model.
        :param fields: List of Shotgun fields to populate the items in the model with.
                       These will be passed to the Shotgun API find() call when populating
                       the model.
        """
        # Please note that some of these members already exist as private members
        # in the base implementation without any accessor.
        self._entity_type = entity_type
        self._original_filters = filters
        self._hierarchy = hierarchy
        self._fields = fields
        self._extra_filters = None
        self._entity_types = set()
        super(ShotgunExtendedEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )

    @property
    def represents_tasks(self):
        """
        :returns: True if this model represents Tasks.
        """
        return self.get_entity_type() == "Task"

    @property
    def supports_step_filtering(self):
        """
        :returns: True if Step filtering can be used with this model
        """
        # If don't have steps in the fields we query from Shotgun, we assume
        # step filtering should be disabled.
        return "step" in self._fields or "step" in self._hierarchy

    def load_and_refresh(self, extra_filters=None):
        """
        Load the data for this model and post a refresh.

        :param extra_filters: A list of additional Shotgun filters which are added
                              to the initial filters.
        """
        self._extra_filters = extra_filters
        filters = self._original_filters[:] # Copy the list to not update the reference
        if extra_filters:
            filters.append(extra_filters)
        self._load_data(
            self._entity_type,
            filters,
            self._hierarchy,
            self._fields
        )
        self.async_refresh()

    def update_filters(self, extra_filters):
        """
        Update the filters used by this model.

        A full refresh is triggered by the update if not using deferred queries.
        Otherwise, the filter is applied to all expanded items in the model which
        are direct parent of deferred results.

        :param extra_filters: A list of additional Shotgun filters which are added
                              to the initial filters.
        """
        self._extra_filters = extra_filters
        filters = self._original_filters[:] # Copy the list to not update the reference
        if extra_filters:
            filters.append(extra_filters)
        self._load_data(
            self._entity_type,
            filters,
            self._hierarchy,
            self._fields
        )
        self.async_refresh()

    def _finalize_item(self, item):
        """
        Called every time an item was added in the model.
        """
        super(ShotgunExtendedEntityModel, self)._finalize_item(item)
        # We need to keep track of which entities are in the model, so we can bail
        # out cheaply on entity searches, and not traverse the full model to look
        # for an entity which can't be there.
        entity = self.get_entity(item)
        if entity:
            self._entity_types.add(entity["type"])

    def _create_item(self, parent, data_item):
        """
        Override the base implementation to ensure we always have a valid value
        for the _SG_ITEM_SORT_ROLE by copying over the Qt.DisplayRole value.
        """
        item = super(ShotgunExtendedEntityModel, self)._create_item(parent, data_item)
        item.setData(item.data(QtCore.Qt.DisplayRole), self._SG_ITEM_SORT_ROLE)
        return item

    def clear(self):
        """
        Clear the data we hold.
        """
        super(ShotgunExtendedEntityModel, self).clear()
        self._entity_types = set()

    def ensure_data_for_context(self, context):
        """
        Ensure the data is loaded for the given context.

        This is typically used to load data for the current Toolkit context and
        select a matching item in the tree.

        :param context: A Toolkit context.
        """
        if not context:
            return
        entity_type = self.get_entity_type()
        entity = None
        if entity_type == "Task":
            entity = context.task
        elif context.entity and context.entity["type"] == entity_type:
            # For now only load anything if dealing with leaves: loading intermediate
            # nodes could lead to performance hits, we need to make sure there is
            # a valid use case for doing this.
            entity = context.entity
        if entity:
            # Retrieving the item is enough to ensure it is loaded if available.
            item = self.item_from_entity(entity["type"], entity["id"])

    def item_from_entity(self, entity_type, entity_id):
        """
        Retrieve the item representing the given entity in the model.

        Leaves are only considered if the given Entity type matches the Entity
        type this model represents. Otherwise, the full model hierarchy is traversed
        to retrieve the given Entity.

        .. note::
            The same entity can appear multiple times in the hierarchy, the first
            match is returned.

        :param str entity_type: A Shotgun Entity type.
        :param int entity_id: The Shotgun id of the Entity to look for.
        """
        logger.info("[item_from_entity] Looking for %s %s..." % (entity_type, entity_id))
        # If dealing with the primary entity type this model represents, just
        # call the base implementation which only considers leaves.
        if entity_type == self.get_entity_type():
            logger.info("Falling back on base impl. %s" % self.get_entity_type())
            return super(ShotgunExtendedEntityModel, self).item_from_entity(
                entity_type, entity_id
            )
        # If not dealing with the primary entity type, we need to traverse the
        # model to find the entity.
        # Bail out quickly if we know that the entity type we are looking for is
        # not in this model.
        # Please note that this implies that we need to load all intermediate nodes
        # in the tree to get an accurate list of all the entity types it contains.
        if entity_type not in self._entity_types:
            return None
        # If the model is empty, just bail out
        if not self.rowCount():
            return None
        parent_list = [self.invisibleRootItem()]
        while parent_list:
            parent = parent_list.pop()
            logger.info("Checking items under %s" % parent)
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                entity = self.get_entity(item)
                logger.info("Got %s from %s" % (entity, item))
                # If dealing with an item holding the entity type we're looking
                # for, we don't add it to the list of items to explore. We return
                # it if the id is the one we're looking for.
                if not entity or entity["type"] != entity_type:
                    if item.hasChildren():
                        logger.info("Adding %s to parent list" % item)
                        parent_list.append(item)
                elif entity["id"] == entity_id:
                    return item
        return None

    def item_from_field_value_path(self, field_value_list):
        """
        Retrieve an item from a list of field values identifying its path.

        This allows to retrieve an item in an updated model from a list of
        collected field values representing its path.

        Full or partial matches are performed: if the item represented by the
        given value list is not present in the model anymore, the last item
        matched from the value list is returned.

        :param field_value_list: A list of field values for the path from the
                                 root to the item.
        """
        if not self.rowCount():
            return None
        parent = self.invisibleRootItem()
        for field_value in field_value_list:
            logger.info("Looking for %s under %s" % (field_value, parent))
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                value = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
                logger.info("Got %s from %s" % (value, item))
                if value == field_value:
                    parent = item
                    break
            else:
                logger.warning("Couldn't retrieve %s under %s" % (
                    field_value, parent,
                ))
        return parent

    def get_item_field_value_path(self, item):
        """
        Return a list of field values identifying the absolute path to the given item.

        This can be collected and used later to retrieve the path to the item in an
        updated model.

        :returns: A list of field values for the path from the root to the item.
        """
        current_item = item
        values = []
        while current_item:
            values.append(
                current_item.data(self.SG_ASSOCIATED_FIELD_ROLE)
            )
            current_item = current_item.parent()
        # Reverse the list we return.
        return values[::-1]

    def _get_key_for_field_data(self, field, sg_data):
        """
        Generates a key for a Shotgun field data.

        These keys can be used as uid in caches.

        :param field: a Shotgun field name from the sg_data dictionary.
        :param sg_data: a Shotgun data dictionary.
        :returns: a string key
        """
        # Note: this is a simplified version of tk-framework-shotgunutils
        # ShotgunFindDataHandler.__generate_unique_key method.
        value = sg_data.get(field)

        if isinstance(value, dict) and "id" in value and "type" in value:
            # For single entity links, return the entity id
            unique_key = "%s_%s" % (value["type"], value["id"])
        elif isinstance(value, list):
            # This is a list of some sort. Loop over all elements and extract a comma separated list.
            formatted_values = []
            for v in value:
                if isinstance(v, dict) and "id" in v and "type" in v:
                    # This is a link field
                    formatted_values.append("%s_%s" % (v["type"], v["id"]))
                else:
                    formatted_values.append(str(v))
            unique_key = ",".join(formatted_values)
        else:
            # everything else just cast to string
            unique_key = str(value)
        return unique_key
