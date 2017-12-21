# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

logger = sgtk.platform.get_logger(__name__)


class ShotgunUpdatableEntityModel(ShotgunEntityModel):
    """
    A Shotgun Entity model with updatable filters and deferred queries.
    """
    def __init__(self, entity_type, filters, hierarchy, fields, deferred_query, *args, **kwargs):
        self._entity_type = entity_type
        self._original_filters = filters
        self._hierarchy = hierarchy
        self._fields = fields
        self._deferred_query = deferred_query
        super(ShotgunUpdatableEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )

    @property
    def deferred_query(self):
        """
        :returns: The deferred query for this model, if any.
        """
        return self._deferred_query

    @property
    def represents_tasks(self):
        """
        :returns: True if this model represents Tasks through deferred query or
                  directly by storing Shotgun Task entities.
        """
        if self.get_entity_type() == "Task":
            return True
        if self._deferred_query and self._deferred_query["query"]["entity_type"] == "Task":
            return True
        return False

    def update_filters(self, extra_filters):
        """
        Update the filters used by this model.

        A full refresh is triggered by the update.

        :param extra_filters: A list of additional Shotgun filters which are added
                              to the initial filters.
        """
        if not self._deferred_query:
            filters = self._original_filters[:] # Copy the list to not update the reference
            if extra_filters:
                filters.append(extra_filters)
            logger.info("Refreshing data with %s -> %s" % (extra_filters, filters))
            self._load_data(
                self._entity_type,
                filters,
                self._hierarchy,
                self._fields
            )
        self.async_refresh()

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
        logger.info("Looking for %s %s..." % (entity_type, entity_id))
        #self.ensure_data_is_loaded()
        # If dealing with the primary entity type this model represent, just
        # call the base implementation.
        if entity_type == self.get_entity_type():
            return super(ShotgunUpdatableEntityModel, self).item_from_entity(
                entity_type, entity_id
            )
        # If not dealing with the primary entity type, we need to traverse the
        # model to find the entity
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
                if entity and entity["type"] == entity_type and entity["id"] == entity_id:
                    return item
                if item.hasChildren():
                    logger.info("Adding %s to parent list" % item)
                    parent_list.append(item)
        return None

    def item_from_field_value(self, item_field_value):
        logger.info("Looking for %s" % item_field_value)
        #self.ensure_data_is_loaded()
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
                value = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
                logger.info("Got %s from %s" % (value, item))
                if value == item_field_value:
                    return item
                if item.hasChildren():
                    logger.info("Adding %s to parent list" % item)
                    parent_list.append(item)

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
        return values[::-1]
