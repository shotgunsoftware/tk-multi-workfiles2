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
from sgtk.platform.qt import QtGui

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel
ShotgunDataHandlerCache = shotgun_model.data_handler_cache.ShotgunDataHandlerCache

from .util import get_sg_entity_name_field

logger = sgtk.platform.get_logger(__name__)


class ShotgunUpdatableEntityModel(ShotgunEntityModel):
    """
    A Shotgun Entity model with updatable filters and deferred queries.
    """
    def __init__(self, entity_type, filters, hierarchy, fields, deferred_query, *args, **kwargs):
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
        :param deferred_query: A dictionary with the `entity_type`, `filter` and
                               `fields` allowing to run a Shotgun sub-query for
                               a given entity in this model.
        """
        self._entity_type = entity_type
        self._original_filters = filters
        self._hierarchy = hierarchy
        self._fields = fields
        self._deferred_query = deferred_query
        self._extra_filters = None
        self._entity_types = set()
        super(ShotgunUpdatableEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )
        self._deferred_cache = ShotgunDataHandlerCache()
#        self.data_refreshed.connect(self._on_data_refreshed)

#    def _on_data_refreshed(self, modified):
#        """
#        Called when new data is available.
#
#        Ensure all data in the tree except for the leaves is loaded. By default,
#        only top nodes are automatically added in the model from the retrieved
#        Shotgun data, because loading the full set of data can be slow. However,
#        we need the intermediate nodes in the tree to always be loaded in the
#        model. The assumption here is that by not loading the leaves automatically
#        we will not cause any performance hit.
#
#        :param bool modified: Whether or not some data was changed.
#        """
#        self.ensure_intermediate_data_is_loaded()

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
        if self._deferred_query and self._deferred_query["entity_type"] == "Task":
            return True
        return False

    def update_filters(self, extra_filters):
        """
        Update the filters used by this model.

        A full refresh is triggered by the update.

        :param extra_filters: A list of additional Shotgun filters which are added
                              to the initial filters.
        """
        self._extra_filters = extra_filters
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
        else:
            # Allow all leaves in the model to potentially fetch more data
            entity_type = self.get_entity_type()
            for entity_id in self.entity_ids:
                item = super(ShotgunUpdatableEntityModel, self).item_from_entity(
                    entity_type, entity_id
                )
                if item:
                    item.setData(False, self._SG_ITEM_FETCHED_MORE)

            # Refresh our deferred cache
            # Get the full list of uids
            uids = [uid for uid in self._deferred_cache.uids]
            # Retrieve parents for these uids
            affected_parents = set()
            for uid in uids:
                item = self._get_item_by_unique_id(uid)
                if item and item.parent():
                    affected_parents.add(item.parent())
            # Loop over all affected parents (which were expanded) and refresh
            # them
            name_field = get_sg_entity_name_field(self._deferred_query["entity_type"])
            new_uids = []
            for parent in affected_parents:
                parent.setData(True, self._SG_ITEM_FETCHED_MORE)
                sg_data = parent.get_sg_data()
                if not sg_data:
                    continue
                sub_entities = self._run_deferred_query_for_entity(sg_data)
                for sub_entity in sub_entities:
                    # Keep a list of all uids
                    uid = self._deferred_entity_uid(sub_entity)
                    new_uids.append(uid)
                    # Create new entries if needed
                    if uid in uids:
                        continue
                    self._add_deferred_item(parent, uid, name_field, sub_entity)
            # Discard items which shouldn't be there anymore
            for uid in uids:
                if uid in new_uids:
                    continue
                data_item = self._deferred_cache.take_item(uid)
                item = self._get_item_by_unique_id(uid)
                if not item:
                    logger.warning("Unable to find item with uid %s" % uid)
                else:
                    logger.info("Discarding %s" % item)
                    # Reset the parent canFetchMore
                    parent = item.parent()
                    if parent:
                        parent.removeRow(item.row())

    def _add_deferred_item(self, parent_item, uid, name_field, sg_data):
        self._deferred_cache.add_item(
            parent_uid=None,
            sg_data=sg_data,
            field_name=name_field,
            is_leaf=True,
            uid=uid,
        )
        sub_item = self._create_item(
            parent=parent_item,
            data_item=self._deferred_cache.get_entry_by_uid(uid),
        )
        sub_item.setData(True, self._SG_ITEM_FETCHED_MORE)
        if sg_data["type"] == "Task" and "step" in sg_data:
            # We don't have the step in the item hierarchy, we use the icon to
            # highlight the Step the Task is linked to.
            sub_item.setIcon(self._get_default_thumbnail(sg_data["step"]))

    def _run_deferred_query_for_entity(self, sg_entity):
        """
        Run the deferred Shotgun query for the given entity.

        It is assumed that an "entity" field is available on the target entities
        to link them to the given Shotgun Entity.

        :returns: A list of Shotgun results, as returned by a Shotgun `find` call.
        """
        deferred_query = self._deferred_query
        if not deferred_query:
            return []
        filters = deferred_query["filters"][:]
        filters.append(["entity", "is", sg_entity])
        if self._extra_filters:
            filters.append(self._extra_filters)
        name_field = get_sg_entity_name_field(deferred_query["entity_type"])
        return sgtk.platform.current_bundle().shotgun.find(
            deferred_query["entity_type"],
            filters=filters,
            fields=deferred_query["fields"] + [name_field],
            order=[{
                "field_name": name_field,
                "direction": "asc"
            }]
        )

    @staticmethod
    def _deferred_entity_uid(sg_entity):
        """
        Returns a unique id for the given Entity retrieved in a deferred query.
        """
        # ShotgunModel uses the entity id for leaves, we use the Entity type and
        # its id to avoid clashes in the various internal caches.
        return "%s_%d" % (sg_entity["type"], sg_entity["id"])

    def _finalize_item(self, item):
        """
        Called every time an item was added in the model.
        """
        super(ShotgunUpdatableEntityModel, self)._finalize_item(item)
        # We need to keep track of which entities are in the model, so we can bail
        # out cheaply on entity searches, and not traverse the full model to look
        # for an entity which can't be there.
        entity = self.get_entity(item)
        if entity:
            self._entity_types.add(entity["type"])

    def ensure_intermediate_data_is_loaded(self):
        """
        Ensure all data is loaded in the model, except for the leaves of the tree.

        This allows to load most of the data in the model without a performance
        hit, assuming the hit mostly comes from the leaves.
        """
        max_depth = len(self._hierarchy)
        # Maintain a list of items to traverse with their depth.
        # 0 is the depth for the top items in the model, excluding the invisible
        # root.
        # If we have the following hierarchy for Tasks, we fetch data for only the
        # two first entries (we don't fetch data for the two last entries).
        # [entity.Shot.sg_sequence, entity, step, content]
        if max_depth < 2:
            return
        max_depth -= 2
        item_list = [(self.invisibleRootItem(), -1)]
        while item_list:
            item, depth = item_list.pop()
            if self.canFetchMore(item.index()):
                self.fetchMore(item.index())
            depth += 1
            if depth < max_depth:
                for row_i in range(item.rowCount()):
                    child_item = item.child(row_i)
                    item_list.append((child_item, depth))

    def ensure_data_is_loaded(self, index=None):
        """
        Ensure all data is loaded in the model, except for deferred queries.
        """
        if not self._deferred_query:
            # Just call the base implementation
            return super(ShotgunUpdatableEntityModel, self).ensure_data_is_loaded(index)
        item_list = []
        if index is None:
            # Load everything
            # The top item is not a QStandardItem and we rely on
            # ShotgunStandardItem methods so grab children straightaway.
            for row_i in range(self.invisibleRootItem().rowCount()):
                item_list.append(self.invisibleRootItem().child(row_i))
        else:
            item_list = [self.itemFromIndex(index)]

        while item_list:
            item = item_list.pop()
            if item.get_sg_data():
                # Leaves in the static SG model, stop here otherwise we will trigger
                # deferred queries
                continue
            if self.canFetchMore(item.index()):
                self.fetchMore(item.index())
            for row_i in range(item.rowCount()):
                child_item = item.child(row_i)
                item_list.append(child_item)

    def clear(self):
        """
        Clear the data we hold.
        """
        super(ShotgunUpdatableEntityModel, self).clear()
        self._entity_types = set()

    def hasChildren(self, index):
        """
        """
        if not self._deferred_query or not index.isValid() or not self.itemFromIndex(index).get_sg_data():
            return super(ShotgunUpdatableEntityModel, self).hasChildren(index)
        # Trying to being accurate here does not make any difference for Qt, so let's
        # just always return True.
        return True

    def canFetchMore(self, index):
        """
        Return True if more children can be fetched under the given index.

        :param index: A :class:`QtCore.QModelIndex` instance.
        :returns: A boolean, whether or not more children can be fetched.
        """
        if not self._deferred_query or not index.isValid() or not self.itemFromIndex(index).get_sg_data():
            return super(ShotgunUpdatableEntityModel, self).canFetchMore(index)

        item = self.itemFromIndex(index)
        if item.data(self._SG_ITEM_FETCHED_MORE):
            # More data has already been queried for this item
            return False
        return True

    def fetchMore(self, index):
        """
        Fetch more children under the given index.

        :param index: A :class:`QtCore.QModelIndex` instance.
        """
        if not index.isValid() or not self._deferred_query:
            return super(ShotgunUpdatableEntityModel, self).fetchMore(index)
        item = self.itemFromIndex(index)
        # Set the flag to prevent subsequent attempts to fetch more
        item.setData(True, self._SG_ITEM_FETCHED_MORE)
        sg_data = item.get_sg_data()
        if not sg_data:
            return super(ShotgunUpdatableEntityModel, self).fetchMore(index)
        sub_entities = self._run_deferred_query_for_entity(sg_data)
        name_field = get_sg_entity_name_field(self._deferred_query["entity_type"])
        logger.info("Retrieved %s for %s" % (sg_data, sub_entities))
        for sub_entity in sub_entities:
            uid = self._deferred_entity_uid(sub_entity)
            self._add_deferred_item(item, uid, name_field, sub_entity)

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
            return super(ShotgunUpdatableEntityModel, self).item_from_entity(
                entity_type, entity_id
            )
        logger.info("Doing custom lookup %s" % self.get_entity_type())
        # If we have deferred queries, check the deferred cache
        if self._deferred_query and self._deferred_query["entity_type"] == entity_type:
            logger.info("Deferred query lookup...")
            return self._get_item_by_unique_id(entity_id)

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
        return values[::-1]
