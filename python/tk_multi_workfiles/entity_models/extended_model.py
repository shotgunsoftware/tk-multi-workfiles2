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


class ShotgunExtendedEntityModel(ShotgunEntityModel):
    """
    A Shotgun Entity model with updatable filters and the addition of methods to
    maintain the selection of items when the model is refreshed.

    Typical use of an extended model would look like:
     .. code-block:: python
            my_model = ShotgunExtendedEntityModel(
                # Nothing different from the base ShotgunEntityModel class.
                "Task",
                [["entity", "type_is", "Asset"]],
                [entity.Asset.sg_asset_type, entity, step, content],
            )
            # Load the model and refresh it
            my_model.load_and_refresh()
            # Retrieve the path to a selected item retrieved from a view
            selected_path = my_model.get_item_field_value_path(selected_item)
            # Narrow down the list of Tasks with a Step filter which will clear
            # all the data and refresh it in the background.
            my_model.update_filters(["step.Step.code", "is", "Rig"])
            # Retrieve the previously selected item from the saved path to restore
            # the selection in the view.
            selected_item = my_model.item_from_field_value_path(selected_path)
    """

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
        self._extra_filter = None

        # We keep track of which entities are in the model, so we can bail
        # out cheaply on entity searches, and not traverse the full model to look
        # for an entity which can't be there.
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
        # If we don't have steps in the fields we query from Shotgun, we assume
        # step filtering should be disabled.
        return "step" in self._fields or "step" in self._hierarchy

    def load_and_refresh(self, extra_filter=None):
        """
        Load the data for this model and post a refresh.

        :param extra_filter: An additional Shotgun filter which is added
                             to the initial filters list.
        """
        self._extra_filter = extra_filter
        filters = self._original_filters[:] # Copy the list to not update the reference
        if extra_filter:
            filters.append(extra_filter)
        self._load_data(
            self._entity_type,
            filters,
            self._hierarchy,
            self._fields
        )
        self.async_refresh()

    def update_filters(self, extra_filter):
        """
        Update the filters used by this model.

        A full refresh is triggered by the update if not using deferred queries.
        Otherwise, the filter is applied to all expanded items in the model which
        are direct parent of deferred results.

        :param extra_filter: An additional Shotgun filter which is added
                             to the initial filters list.
        """
        self._extra_filter = extra_filter
        filters = self._original_filters[:] # Copy the list to not update the reference
        if extra_filter:
            filters.append(extra_filter)
        self._load_data(
            self._entity_type,
            filters,
            self._hierarchy,
            self._fields
        )
        # If we loaded something from the cache notify viewers that new data is
        # already available.
        if self.invisibleRootItem().rowCount():
            self.data_refreshed.emit(True)
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
            match is returned. A typical example is Pipeline Steps, but this could
            happen as well for some unusual hierarchies, like /Task/Sequence/Shot:
            the same Sequence could appear under different Task.

        :param str entity_type: A Shotgun Entity type.
        :param int entity_id: The Shotgun id of the Entity to look for.
        """
        # If dealing with the primary entity type this model represents, just
        # call the base implementation which only considers leaves.
        if entity_type == self.get_entity_type():
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
        # We modify the list as we iterate on it by adding children, so we can't
        # use a simple iterator here.
        while parent_list:
            parent = parent_list.pop()
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                entity = self.get_entity(item)
                # If dealing with an item holding the entity type we're looking
                # for, we don't add it to the list of items to explore. We return
                # it if the id is the one we're looking for.
                if not entity or entity["type"] != entity_type:
                    if item.hasChildren():
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
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                value = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
                if value == field_value:
                    parent = item
                    break
        return parent

    def get_item_field_value_path(self, item):
        """
        Return a list of field values identifying the absolute path to the given item.

        This can be collected and used later to retrieve the path to the item in an
        updated model.

        The values are the Shotgun fields values which are set by the Shotgun
        Model for the SG_ASSOCIATED_FIELD_ROLE, and therefore depends on which
        Shotgun fields are used in the hierarchy and on their type.
        E.g. for a model retrieving Tasks and with an entity/sg_status_list/task
        hierarchy, the returned list could look like:
        `[{"type": "Shot", "id": 123}, "ip", {"type": "Task", "id": 456}]`.

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
