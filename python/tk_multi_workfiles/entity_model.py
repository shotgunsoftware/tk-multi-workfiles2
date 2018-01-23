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
from sgtk.platform.qt import QtGui, QtCore

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel
ShotgunDataHandlerCache = shotgun_model.data_handler_cache.ShotgunDataHandlerCache

from .util import get_sg_entity_name_field

logger = sgtk.platform.get_logger(__name__)


class ShotgunUpdatableEntityModel(ShotgunEntityModel):
    """
    A Shotgun Entity model with updatable filters and deferred queries.
    """
    _SG_ITEM_SORT_ROLE = ShotgunEntityModel._SG_ITEM_UNIQUE_ID + 50
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
        # Please note that some of these members already exist as private members
        # in the base implementation without any accessor.
        self._entity_type = entity_type
        self._original_filters = filters
        self._hierarchy = hierarchy
        self._fields = fields
        self._deferred_query = deferred_query
        self._extra_filters = None
        self._entity_types = set()
        self._task_step_icons = {}
        super(ShotgunUpdatableEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )
        self._deferred_cache = ShotgunDataHandlerCache()
        self._deferred_models = {}

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

    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        super(ShotgunUpdatableEntityModel, self).async_refresh()
        if self._deferred_query:
            # Refresh our deferred cache
            # Get the full list of uids
            uids = [uid for uid in self._deferred_cache.uids]
            # Retrieve parents for these uids
            affected_parents = set()
            for uid in uids:
                item = self._get_item_by_unique_id(uid)
                if item and item.parent():
                    # Let the parent re-fetch children
                    item.parent().setData(False, self._SG_ITEM_FETCHED_MORE)

    def load_and_refresh(self, extra_filters=None):
        """
        Load the data for this model and post a refresh.

        :param extra_filters: A list of additional Shotgun filters which are added
                              to the initial filters.
        """
        self._extra_filters = extra_filters
        if not self._deferred_query:
            filters = self._original_filters[:] # Copy the list to not update the reference
            if extra_filters:
                filters.append(extra_filters)
        else:
            # Extra filter is not applied to the model containing top nodes
            # for deferred queries.
            filters = self._original_filters
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
        if not self._deferred_query:
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
        else:
            # Refresh our deferred cache.
            # Get the full list of expanded parent uids
            uids = [uid for uid in self._deferred_cache.get_child_uids(parent_uid=None)]
            # And simply ask them to refetch their children.
            for uid in uids:
                item = self._get_item_by_unique_id(uid)
                if item:
                    self.fetchMore(item.index())
            return

    def _add_deferred_item(self, parent_item, uid, name_field, sg_data, order_key):
        """
        Add a child item under the given parent for the given Shotgun record
        loaded from a deferred query.

        :param parent_item: A :class:`ShotgunStandardItem` instance.
        :param str uid: A unique id for the new item.
        :param name_field: A field name from which the Entity name can be retrieved.
        :param sg_data: A Shotgun Entity dictionary.
        """
        parent_uid = parent_item.data(self._SG_ITEM_UNIQUE_ID)
        self._deferred_cache.add_item(
            parent_uid=None,
            sg_data={},
            field_name="",
            is_leaf=False,
            uid=parent_uid,
        )
        created = self._deferred_cache.add_item(
            parent_uid=parent_uid,
            sg_data=sg_data,
            field_name=name_field,
            is_leaf=True,
            uid=uid,
        )
        if created:
            sub_item = self._create_item(
                parent=parent_item,
                data_item=self._deferred_cache.get_entry_by_uid(uid),
            )
            sub_item.setData(True, self._SG_ITEM_FETCHED_MORE)
            sub_item.setData(order_key, self._SG_ITEM_SORT_ROLE)

            if sg_data["type"] == "Task" and "step" in sg_data and sg_data["step"]:
                sg_step = sg_data["step"]
                sub_item.setToolTip(
                    "%s, Step '%s'" % (sub_item.toolTip(), sg_step["name"])
                )
                # We don't have the step in the item hierarchy, we use the icon to
                # highlight the Step the Task is linked to.
                step_id = sg_step["id"]
                if step_id in self._task_step_icons:
                    # If we already have such an icon for the given step, just
                    # re-use it.
                    sub_item.setIcon(self._task_step_icons[step_id])
                else:
                    # Otherwise, build a new one combinining the two icons
                    # and cache it.
                    step_icon = self._get_default_thumbnail(sg_step)
                    size = step_icon.availableSizes()[-1]
                    step_pixmap = step_icon.pixmap(size)
                    task_step_icon = sub_item.icon()
                    size = step_icon.availableSizes()[-1]
                    task_pixmap = sub_item.icon().pixmap(size)
                    source_rect = QtCore.QRectF(
                        0.0, 0.0,
                        step_pixmap.width(),
                        step_pixmap.height()
                    )
                    target_rect = QtCore.QRectF(
                        task_pixmap.width() * 0.5,
                        task_pixmap.height() * 0.5,
                        task_pixmap.width() * 0.5,
                        task_pixmap.height() * 0.5
                    )
                    painter = QtGui.QPainter(task_pixmap)
                    try:
                        painter.setCompositionMode(
                            QtGui.QPainter.CompositionMode_Xor
                        )
                        painter.drawPixmap(target_rect, step_pixmap, source_rect)
                        self._task_step_icons[step_id] = QtGui.QIcon(task_pixmap)
                        sub_item.setIcon(self._task_step_icons[step_id])
                    finally:
                        painter.end()

    @classmethod
    def _dummy_place_holder_item_uid(cls, parent_item, refreshing):
        """
        Return a unique id which can be used for a dummy "Not Found" item under
        the given parent item.

        :param parent_item: A :class:`ShotgunStandardItem` instance.
        :returns: A string.
        """
        return "_dummy_item_uid%s_%s" % (
            "_refreshing" if refreshing else "",
            parent_item.data(cls._SG_ITEM_UNIQUE_ID)
        )

    def _add_dummy_place_holder_item(self, parent_item, refreshing):
        """
        Create a dummy child item under the given item.

        These items are used in tree views to show that a deferred query didn't
        return any Shotgun record or that the data is being refreshed from Shotgun.

        :param parent_item: A :class:`ShotgunStandardItem` instance.
        :returns: A string, the unique id for the item.
        """
        parent_uid = parent_item.data(self._SG_ITEM_UNIQUE_ID)
        self._deferred_cache.add_item(
            parent_uid=None,
            sg_data={},
            field_name="",
            is_leaf=False,
            uid=parent_uid,
        )
        uid = self._dummy_place_holder_item_uid(parent_item, refreshing)
        if refreshing:
            text = "Retrieving %ss..." % self._deferred_query["entity_type"]
        else:
            text = "No %ss" % self._deferred_query["entity_type"]
        created = self._deferred_cache.add_item(
            parent_uid=parent_uid,
            # We need to use something which looks like a SG Entity dictionary.
            # By having a "text" key and using it for the field name, the tree
            # view will display its contents.
            sg_data={
                "text": text,
                "type": ""
            },
            field_name="text",
            is_leaf=True,
            uid=uid,
        )
        if created:
            sub_item = self._create_item(
                parent=parent_item,
                data_item=self._deferred_cache.get_entry_by_uid(uid),
            )
            sub_item.setData(True, self._SG_ITEM_FETCHED_MORE)
            # This item can't be used.
            sub_item.setSelectable(False)
            sub_item.setEnabled(False)
            # We don't want an icon to appear in the view.
            sub_item.setIcon(QtGui.QIcon())
        return uid

    def _run_deferred_query_for_entity(self, sg_entity):
        """
        Run the deferred Shotgun query for the given entity.

        :returns: A list of Shotgun results, as returned by a Shotgun `find` call.
        """
        deferred_query = self._deferred_query
        if not deferred_query:
            return []
        filters = deferred_query["filters"][:]
        link_field_name = deferred_query["link_field"]
        filters.append([link_field_name, "is", sg_entity])
        if self._extra_filters:
            filters.append(self._extra_filters)
        name_field = get_sg_entity_name_field(deferred_query["entity_type"])
        if sg_entity["id"] not in self._deferred_models:
            self._deferred_models[sg_entity["id"]] = ShotgunEntityModel(
                deferred_query["entity_type"],
                filters,
                hierarchy=[link_field_name, name_field],
                fields=deferred_query["fields"] + [name_field, link_field_name],
                parent=self,
            )
            self._deferred_models[sg_entity["id"]].data_refreshed.connect(
                lambda changed : self._on_deferred_data_refreshed(sg_entity, changed)
            )
            self._deferred_models[sg_entity["id"]].async_refresh()
        else:
            self._deferred_models[sg_entity["id"]]._load_data(
                deferred_query["entity_type"],
                filters,
                hierarchy=[link_field_name, name_field],
                fields=deferred_query["fields"] + [name_field, link_field_name],
            )
        self._on_deferred_data_refreshed(sg_entity, True, True)
        self._deferred_models[sg_entity["id"]].async_refresh()

    def _on_deferred_data_refreshed(self, sg_entity, changed, pending_refresh=False):
        """
        Called when new data is available in a deferred Shotgun model for a given
        Entity.

        :param dict sg_entity: A Shotgun Entity with at least "type" and "id" keys.
        :param bool changed: Whether or not the data in the model was changed.
        :param bool pending_refresh: Whether or not a data refresh has been posted,
                                     so refreshed data is expected later.
        """
        parent_item = self.item_from_entity(sg_entity["type"], sg_entity["id"])
        if not parent_item:
            logger.info("Invalid Parent item %s" % parent_item)
            return
        # We use our own deferred cache to avoid conflicts with ShotgunModel so
        # we can manipulate it freely.
        parent_uid = parent_item.data(self._SG_ITEM_UNIQUE_ID)
        if self._deferred_cache.item_exists(parent_uid):
            # Grab all entries from the iterator
            existing_uids = [x for x in self._deferred_cache.get_child_uids(parent_uid)]
        else:
            existing_uids = []

        sub_entities = []
        deferred_model = self._deferred_models[sg_entity["id"]]
        sub_entity_type = deferred_model.get_entity_type()
        name_field = get_sg_entity_name_field(sub_entity_type)
        # Loop over all entities (leaves) in the deferred model.
        for sub_entity_id in deferred_model.entity_ids:
            sub_item = deferred_model.item_from_entity(sub_entity_type, sub_entity_id)
            if sub_item:
                sg_data = sub_item.get_sg_data()
                if sg_data:
                    sub_entities.append(sg_data)
        refreshed_uids = []
        # Ideallly we would retrieve the field list from the ShotgunEntityModel
        # but this is a private member.
        deferred_query = self._deferred_query
        fields = deferred_query["fields"] + [name_field]
        for sub_entity in sub_entities:
            uid = self._deferred_entity_uid(sub_entity)
            refreshed_uids.append(uid)
            # Build a key used to sort the items based on the fields specified
            # in the deferred query settings
            order_keys = []
            for field in fields:
                field_value = sub_entity[field]
                # Special case for dictionaries which are linked entities: use
                # the name field value.
                if isinstance(field_value, dict) and "name" in field_value:
                    order_keys.append("%s" % field_value["name"])
                else:
                    order_keys.append("%s" % field_value)
            self._add_deferred_item(
                parent_item, uid, name_field, sub_entity, "_".join(order_keys)
            )
        if not sub_entities:
            # If we don't have any Entity, add a "Retrieving XXXXXs" or
            # "No XXXXs found" child, depending on `pending_refresh` value.
            uid = self._add_dummy_place_holder_item(parent_item, pending_refresh)
            refreshed_uids.append(uid)
        # Go through the existing items and discard the ones which shouldn't be
        # there anymore.
        for uid in existing_uids:
            if uid in refreshed_uids:
                # Here we could update items from the refreshed data
                continue
            data_item = self._deferred_cache.take_item(uid)
            item = self._get_item_by_unique_id(uid)
            if not item:
                logger.warning("Unable to find item with uid %s" % uid)
            else:
                parent = item.parent()
                if parent:
                    parent.removeRow(item.row())

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

    def _create_item(self, parent, data_item):
        """
        Override the base implementation to ensure we always have a valid value
        for the _SG_ITEM_SORT_ROLE by copying over the Qt.DisplayRole value.
        """
        item = super(ShotgunUpdatableEntityModel, self)._create_item(parent, data_item)
        item.setData(item.data(QtCore.Qt.DisplayRole), self._SG_ITEM_SORT_ROLE)
        return item

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
        # Get a fresh and empty deferred cache.
        self._deferred_cache = ShotgunDataHandlerCache()

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
        return

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
