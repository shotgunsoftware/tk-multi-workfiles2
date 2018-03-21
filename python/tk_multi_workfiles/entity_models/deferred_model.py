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
ShotgunDataHandlerCache = shotgun_model.data_handler_cache.ShotgunDataHandlerCache

shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")

from ..util import get_sg_entity_name_field
from .extended_model import ShotgunExtendedEntityModel


class ShotgunDeferredEntityModel(ShotgunExtendedEntityModel):
    """
    A Shotgun Entity model which supports two steps for loading data:
    - A primary request is used to populate top nodes in the tree, like for
      a regular Shotgun Entity Model.
    - Secondary requests are deferred until the point the data really needs
      to be fetched, typically when a leaf in the primary model is expanded.
      The primary tree is then extended with child items dynamically retrieved
      on demand with the deferred queries.

    Deferred queries need to specify:
      - The target entity type for the query, e.g. 'Task'.
      - The field name to link the secondary query to the primary one, e.g.
        'entity'.
    A sub-hierarchy can be defined with a list of fields, e.g. ['step'].
    If needed, additional filters can be specified for deferred queries.

    Typical use of a deferred model would look like:
     .. code-block:: python
            my_model = ShotgunDeferredEntityModel(
                # Main query: retrieve Shots and group them by Sequences.
                "Shot",
                [],
                ["sg_sequence", "code"],
                # Deferred query: retrieve Tasks using the "entity" field to retrieve
                # Tasks for a given Shot, group Tasks by their pipeline Step.
                {
                    "entity_type": "Task",
                    "link_field": "entity",
                    "filters": []
                    hierarchy": ["step"]
                }
            )
            # Load the model and refresh it
            my_model.load_and_refresh()
            # Narrow down the list of Tasks with a Step filter.
            my_model.update_filters(["step.Step.code", "is", "Rig"])
    """

    def __init__(self, entity_type, filters, hierarchy, fields, deferred_query, *args, **kwargs):
        """
        Construct a ShotgunDeferredEntityModel.

        :param entity_type: The type of the entities that should be loaded into this model.
        :param filters: A list of filters to be applied to entities in the model - these
                        will be passed to the Shotgun API find() call when populating the
                        model
        :param hierarchy: List of Shotgun fields that will be used to define the structure
                          of the items in the model.
        :param fields: List of Shotgun fields to populate the items in the model with.
                       These will be passed to the Shotgun API find() call when populating
                       the model.
        :param deferred_query: A dictionary with the `entity_type`, `link_field`
                               `filters` and `hierarchy` keys, allowing to run a
                               Shotgun sub-query for a given entity in this model.
        """
        # Basic sanity check that we do have a deferred query, so we don't have
        # to test it everywhere.
        if not deferred_query:
            raise ValueError("A non empty deferred query is required")

        self._deferred_query = deferred_query
        self._task_step_icons = {}
        self._deferred_models = {}
        # A bool used to track if a data_refreshed signal emission has been posted
        # in the event queue, to ensure there is only one at any given time.
        self._pending_delayed_data_refreshed = False
        super(ShotgunDeferredEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )
        # Create a cache to handle results from deferred queries.
        self._deferred_cache = ShotgunDataHandlerCache()

    @property
    def deferred_query(self):
        """
        :returns: The deferred query for this model.
        """
        return self._deferred_query

    @property
    def represents_tasks(self):
        """
        :returns: True if this model represents Tasks through deferred query.
        """
        return self._deferred_query["entity_type"] == "Task"

    @property
    def supports_step_filtering(self):
        """
        :returns: True if Step filtering can be used with this model
        """
        # If we don't have steps in the fields we query from Shotgun, we assume
        # step filtering should be disabled.
        return "step" in self._deferred_query["hierarchy"]

    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        # Refresh the primary cache.
        super(ShotgunDeferredEntityModel, self).async_refresh()
        # Refresh our deferred cache
        # Get the full list of uids
        uids = [uid for uid in self._deferred_cache.uids]
        # Retrieve parents for these uids in the model.
        for uid in uids:
            item = self._get_item_by_unique_id(uid)
            if item and item.parent():
                # Let the parent re-fetch children
                item.parent().setData(False, self._SG_ITEM_FETCHED_MORE)

    def load_and_refresh(self, extra_filter=None):
        """
        Load the data for this model and post a refresh.

        The given extra filter will be added to deferred queries initial filters
        list when fetching deferred results.

        :param extra_filter: An additional Shotgun filter which is added
                             to the initial filters list for the deferred queries.
        """
        self._extra_filter = extra_filter
        # Extra filter is not applied to the model containing top nodes
        # for deferred queries.
        self._load_data(
            self._entity_type,
            self._original_filters,
            self._hierarchy,
            self._fields
        )
        self.async_refresh()

    def ensure_data_for_context(self, context):
        """
        Ensure the data is loaded for the given context.

        This is typically used to load data for the current Toolkit context and
        select a matching item in the tree.

        :param context: A Toolkit context.
        """
        if context.entity and context.entity["type"] == self.get_entity_type():
            # If we have an entity in our context, check if we have it in our
            # "static" model.
            item = self.item_from_entity(context.entity["type"], context.entity["id"])
            if item:
                # Fetch children if not done yet.
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())

    def update_filters(self, extra_filter):
        """
        Update the deferred filters used by this model.

        The given extra filter is added to the initial deferred query filters
        list to fetch deferred results.

        All expanded items in the model which are direct parent of deferred results
        are flagged as needing to be refreshed.

        :param extra_filter: An additional Shotgun filter which is added
                             to the initial filters list for the deferred queries.
        """
        self._extra_filter = extra_filter
        # Refresh our deferred cache.
        # Get the full list of expanded parent uids
        uids = [uid for uid in self._deferred_cache.get_child_uids(parent_uid=None)]
        # And simply tell them to refetch their children.
        for uid in uids:
            item = self._get_item_by_unique_id(uid)
            if item:
                self.fetchMore(item.index())

    def clear(self):
        """
        Clear the data we hold.
        """
        self._deferred_cache = ShotgunDataHandlerCache()
        for deferred_model in self._deferred_models.itervalues():
            deferred_model.clear()
        self._deferred_models = {}
        super(ShotgunDeferredEntityModel, self).clear()

    def destroy(self):
        """
        Destroy this model and any deferred models attached to it.
        """
        for deferred_model in self._deferred_models.itervalues():
            deferred_model.destroy()
        self._deferred_models = {}
        super(ShotgunDeferredEntityModel, self).destroy()

    def _add_deferred_item_hierarchy(self, parent_item, hierarchy, name_field, sg_data):
        """
        Add a hierarchy of items under the given parent for the given Shotgun record
        loaded from a deferred query.

        :param parent_item: A :class:`ShotgunStandardItem` instance.
        :param hierarchy: A list of Shotgun field names defining the tree structure
                          to build under the parent item.
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
        refreshed_uids = []
        current_item = parent_item
        current_uid = parent_uid
        for name in hierarchy:
            # We cache items directly under a single parent to retrieve them
            # easily.
            uid = "%s/%s" % (parent_uid, self._get_key_for_field_data(name, sg_data))
            refreshed_uids.append(uid)
            exists = self._deferred_cache.item_exists(uid)
            # Update or create the cached data item
            updated = self._deferred_cache.add_item(
                parent_uid=current_uid,
                sg_data=sg_data,
                field_name=name,
                is_leaf=False,
                uid=uid,
            )
            if not exists:
                # Create the model item if it didn't exist
                current_item = self._create_item(
                    parent=current_item,
                    data_item=self._deferred_cache.get_entry_by_uid(uid),
                )
                current_item.setData(True, self._SG_ITEM_FETCHED_MORE)
            else:
                current_item = self._get_item_by_unique_id(uid)

        uid = self._deferred_entity_uid(sg_data)
        refreshed_uids.append(uid)
        exists = self._deferred_cache.item_exists(uid)
        # Update or create the cached data item
        self._deferred_cache.add_item(
            parent_uid=current_uid,
            sg_data=sg_data,
            field_name=name_field,
            is_leaf=True,
            uid=uid,
        )
        if not exists:
            # Create the model item if it didn't exist
            current_item = self._create_item(
                parent=current_item,
                data_item=self._deferred_cache.get_entry_by_uid(uid),
            )
            current_item.setData(True, self._SG_ITEM_FETCHED_MORE)
        return refreshed_uids

    @classmethod
    def _dummy_placeholder_item_uid(cls, parent_item):
        """
        Return a unique id which can be used for a dummy "Not Found" item under
        the given parent item.

        :param parent_item: A :class:`ShotgunStandardItem` instance.
        :returns: A string.
        """
        return "_dummy_item_uid_%s" % (
            parent_item.data(cls._SG_ITEM_UNIQUE_ID)
        )

    def _add_dummy_placeholder_item(self, parent_item, refreshing):
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
        uid = self._dummy_placeholder_item_uid(parent_item)
        display_name = shotgun_globals.get_type_display_name(
            self._deferred_query["entity_type"]
        )
        if refreshing:
            text = "Retrieving %ss..." % display_name
        else:
            text = "No %ss found" % display_name

        exists = self._deferred_cache.item_exists(uid)
        # Update or create the dummy item in the cache
        self._deferred_cache.add_item(
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
        if not exists:
            # Create the item in the model
            sub_item = self._create_item(
                parent=parent_item,
                data_item=self._deferred_cache.get_entry_by_uid(uid),
            )
            sub_item.setData(True, self._SG_ITEM_FETCHED_MORE)
            # This item can't be used.
            sub_item.setSelectable(False)
            sub_item.setEnabled(False)
            sub_item.setIcon(QtGui.QIcon())
        else:
            sub_item = self._get_item_by_unique_id(uid)
            if sub_item:
                self._update_item(
                    sub_item,
                    self._deferred_cache.get_entry_by_uid(uid)
                )
                # We don't want an icon to appear in the view. Updating the item
                # reset the icon, so we have to reset it after the update.
                sub_item.setIcon(QtGui.QIcon())
        return uid

    def _run_deferred_query_for_entity(self, sg_entity):
        """
        Run the deferred Shotgun query for the given entity.
        """
        deferred_query = self._deferred_query
        # Retrieve the deferred query filters and amend them to return results
        # linked to the given Entity.
        filters = deferred_query["filters"][:]
        link_field_name = deferred_query["link_field"]
        filters.append([link_field_name, "is", sg_entity])
        # Append extra filters, (step filtering).
        if self._extra_filter:
            filters.append(self._extra_filter)
        # Load or create a ShotgunEntityModel for the amended query. We have one
        # ShotgunEntityModel per Entity.
        name_field = get_sg_entity_name_field(deferred_query["entity_type"])
        if sg_entity["id"] not in self._deferred_models:
            # Create a new model and connect callback.
            self._deferred_models[sg_entity["id"]] = ShotgunEntityModel(
                deferred_query["entity_type"],
                filters,
                hierarchy=[name_field],
                fields=deferred_query["hierarchy"] + [name_field, link_field_name],
                parent=self,
            )
            self._deferred_models[sg_entity["id"]].data_refreshed.connect(
                lambda changed : self._on_deferred_data_refreshed(sg_entity, changed)
            )
            self._deferred_models[sg_entity["id"]].data_refresh_fail.connect(
                lambda message : self._on_deferred_data_refresh_failed(sg_entity, message)
            )
            self._deferred_models[sg_entity["id"]].async_refresh()
        else:
            self._deferred_models[sg_entity["id"]]._load_data(
                deferred_query["entity_type"],
                filters,
                hierarchy=[name_field],
                fields=deferred_query["hierarchy"] + [name_field, link_field_name],
            )
        # Immediately populate the model with the cached data (if any).
        self._on_deferred_data_refreshed(sg_entity, True, True)
        # And post a refresh in the background.
        self._deferred_models[sg_entity["id"]].async_refresh()

    def _on_deferred_data_refresh_failed(self, sg_entity, message):
        """
        Handle deferred query refresh failure for the given Entity.

        Update the dummy placeholder item, if any, with the error
        message.
        """
        parent_item = self.item_from_entity(sg_entity["type"], sg_entity["id"])
        # It is possible that the parent is gone because a refresh of the primary
        # model happened. So let's be cautious here.
        if not parent_item:
            return
        parent_uid = parent_item.data(self._SG_ITEM_UNIQUE_ID)
        refreshing_uid = self._dummy_placeholder_item_uid(parent_item)
        # Check if we have a dummy placeholder item. If so update its text with
        # an error message. The message is already logged by shotgun_model, here
        # we just don't want the user to think that the query is still going on.
        data_item = self._deferred_cache.get_entry_by_uid(refreshing_uid)
        if data_item:
            self._deferred_cache.add_item(
                parent_uid=parent_uid,
                # We need to use something which looks like a SG Entity dictionary.
                # By having a "text" key and using it for the field name, the tree
                # view will display its contents.
                sg_data={
                    "text": message,
                    "type": ""
                },
                field_name="text",
                is_leaf=True,
                uid=refreshing_uid,
            )
            item = self._get_item_by_unique_id(refreshing_uid)
            if item:
                self._update_item(item, data_item)
                item.setIcon(QtGui.QIcon())

    def _on_deferred_data_refreshed(self, sg_entity, changed, pending_refresh=False):
        """
        Called when new data is available in a deferred Shotgun model for a given
        Entity.

        :param dict sg_entity: A Shotgun Entity with at least "type" and "id" keys.
        :param bool changed: Whether or not the data in the model was changed.
        :param bool pending_refresh: Whether or not a data refresh has been posted,
                                     so refreshed data is expected later.
        """
        if not changed:
            return
        parent_item = self.item_from_entity(sg_entity["type"], sg_entity["id"])
        # It is possible that the parent is gone because a refresh of the primary
        # model happened. So let's be cautious here.
        if not parent_item:
            return
        # We use our own deferred cache to avoid conflicts with ShotgunModel so
        # we can manipulate it freely.
        parent_uid = parent_item.data(self._SG_ITEM_UNIQUE_ID)
        if self._deferred_cache.item_exists(parent_uid):
            # Grab all entries from the iterator
            existing_uids = set([x for x in self._deferred_cache.get_child_uids(parent_uid)])
        else:
            existing_uids = set()

        deferred_model = self._deferred_models[sg_entity["id"]]
        deferred_entity_type = deferred_model.get_entity_type()
        name_field = get_sg_entity_name_field(deferred_entity_type)

        # First collect all Entity items which have been fetched so far by deferred
        # queries.
        sg_deferred_entities = []
        for deferred_entity_id in deferred_model.entity_ids:
            deferred_item = deferred_model.item_from_entity(
                deferred_entity_type,
                deferred_entity_id
            )
            # In theory we should always have a matching item, but better to be
            # a bit cautious...
            if deferred_item:
                sg_entity = deferred_item.get_sg_data()
                if sg_entity:
                    sg_deferred_entities.append(sg_entity)
        # Now refresh all the deferred entity items we retrieved and keep a list of
        # the refreshed uids: new or which are still present.
        refreshed_uids = set()
        # Ideallly we would retrieve the field list from the ShotgunEntityModel
        # but this is a private member.
        deferred_query = self._deferred_query
        for sg_deferred_entity in sg_deferred_entities:
            # Update existing items or create new ones.
            uids = self._add_deferred_item_hierarchy(
                parent_item,
                deferred_query["hierarchy"],
                name_field,
                sg_deferred_entity,
            )
            refreshed_uids.update(uids)
        if not sg_deferred_entities:
            # If we don't have any Entity, add a "Retrieving XXXXXs" or
            # "No XXXXs found" child, depending on `pending_refresh` value.
            uid = self._add_dummy_placeholder_item(parent_item, pending_refresh)
            refreshed_uids.add(uid)
        # Go through the existing items and discard the ones which shouldn't be
        # there anymore.
        for uid in existing_uids:
            if uid in refreshed_uids:
                # TODO: here we could update items from the refreshed data
                continue
            data_item = self._deferred_cache.take_item(uid)
            item = self._get_item_by_unique_id(uid)
            if item:
                # The item might be already gone because one its ancestor was
                # deleted.
                self._delete_item(item)
        # Use a symmetric difference (^) to get all uids which are either in one or
        # the other set, but not in both. If we have any uid which is not in both
        # sets, then things changed.
        if existing_uids ^ refreshed_uids:
            self._post_delayed_data_refreshed()
        elif len(refreshed_uids) == 1 and self._dummy_placeholder_item_uid(parent_item) in refreshed_uids:
            # Special case if we just have the dummy placeholder: the same item
            # is kept but its value changed, e.g. "Retrieving..." to "No xx found"
            # this value is used by the file browser tab so we need to notify it
            # to update itself.
            self._post_delayed_data_refreshed()

    def _post_delayed_data_refreshed(self):
        """
        Post the emission of the `data_refreshed` signal at the end of the event
        queue.

        This method guarantees that there is only one pending signals in the queue
        at any time.
        """
        # Make sure we only trigger a refresh only once after all pending
        # deferred data has been processed by posting a single data_refreshed
        # emission in the event queue after all events which are already queued.
        if not self._pending_delayed_data_refreshed:
            # Post the signal emission at the end of the event queue.
            QtCore.QTimer.singleShot(0, self._delayed_data_refreshed_emission)
            # And keep trace an emission was posted
            self._pending_delayed_data_refreshed = True

    def _delayed_data_refreshed_emission(self):
        """
        Emit the data_refreshed signal and reset the pending emission flag.
        """
        self._pending_delayed_data_refreshed = False
        self.data_refreshed.emit(True)

    @staticmethod
    def _deferred_entity_uid(sg_entity):
        """
        Returns a unique id for the given Entity retrieved in a deferred query.
        """
        # ShotgunModel uses the entity id for leaves, we use the Entity type and
        # its id to avoid clashes in the various internal caches.
        return "%s_%d" % (sg_entity["type"], sg_entity["id"])

    def ensure_data_is_loaded(self, index=None):
        """
        Ensure all data is loaded in the model, except for deferred queries.

        .. note::
            The base class implementation is not called.

        :param index: Model index for which to recursively load data.
                      If set to None, the entire tree will be loaded.
        :type index: :class:`~PySide.QtCore.QModelIndex`
        """

        item_list = []
        if index is None:
            # Load everything
            # The top item is not a QStandardItem and we rely on
            # ShotgunStandardItem methods so grab children straightaway.
            for row_i in range(self.invisibleRootItem().rowCount()):
                item_list.append(self.invisibleRootItem().child(row_i))
        else:
            item_list = [self.itemFromIndex(index)]

        # We modify the list by adding children as we go through it, so we can't
        # use a simple iterator.
        while item_list:
            item = item_list.pop()
            if item.get_sg_data() and item.index() != index:
                # Leaves in the static SG model, we only load data for children
                # if the leaf was the actual item being selected, so files for
                # it will be collected. Otherwise we stop here to not trigger
                # all deferred queries.
                continue
            if self.canFetchMore(item.index()):
                self.fetchMore(item.index())
            for row_i in range(item.rowCount()):
                child_item = item.child(row_i)
                item_list.append(child_item)

    def hasChildren(self, index):
        """
        Return True if the item at the given index has children.

        :param index: A :class:`QtCore.QModelIndex` instance.
        :returns: A boolean, whether or not the given index has children.
        """
        # Just call base implementation if the index is not valid or if we are
        # not dealing with a leaf.
        if not index.isValid() or not self.itemFromIndex(index).get_sg_data():
            return super(ShotgunDeferredEntityModel, self).hasChildren(index)
        # We always have at least a child, which can be a valid item pulled with
        # a deferred query or a placeholder item.
        return True

    def canFetchMore(self, index):
        """
        Return True if more children can be fetched under the given index.

        :param index: A :class:`QtCore.QModelIndex` instance.
        :returns: A boolean, whether or not more children can be fetched.
        """
        # Just call base implementation if the index is not valid or if we are
        # not dealing with a leaf.
        if not index.isValid() or not self.itemFromIndex(index).get_sg_data():
            return super(ShotgunDeferredEntityModel, self).canFetchMore(index)

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
        if not index.isValid():
            # Let the base implementation deal with invalid items
            return super(ShotgunDeferredEntityModel, self).fetchMore(index)
        item = self.itemFromIndex(index)
        # Set the flag to prevent subsequent attempts to fetch more
        item.setData(True, self._SG_ITEM_FETCHED_MORE)
        sg_data = item.get_sg_data()
        if not sg_data:
            # If not dealing with a leaf, let the base implementation deal with
            # the index.
            return super(ShotgunDeferredEntityModel, self).fetchMore(index)
        self._run_deferred_query_for_entity(sg_data)

    def item_from_entity(self, entity_type, entity_id):
        """
        Retrieve the item representing the given entity in the model.

        Leaves are only considered if the given Entity type matches the Entity
        type this model represents. Otherwise, the full model hierarchy is traversed
        to retrieve the given Entity.

        All entities which have been already fetched with direct or deferred queries
        are considered. However, no additional deferred queries is run to fetch
        more data from Shotgun.

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
        if entity_type == self.get_entity_type() or self._deferred_query["entity_type"] != entity_type:
            return super(ShotgunDeferredEntityModel, self).item_from_entity(
                entity_type, entity_id
            )
        return self._get_item_by_unique_id(
            self._deferred_entity_uid({ "type": entity_type, "id" : entity_id})
        )

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
                # We never fetch more data for leaves in the primary model
                # otherwise this trigger deferred queries.
                if not item.get_sg_data() and self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                value = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
                if value == field_value:
                    parent = item
                    break
        return parent

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
