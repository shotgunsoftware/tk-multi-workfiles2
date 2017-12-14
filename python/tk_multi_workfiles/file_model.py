# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import weakref

import sgtk
from sgtk.platform.qt import QtGui, QtCore

from .file_finder import AsyncFileFinder
from .user_cache import g_user_cache
from .file_search_cache import FileSearchCache

shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")
ShotgunDataRetriever = shotgun_data.ShotgunDataRetriever


class FileModel(QtGui.QStandardItemModel):
    """
    The FileModel maintains a model of all files (work files and publishes) found for a matrix of
    entities and users.  Details of each 'version' of a file are contained in a FileItem instance
    and presented as a single model item.

    File items are grouped into groups that represent both the entity and the user that the files
    were found for (the WorkArea).

    Additional items are added to a group to represent additional hierarchy in the model.
    """

    class SearchDetails(object):
        """
        Representation of details needed to search for a set of files.  A single instance
        of this class represents a single entity to be grouped in the model
        """

        def __init__(self, name=None):
            """
            :param name:    The string name to be used for the search.  This is used when constructing
                            the group name in the model.
            """
            self.name = name
            self.entity = None
            self.child_entities = []
            self.is_leaf = False # TODO: this does not seem to be used anywhere?

        def __repr__(self):
            """
            :returns:    The string representation of these details
            """
            return ("%s\n"
                    " - Entity: %s\n"
                    " - Is leaf: %s\n%s"
                    % (self.name, self.entity, self.is_leaf, self.child_entities))

    # enumeration of node types in model:
    (FILE_NODE_TYPE, GROUP_NODE_TYPE, FOLDER_NODE_TYPE) = range(3)

    # enumeration of search status:
    (SEARCHING, SEARCH_COMPLETED, SEARCH_FAILED) = range(3)

    # additional data roles defined for the model:
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    NODE_TYPE_ROLE = _BASE_ROLE     + 1     # type of node in model (e.g. FILE_NODE_TYPE)
    FILE_ITEM_ROLE = _BASE_ROLE     + 2     # FileItem data
    WORK_AREA_ROLE = _BASE_ROLE     + 3     # WorkArea data
    SEARCH_STATUS_ROLE = _BASE_ROLE + 4     # search status data
    SEARCH_MSG_ROLE = _BASE_ROLE    + 5     # search message data

    class _BaseModelItem(QtGui.QStandardItem):
        """
        Base model item for storage of the file data in the model.
        """

        def __init__(self, typ, text=None):
            """
            :param typ:     The type of item this represents (see enumeration of node types above)
            :param text:    String used for the label/display role for this item
            """
            QtGui.QStandardItem.__init__(self, text or "")
            self._type = typ

        def data(self, role):
            """
            Return the data from the item for the specified role.

            :param role:    The role to return data for.
            :returns:       Data for the specified role
            """
            if role == FileModel.NODE_TYPE_ROLE:
                return self._type
            else:
                # just return the default implementation:
                return QtGui.QStandardItem.data(self, role)

        def setData(self, value, role):
            """
            Set the data on the item for the specified role

            :param value:   The value to set the data with
            :param role:    The role to set the data for
            """
            if role == FileModel.NODE_TYPE_ROLE:
                # do nothing as the data can't be set:
                pass
            else:
                # call the base implementation:
                QtGui.QStandardItem.setData(self, value, role)

    class _FileModelItem(_BaseModelItem):
        """
        Model item that represents a single FileItem in the model
        """

        def __init__(self, file_item, work_area):
            """
            :param file_item:    The FileItem instance this model item represents
            :param work_area:    The WorkArea this file item belongs to
            """
            FileModel._BaseModelItem.__init__(self, typ=FileModel.FILE_NODE_TYPE)
            self._file_item = file_item
            self._work_area = work_area

        @property
        def file_item(self):
            """
            :returns:    The file item this model item represents
            """
            return self._file_item

        @property
        def work_area(self):
            """
            :returns:    The work area the file belongs to
            """
            return self._work_area

        def data(self, role):
            """
            Return the data from the item for the specified role.

            :param role:    The role to return data for.
            :returns:       Data for the specified role
            """
            if role == QtCore.Qt.DisplayRole:
                return "%s, v%0d" % (self._file_item.name, self._file_item.version)
            elif role == FileModel.FILE_ITEM_ROLE:
                return self._file_item
            elif role == FileModel.WORK_AREA_ROLE:
                return self._work_area
            else:
                # just return the default implementation:
                return FileModel._BaseModelItem.data(self, role)

        def setData(self, value, role):
            """
            Set the data on the item for the specified role

            :param value:   The value to set the data with
            :param role:    The role to set the data for
            """
            if role == QtCore.Qt.DisplayRole:
                # do nothing as it can't be set!
                pass
            elif role == FileModel.FILE_ITEM_ROLE:
                self._file_item = value
                self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                self._work_area = value
                self.emitDataChanged()
            else:
                # call the base implementation:
                FileModel._BaseModelItem.setData(self, value, role)

    class _FolderModelItem(_BaseModelItem):
        """
        Model item that represents a folder in the model.  These are used when a group has entity
        children that need to be represented in the model.
        """

        def __init__(self, name, entity):
            """
            :param name:    The name to use for the model item display role
            :param entity:  A Shotgun entity dictionary for the entity that this folder item represents
            """
            FileModel._BaseModelItem.__init__(self, typ=FileModel.FOLDER_NODE_TYPE, text=name)
            self._entity = entity

        @property
        def entity(self):
            """
            :returns:   An entity dictionary representing the entity represented by this item
            """
            return self._entity

    class _GroupModelItem(_BaseModelItem):
        """
        Model item that represents a group in the model.  A group is a per-user, per-entity item that contains
        the files found for the group as well as any additional child entities.
        """

        def __init__(self, name, key, work_area=None):
            """
            :param name:        The name to use for the model items display role
            :param key:         A unique key representing this group
            :param work_area:   A WorkArea instance that this group represents
            """
            FileModel._BaseModelItem.__init__(self, typ=FileModel.GROUP_NODE_TYPE, text=name)

            self._search_status = FileModel.SEARCH_COMPLETED
            self._search_msg = ""
            self._key = key
            self._work_area = work_area

        @property
        def key(self):
            """
            :returns:   The unique key for this group
            """
            return self._key

        # @property
        def _get_work_area(self):
            """
            :returns:   The WorkArea instance associated with this item
            """
            return self._work_area

        # @work_area.setter
        def _set_work_area(self, work_area):
            """
            Set the work area associated with this item

            :param work_area:   The WorkArea to associate with this item
            """
            self._work_area = work_area
            self.emitDataChanged()

        work_area = property(_get_work_area, _set_work_area)

        def set_search_status(self, status, msg=None):
            """
            Set the search status for this item and emit a dataChanged signal to indicate it's changed.

            :param status:  The search status (see the search status enumeration above) to update this item with
            :param msg:     The status message if any to update this item with
            """
            self._search_status = status
            self._search_msg = msg
            self.emitDataChanged()

        def data(self, role):
            """
            Return the data from the item for the specified role.

            :param role:    The role to return data for.
            :returns:       Data for the specified role
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                return self._search_status
            elif role == FileModel.SEARCH_MSG_ROLE:
                return self._search_msg
            elif role == FileModel.WORK_AREA_ROLE:
                return self._work_area
            else:
                # just return the default implementation:
                return FileModel._BaseModelItem.data(self, role)

        def setData(self, value, role):
            """
            Set the data on the item for the specified role

            :param value:   The value to set the data with
            :param role:    The role to set the data for
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                self._search_status = value
                self.emitDataChanged()
            elif role == FileModel.SEARCH_MSG_ROLE:
                self._search_msg = value
                self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                self._work_area = value
                self.emitDataChanged()
            else:
                # call the base implementation:
                FileModel._BaseModelItem.setData(self, value, role)

    # Signal emitted when sandboxes are used, but before we know which ones
    uses_user_sandboxes = QtCore.Signal(object) # Work area that uses sandboxes.
    # Signal emitted when the sandbox_users_found when users were found in the sandbox.
    sandbox_users_found = QtCore.Signal(list)# list of users

    def __init__(self, bg_task_manager, parent):
        """
        :param bg_task_manager: A BackgroundTaskManager instance that will be used for all background/threaded
                                work that needs undertaking
        :param parent:          The parent QObject for this instance
        """
        QtGui.QStandardItemModel.__init__(self, parent)

        self._app = sgtk.platform.current_bundle()
        self._published_file_type = sgtk.util.get_published_file_entity_type(self._app.sgtk)

        # sg data retriever is used to download thumbnails in the background
        self._sg_data_retriever = ShotgunDataRetriever(bg_task_manager=bg_task_manager)
        self._sg_data_retriever.work_completed.connect(self._on_data_retriever_work_completed)
        self._sg_data_retriever.work_failure.connect(self._on_data_retriever_work_failed)

        # details about the current entities and users that are represented
        # in this model.
        self._current_searches = []
        self._current_users = [g_user_cache.current_user]

        self._in_progress_searches = {}
        self._search_cache = FileSearchCache()

        # self._current_item_map[search_id][file.key][file.version] = model._FileModelItem
        self._current_item_map = {}
        # self._pending_thumbnail_requests[request_id] = (group_key, file_key, file_version)
        self._pending_thumbnail_requests = {}

        # we'll need a file finder to be able to find files:
        self._finder = AsyncFileFinder(bg_task_manager, self)
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.publishes_found.connect(self._on_finder_publishes_found)
        self._finder.search_completed.connect(self._on_finder_search_completed)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        self._finder.work_area_resolved.connect(self._on_finder_work_area_resolved)
        self._finder.work_area_found.connect(self._on_finder_work_area_found)

    def destroy(self):
        """
        Called to clean-up and shutdown any internal objects when the model has been finished
        with.  Failure to call this may result in instability or unexpected behaviour!
        """
        # clear the model:
        self.clear()

        # stop the data retriever:
        if self._sg_data_retriever:
            self._sg_data_retriever.stop()
            self._sg_data_retriever.deleteLater()
            self._sg_data_retriever = None

        # clean up the cache:
        if self._search_cache:
            self._search_cache.clear()
            self._search_cache = None

        # disconnect and clean up the file finder:
        if self._finder:
            self._finder.files_found.disconnect(self._on_finder_files_found)
            self._finder.publishes_found.disconnect(self._on_finder_publishes_found)
            self._finder.search_completed.disconnect(self._on_finder_search_completed)
            self._finder.search_failed.disconnect(self._on_finder_search_failed)
            self._finder.work_area_resolved.disconnect(self._on_finder_work_area_resolved)
            self._finder.shut_down()
            self._finder = None

    def get_cached_file_versions(self, key, work_area, clean_only=False):
        """
        Return the cached file versions for the specified file key and work area.  Note that this isn't
        garunteed to find all versions of a file that exist if the cache hasn't been populated yet/is dirty
        if clean_only is False.

        :param key:         The unique file key to find file versions for
        :param work_area:   A WorkArea instance to find file versions for
        :param clean_only:  If true then the cached file versions will only be returned if the cache is
                            up-to-date.  If false then file versions will be returned even if the model is still
                            searching for files.
        :returns:           A dictionary {version:FileItem} of all file versions found.
        """
        return self._search_cache.find_file_versions(work_area, key, clean_only)

    def items_from_file(self, file_item, ignore_version=False):
        """
        Find the model item(s) for the specified file item.

        :param file_item:       The FileItem instance to find the model item(s) for
        :param ignore_version:  If True then all versions that match the FileItem key will be returned.  If False
                                then only items that match the exact version of the FileItem will be returned.
        :returns:               A list of any found model items representing the specified FileItem
        """
        if not file_item:
            return []
        return self._find_current_items(None, file_item.key, file_item.version if not ignore_version else None)

    # Interface for modifying the entities in the model:
    def set_entity_searches(self, searches):
        """
        Set the entity searches that the model should populate itself with.  The model will
        be updated to contain a group item for each search+user combination and will initiate a
        search for all files (work files and publishes) in this group.

        :param searches:    A list of SearchDetails instances containing information about the entities
                            to search for
        """
        self._app.log_debug("File Model: Setting entity searches on model to: %s" % [s.name for s in searches if s])
        # stop any in-progress searches:
        self._stop_in_progress_searches()
        self._current_searches = searches or []

        # update groups:
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    # Interface for modifying the users in the model:
    def set_users(self, users):
        """
        Set the users the model should populate itself with.  The model will be updated to contain a group
        item for each search+user combination and will initiate a search for all files (work files and
        publishes) in this group.

        :param users:    A list of Shotgun user dictionaries that should be represented in the model
        """
        # stop any in-progress searches:
        self._stop_in_progress_searches()

        self._current_users = list(users or [])
        if g_user_cache.current_user:
            # we _always_ search for the current user:
            user_ids = [user["id"] for user in self._current_users]
            if g_user_cache.current_user["id"] not in user_ids:
                self._current_users.insert(0, g_user_cache.current_user)
        elif not self._current_users:
            # no users so use 'None' instead which will effectively search for the
            # current user but handles the legacy case where the current user doesn't
            # match the log-in!
            self._current_users = [None]

        # update groups:
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    def async_refresh(self):
        """
        Asynchronously refresh the model by stopping all in-progress searches and starting
        all searches from scratch
        """
        # stop any current searches:
        self._stop_in_progress_searches()
        # and restart all searches:
        self._start_searches()

    def clear(self):
        """
        Overriden from base class.  Clear the model in a safe way.
        """
        # stop all current searches:
        self._stop_in_progress_searches()

        # clear all items in a bottom-up fashion:
        # note that we don't call QStandardItemModel.clear due to a bug
        # in pre-1.1.2 PySide that can result in crashes!
        self._clear_children_r(self.invisibleRootItem())

        # clean up the current-item map
        self._current_item_map = {}

    # ------------------------------------------------------------------------------------------
    # protected methods

    def _safe_remove_row(self, row, parent_item=None):
        """
        Remove the specified row from the parent item in a PySide/Shoboken friendly way by removing
        all its children first in a bottom-up fashion.

        :param row:         The row to remove
        :param parent_item: The parent QStandardItem of the item to remove.  If None then the row
                            is removed from the root item.
        """
        parent_item = parent_item or self.invisibleRootItem()

        # get the item and safey remove all children of the item:
        item = parent_item.child(row)
        if not item:
            return
        self._clear_children_r(item)

        # and remove the row:
        parent_item.removeRow(row)

    def _clear_children_r(self, parent_item):
        """
        Recursively clear the children from the specified parent item in a bottom-up fashion

        :param parent_item: The parent QStandardItem to remove all children for
        """
        num_rows = parent_item.rowCount()
        if num_rows == 0:
            return

        # remove all grandchildren:
        for row in range(num_rows):
            child_item = parent_item.child(row)
            if child_item:
                self._clear_children_r(child_item)

        # remove all children:
        parent_item.removeRows(0, num_rows)

    def _item_generator(self, parent_item, item_type=QtGui.QStandardItem):
        """
        Item generator that yields all items under the specified parent that are of
        the specified type.

        :param parent_item: The parent QStandardItem to search under
        :param item_type:   The class type of the model items to generate
        :returns:           A generator that yields all child items of the parent that
                            are of the specified type
        """
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, item_type):
                yield child_item

    def _group_items(self):
        """
        Iterate over all root items in the model and yield all _GroupModelItems that are found

        :returns:   A generator that yields all _GroupModelItems in the model
        """
        return self._item_generator(self.invisibleRootItem(), FileModel._GroupModelItem)

    def _file_items(self, parent_item):
        """
        Iterate over all child items for the specified parent and yield all _FileModelItems that
        are found

        :param parent_item: The parent item to yield _FileModelItems for
        :returns:           A generator that yields all _FileModelItems under the specified parent
        """
        return self._item_generator(parent_item, FileModel._FileModelItem)

    def _gen_entity_key(self, entity_dict):
        """
        Generate a unique key for the specified Shotgun entity dictionary.

        :param entity_dict: A Shotgun entity dictionary containing at least id and type.  Can be None.
        :returns:           A tuple containing (type, id) of the entity that can be used as a unique key to
                            identify the entity.
        """
        if not entity_dict:
            return (None, None)
        else:
            return (entity_dict.get("type"), entity_dict.get("id"))

    def _start_searches(self):
        """
        Start all searches for all users that should be presented in the model.
        """
        if not self._current_searches:
            # nothing to do!
            return

        # get existing groups:
        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        for search in self._current_searches:
            if not search.entity:
                continue

            # update all existing group items for this entity and all users to indicate
            # that we are searching for files
            entity_key = self._gen_entity_key(search.entity)
            for user in self._current_users:
                user_key = self._gen_entity_key(user)
                group_key = (entity_key, user_key)
                group_item = group_map.get(group_key)
                if group_item:
                    group_item.set_search_status(FileModel.SEARCHING)

                # and dirty the search cache:
                self._search_cache.set_dirty(search.entity, user)

            # actually start the search:
            search_id = self._finder.begin_search(search.entity, self._current_users)
            self._in_progress_searches[search_id] = search
            self._app.log_debug("File Model: Started search %d..." % search_id)

    def _stop_in_progress_searches(self):
        """
        Stop all in-progress searches
        """
        search_ids = self._in_progress_searches.keys()
        self._in_progress_searches = {}
        for search_id in search_ids:
            self._finder.stop_search(search_id)

        # any pending thumbnail requests can also be stopped:
        for request_id in self._pending_thumbnail_requests:
            self._sg_data_retriever.stop_work(request_id)
        self._pending_thumbnail_requests = {}

    def _update_groups(self):
        """
        Update groups in the model.  Remove any that are no longer needed and insert any that are
        needed but are missing.

        This will ensure that _all_ groups are added for the current user but groups for other users
        are only added if/when files are found unless they already exist in which case they are left
        in the model.  This provides the most consistent experience for any views hooked up to the
        model.
        """
        # get existing groups:
        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        valid_group_keys = set()
        if self._current_searches and self._current_users:

            # get details about the users to run searches for:
            current_user_key = self._gen_entity_key(g_user_cache.current_user)
            have_current_user = False
            for user in self._current_users:
                if self._gen_entity_key(user) == current_user_key:
                    have_current_user = True
                    break
            primary_user_key = current_user_key if have_current_user else self._gen_entity_key(self._current_users[0])

            # iterate over the searches, making sure that group nodes exist as needed
            previous_valid_row = -1
            for search in self._current_searches:
                if not search.entity:
                    # this search doesn't represent an entity so we won't need to search
                    # for files.  In which case we can just add a group item with the
                    # correct name and be done with it!  We also only need one of these
                    # rather than (potentially) one per user!
                    continue

                entity_key = self._gen_entity_key(search.entity)

                # iterate over each user for this group:
                for user in self._current_users:
                    user_key = self._gen_entity_key(user)
                    group_key = (entity_key, user_key)

                    # see if we already have an item for this group:
                    group_item = group_map.get(group_key)

                    if not group_item:
                        # we don't have a group node for this entity/user combination:
                        cached_result = self._search_cache.find(search.entity, user)
                        if (user_key == primary_user_key or cached_result):
                            # always add a group for the primary user or if we already have a cached result:
                            group_item = FileModel._GroupModelItem(search.name, group_key)
                            self.insertRow(previous_valid_row + 1, group_item)

                            if cached_result:
                                # we have a cached result so populate the group:
                                files, work_area = cached_result
                                self._process_files(files, work_area, group_item)
                                group_item.work_area = work_area

                    if group_item:
                        # make sure the name and entity children are up-to-date:
                        self._update_group_child_entity_items(group_item, search.child_entities or [])

                        # keep track of the last valid group row:
                        previous_valid_row = group_item.row()

                        # and keep track of this group item:
                        valid_group_keys.add(group_key)

        # remove any groups that are no longer needed:
        for group_key, group_item in group_map.iteritems():
            if group_key not in valid_group_keys:
                self._safe_remove_row(group_item.row())

        # and clean up the file-to-item map:
        self._cleanup_current_item_map()

    def _update_group_child_entity_items(self, parent_item, child_details):
        """
        Update the non-file child entity items for a group item.  This adds/removes rows accordingly
        to ensure the children match the entity details.

        :param parent_item:     The parent _GroupModelItem to update the entity children under
        :param child_details:   A list of dictionaries containing the details of any child entities that
                                should be represented in this group.  Each dictionary should contain
                                {name, entity} where name is a string used for the name of the model item and
                                entity is a Shotgun entity dictionary representing the entity itself.
        """
        # build a map from the entity key to row for all folder items:
        current_entity_row_map = {}
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, FileModel._FolderModelItem):
                child_name = child_item.text()
                child_entity = child_item.entity
                child_key = (child_name, self._gen_entity_key(child_entity))
                current_entity_row_map[child_key] = ri

        # figure out which entities we need to add:
        valid_gen_entity_keys = set()
        entities_to_add = []
        for details in child_details:
            child_name = details.get("name", "Entity")
            child_entity = details.get("entity")
            child_key = (child_name, self._gen_entity_key(child_entity))
            if child_key in valid_gen_entity_keys:
                # don't add the same entity twice!
                continue
            valid_gen_entity_keys.add(child_key)
            if child_key not in current_entity_row_map:
                entities_to_add.append((child_name, child_entity))

        # figure out which rows to remove...
        rows_to_remove = set([row for key, row in current_entity_row_map.iteritems()
                              if key not in valid_gen_entity_keys])
        # and remove them:
        for row in sorted(rows_to_remove, reverse=True):
            self._safe_remove_row(row, parent_item)

        # finally, add in new rows:
        if entities_to_add:
            new_rows = []
            for name, entity in entities_to_add:
                folder_item = FileModel._FolderModelItem(name, entity)
                new_rows.append(folder_item)
            parent_item.appendRows(new_rows)

    def _process_files(self, files, work_area, group_item, have_local=True, have_publishes=True):
        """
        Update the file items under the specified parent.  This adds/removes/updates file model items
        as needed effectively performing an in-place refresh.  This avoids having to do a complete
        clear/rebuild which would be a much more intrusive user experience.

        This method is typically called when the finder returns some results and will be called multiple
        times within the scope of a single search.  It may be called with local work files, publishes or
        both but only ever updates the corresponding file items.  This means it will only remove model
        items if it is certain that the file/publish no longer exists/should be represented in the model.

        e.g. if updating publishes only, it will never remove file items that only represent work files.

        :param files:           A list of FileItem instances representing the files to process
        :param work_area:       A WorkArea instance representing the work area the files were found in
        :param group_item:      The _GroupModelItem the files should be updated for
        :param have_local:      True if the files list contains details about work files, false otherwise
        :param have_publishes:  True if the files list contains details about publishes, false otherwise
        """
        if not have_local and not have_publishes:
            # nothing to do then!
            return

        # get details about existing items:
        existing_file_item_map = {}
        prev_local_file_versions = set()
        prev_publish_file_versions = set()

        for model_item in self._file_items(group_item):
            file_item = model_item.file_item
            file_version_key = (file_item.key, file_item.version)
            existing_file_item_map[file_version_key] = (file_item, model_item)
            if file_item.is_local:
                prev_local_file_versions.add(file_version_key)
            if file_item.is_published:
                prev_publish_file_versions.add(file_version_key)

        # build a list of existing files that we should keep in the model:
        file_versions_to_keep = set()
        if have_local and not have_publishes:
            # keep all publishes that aren't local
            file_versions_to_keep = prev_publish_file_versions
        elif not have_local and have_publishes:
            # keep all local that aren't publishes
            file_versions_to_keep = prev_local_file_versions
        valid_files = dict([(k, v[0]) for k, v in existing_file_item_map.iteritems() if k in file_versions_to_keep])

        # match files against existing items:
        files_to_add = []
        for file_item in files:
            file_version_key = (file_item.key, file_item.version)
            current_file, model_item = existing_file_item_map.get(file_version_key, (None, None))
            if current_file and model_item:
                # update the existing file:
                if file_item.is_published:
                    current_file.update_from_publish(file_item)
                if file_item.is_local:
                    current_file.update_from_work_file(file_item)
                file_item = current_file
            else:
                # file not in model yet so we'll need to add it:
                files_to_add.append(file_item)

            # add to the list of valid files:
            valid_files[file_version_key] = file_item

            # if this is from a published file then we want to retrieve the thumbnail
            # if one is available:
            if file_item.is_published and file_item.thumbnail_path and not file_item.thumbnail:
                # request the thumbnail using the data retriever:
                request_id = self._sg_data_retriever.request_thumbnail(file_item.thumbnail_path,
                                                                       self._published_file_type,
                                                                       file_item.published_file_id,
                                                                       "image",
                                                                       load_image=True)
                self._pending_thumbnail_requests[request_id] = (group_item.key, file_item.key, file_item.version)

        # figure out if any existing items are no longer needed:
        valid_file_versions = set(valid_files.keys())
        file_versions_to_remove = set(existing_file_item_map.keys()) - valid_file_versions
        rows_to_remove = set(
            [v[1].row() for k, v in existing_file_item_map.iteritems() if k in file_versions_to_remove]
        )

        # update any files that are no longer in the corresponding set but which aren't going to be removed:
        if have_local:
            for file_version_key in (prev_local_file_versions - valid_file_versions) - file_versions_to_remove:
                file_item, model_item = existing_file_item_map[file_version_key]
                file_item.set_not_work_file()
        if have_publishes:
            for file_version_key in (prev_publish_file_versions - valid_file_versions) - file_versions_to_remove:
                file_item, model_item = existing_file_item_map[file_version_key]
                file_item.set_not_published()

        # update the cache - it's important this is done _before_ adding/updating the model items:
        self._search_cache.add(work_area, valid_files.values())

        # now lets remove, add and update items as needed:
        # 1. Remove items that are no longer needed:
        if rows_to_remove:
            for row in sorted(rows_to_remove, reverse=True):
                self._safe_remove_row(row, group_item)

        # 2. Add new items:
        if files_to_add:
            new_items = []
            for file_item in files_to_add:
                model_item = FileModel._FileModelItem(file_item, work_area)
                new_items.append(model_item)
                # and track this item:
                self._track_current_file_item(model_item, group_item)
            if new_items:
                group_item.appendRows(new_items)

        # 3. Update all items in this group:
        self._update_group_file_items(group_item)

        # and clean up the file-to-item map:
        self._cleanup_current_item_map()

    def _track_current_file_item(self, file_model_item, group_model_item):
        """
        Track a current _FileModelItem so that it can be found easily later

        :param file_model_item:     The _FileModelItem to keep track of
        :param group_model_item:    The parent _GroupModelItem for the file model item (note that it may not have
                                    been parented yet!)
        """
        file_item = file_model_item.file_item

        # self._current_item_map[group_key][file_key][file_version] = weakref.ref(_FileModelItem)
        file_map = self._current_item_map.setdefault(group_model_item.key, {})
        version_map = file_map.setdefault(file_item.key, {})
        version_map[file_item.version] = weakref.ref(file_model_item)

    def _find_version_items(self, version_map, file_version):
        """
        Find current model items for the specified file version in the specified map.  If file_version is
        None then all valid model items in the map are returned.

        :param version_map:     A dictionary mapping file version to weakrefs of _FileModelItems
        :param file_version:    The file version to find all matching items for
        :returns:               A list of _FileModelItems that were found that match the specified file version
        """
        found_items = []
        if file_version is not None:
            # see if we have an item for the specific version and add it
            item_ref = version_map.get(file_version)
            item = item_ref() if item_ref else None
            if item:
                found_items.append(item)
        else:
            # add items for all versions to the list:
            for item in [ref() for ref in version_map.values()]:
                if item:
                    found_items.append(item)
        return found_items

    def _find_file_items(self, file_map, file_key, file_version):
        """
        Find current model items for the specified file key and version in the specified map.  If file key
        is None then all items that match the version are returned.

        :param file_map:        A dictionary mapping file key to a dictionary of {file version:_FileModelItem}s
        :param file_key:        The file key to find all matching items for
        :param file_version:    The file version to find all matching items for
        :returns:               A list of _FileModelItems that were found that match the specified file key and
                                version
        """
        found_items = []
        if file_key is not None:
            version_map = file_map.get(file_key)
            if version_map:
                found_items.extend(self._find_version_items(version_map, file_version))
        else:
            for version_map in file_map.values():
                found_items.extend(self._find_version_items(version_map, file_version))
        return found_items

    def _find_current_items(self, group_key, file_key, file_version):
        """
        Find current model items for the specified group key, file key and file version.  If group key
        is None then all items that match the file key and version are returned.

        :param group_key:       The group key to find all matching items for
        :param file_key:        The file key to find all matching items for
        :param file_version:    The file version to find all matching items for
        :returns:               A list of _FileModelItems that were found that match the specified group key,
                                file key and file version
        """
        found_items = []
        if group_key is not None:
            file_map = self._current_item_map.get(group_key)
            if file_map:
                found_items.extend(self._find_file_items(file_map, file_key, file_version))
        else:
            for file_map in self._current_item_map.values():
                found_items.extend(self._find_file_items(file_map, file_key, file_version))
        return found_items

    def _cleanup_current_item_map(self):
        """
        Cleanup the current item map by removing any entries that are no longer valid, e.g. the weakref
        to the _FileModelItem is None.
        """
        new_item_map = {}
        for group_key, file_map in self._current_item_map.iteritems():
            new_file_map = {}
            for file_key, version_map in file_map.iteritems():
                new_version_map = {}
                for version, item_ref in version_map.iteritems():
                    if item_ref and item_ref():
                        new_version_map[version] = item_ref
                if new_version_map:
                    new_file_map[file_key] = new_version_map
            if new_file_map:
                new_item_map[group_key] = new_file_map
        self._current_item_map = new_item_map

    def _on_finder_work_area_found(self, search_id, work_area):
        """
        Slot triggered when the finder finds a work area. This will
        emit the work_area_found signal if the work area uses sandboxing
        in any shape or form. Note that at that point the available
        sandboxes haven't been resolved yet, only that they may exist.

        :param search_id:    The id of the search that the work area was found for
        :param work_area:    The WorkArea instance that was found
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        if work_area.contains_user_sandboxes:
            self.uses_user_sandboxes.emit(work_area)

    def _on_finder_work_area_resolved(self, search_id, work_area):
        """
        Slot triggered when the finder resolved users from a work area during the search.  If the work area
        contains user sandboxes this will emit the sandbox_users_found signal with the list of users.

        :param search_id:    The id of the search that the work area was resolved for
        :param work_area:    The WorkArea instance that was resolved
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        users = list(work_area.sandbox_users)

        # If users were found.
        if users:
            self.sandbox_users_found.emit(users)

    def _on_finder_files_found(self, search_id, file_list, work_area):
        """
        Slot triggered when the finder has found some work files for a search.

        :param search_id:    The id of the search that the work files were found for
        :param file_list:    The list of FileItems that were found
        :param work_area:    The work area that the files were found in
        """
        self._app.log_debug("File Model: Found %d files for search %s, user '%s'"
                            % (len(file_list), search_id,
                               work_area.context.user["name"] if work_area.context.user else "Unknown"))
        self._process_found_files(search_id, file_list, work_area, have_local=True, have_publishes=False)

    def _on_finder_publishes_found(self, search_id, file_list, work_area):
        """
        Slot triggered when the finder has found some publishes for a search

        :param search_id:    The id of the search that the publishes were found for
        :param file_list:    The list of FileItems that were found
        :param work_area:    The work area that the publishes were found in
        """
        self._app.log_debug("File Model: Found %d publishes for search %s, user '%s'"
                            % (len(file_list), search_id,
                               work_area.context.user["name"] if work_area.context.user else "Unknown"))
        self._process_found_files(search_id, file_list, work_area, have_local=False, have_publishes=True)

    def _process_found_files(self, search_id, file_list, work_area, have_local, have_publishes):
        """
        Process files/publishes found by the finder.  This ensures that the parent _GroupModelItem for the
        search entity+user exists and then updates the group with files that were found.

        :param search_id:       The id of the search that the files were found for
        :param file_list:       The list of FileItems that were found
        :param work_area:       The work area that the files were found in
        :param have_local:      True if work files were found, otherwise false
        :param have_publishes:  True if publishes were found, otherwise false
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        search = self._in_progress_searches[search_id]
        search_user = work_area.context.user

        # find the group item for this search:
        group_key = (self._gen_entity_key(search.entity), self._gen_entity_key(search_user))
        found_group = False
        for group_item in self._group_items():
            if group_item.key == group_key:
                found_group = True
                break

        if found_group:
            # and make sure the work area is up-to-date:
            group_item.work_area = work_area
        else:
            if not file_list:
                # no files so don't bother creating a group!
                return

            # we don't have a group item for this search so lets add one now:
            group_item = FileModel._GroupModelItem(search.name, group_key, work_area)
            # (TODO) need to insert it into the right place in the list!
            self.appendRow(group_item)

            # add children
            self._update_group_child_entity_items(group_item, search.child_entities or [])

        # process files:
        self._process_files(file_list, work_area, group_item, have_local, have_publishes)

    def _on_finder_search_completed(self, search_id):
        """
        Slot triggered when a finder search has completed.  This gets called once all search
        tasks have been completed successfully.

        :param search_id:   The id of the search that has completed
        """
        self._app.log_debug("File Model: Search %s completed" % search_id)
        self._process_search_completion(search_id, FileModel.SEARCH_COMPLETED)

    def _on_finder_search_failed(self, search_id, error_msg):
        """
        Slot triggered when a finder search fails for some reason!

        :param search_id:   The id of the search that has failed
        :param error_msg:   The error message reported by the search
        """
        self._app.log_debug("File Model: Search %d failed - %s" % (search_id, error_msg))
        self._process_search_completion(search_id, FileModel.SEARCH_FAILED, error_msg)

    def _process_search_completion(self, search_id, status, error_msg=None):
        """
        Slot triggered when the a search has completely completed.  This is used
        to update the status of the group item and give feedback to the user.

        :param search_id:   The id of the search that has failed
        :param status:      The status of the completed search - see the search status enumeration
                            above
        :param error_msg:   The error message reported by the search
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        search = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])

        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        entity_key = self._gen_entity_key(search.entity)
        for user in self._current_users:
            group_key = (entity_key, self._gen_entity_key(user))
            group_item = group_map.get(group_key)
            if not group_item:
                continue
            group_item.set_search_status(status, error_msg)

            # clean the search cache entry for this item assuming the search completed successfully!
            if status == FileModel.SEARCH_COMPLETED:
                self._search_cache.set_dirty(search.entity, user, is_dirty=False)

    def _on_data_retriever_work_completed(self, uid, request_type, data):
        """
        Slot triggered when the data-retriever has finished doing some work.  The data retriever is currently
        just used to download thumbnails for published files so this will be triggered when a new thumbnail
        has been downloaded and loaded from disk.

        :param uid:             The unique id representing a task being executed by the data retriever
        :param request_type:    A string representing the type of request that has been completed
        :param data:            The result from completing the work
        """
        if uid not in self._pending_thumbnail_requests:
            # the completed work is of no interest to us!
            return
        (group_key, file_key, file_version) = self._pending_thumbnail_requests[uid]
        del(self._pending_thumbnail_requests[uid])

        # extract the thumbnail path and QImage from the data/result
        thumb_path = data.get("thumb_path")
        thumb_image = data.get("image")
        if not thumb_path or not thumb_image:
            return

        # find all file items for this file:
        model_items = self._find_current_items(group_key, file_key, file_version)
        if not model_items:
            return

        # find the work area associated with the group:
        work_area = None
        for group_item in self._group_items():
            if group_item.key == group_key:
                work_area = group_item.work_area
                break

        # prepare a pixmap from the thumbnail image:
        thumb = self._build_thumbnail(thumb_image)
        if not thumb:
            return

        # update all files and items with this thumbnail:
        for model_item in model_items:
            file_item = model_item.file_item
            file_item.thumbnail = thumb
            model_item.emitDataChanged()

            if work_area:
                # update thumbnails on all file versions:
                self._update_version_thumbnails(file_item.key, group_key, work_area)

    def _on_data_retriever_work_failed(self, uid, error_msg):
        """
        Slot triggered when the data retriever fails to do some work!

        :param uid:         The unique id representing the task that the data retriever failed on
        :param error_msg:   The error message for the failed task
        """
        if uid in self._pending_thumbnail_requests:
            del(self._pending_thumbnail_requests[uid])
        self._app.log_debug("File Model: Failed to find thumbnail for id %s: %s" % (uid, error_msg))

    def _update_group_file_items(self, group_item):
        """
        Update all file model items within the specified group model item.  This updates each file's
        tooltip, associated versions and thumbnail and ensures that the correct dataChanged signal is
        emitted for them.

        :param group_item:  The _GroupModelItem representing the group in the model
        """
        work_area = group_item.work_area
        if not work_area:
            return

        # get a unique list of all file keys under the group:
        unique_file_keys = set()
        for item in self._file_items(group_item):
            file_item = item.file_item
            unique_file_keys.add(file_item.key)

        if not unique_file_keys:
            return

        # process files for each key:
        for file_key in unique_file_keys:
            # get all file versions for this key:
            file_versions = self._search_cache.find_file_versions(work_area, file_key) or {}

            # update thumbnail and versions for each version:
            thumb = None
            for _, version in sorted(file_versions.iteritems(), reverse=False):
                if version.thumbnail_path:
                    # this file version should have a thumbnail!
                    thumb = version.thumbnail
                else:
                    # lets use the current thumbnail for this version:
                    version.thumbnail = thumb

                # store the file versions on the file as well:
                version.versions = file_versions

        # update tooltips on all file items:
        for file_model_item in self._file_items(group_item):
            file_item = file_model_item.file_item
            tooltip = ""
            if file_item:
                tooltip = file_item.format_tooltip()
            file_model_item.setToolTip(tooltip)

        # emit data changed signal for all items in the group:
        row_count = group_item.rowCount()
        tl_idx = self.index(0, 0, group_item.index())
        br_idx = self.index(row_count - 1, 0, group_item.index())
        self.dataChanged.emit(tl_idx, br_idx)

    def _update_version_thumbnails(self, file_key, group_key, work_area):
        """
        Update the thumbnail for all versions of a file.  If a file version doesn't have a thumnail set and
        a previous version did then it will re-use the file from the previous version instead.

        :param file_key:    A unique key that identifies all versions of the same file
        :param group_key:   A unique key that represents a single file group
        :param work_area:   A WorkArea instance that all files in this group belong to
        """
        file_versions = self._search_cache.find_file_versions(work_area, file_key) or {}
        thumb = None
        for _, version in sorted(file_versions.iteritems(), reverse=False):
            if version.thumbnail_path:
                # this file version should have a thumbnail!
                thumb = version.thumbnail
            else:
                if version.thumbnail != thumb:
                    # lets use the current thumbnail for this version:
                    version.thumbnail = thumb

                    # emit a data changed signal for any model items that are affected:
                    version_items = self._find_current_items(group_key, version.key, version.version)
                    for item in version_items:
                        item.emitDataChanged()

    def _build_thumbnail(self, thumb_path_or_image):
        """
        Build a thumbnail from the specified path or QImage with uniform dimensions.

        :param thumb_path_or_image: A string representing the path on disk of the thumbnail to load
                                    or a QImage containing the thumbnail to use.
        :returns:                   A QPixmap of size 576/374 pixels containing the scaled thumbnail
        """
        # load the thumbnail
        thumb = QtGui.QPixmap(thumb_path_or_image)
        if not thumb or thumb.isNull():
            return

        # make sure the thumbnail is a good size with the correct aspect ratio:
        MAX_WIDTH = 576 # 96
        MAX_HEIGHT = 374 # 64
        ASPECT = float(MAX_WIDTH) / MAX_HEIGHT

        thumb_sz = thumb.size()
        thumb_aspect = float(thumb_sz.width()) / thumb_sz.height()
        max_thumb_sz = QtCore.QSize(MAX_WIDTH, MAX_HEIGHT)
        if thumb_aspect >= ASPECT:
            # scale based on width:
            if thumb_sz.width() > MAX_WIDTH:
                thumb_sz *= (float(MAX_WIDTH) / thumb_sz.width())
            else:
                max_thumb_sz *= (float(thumb_sz.width()) / MAX_WIDTH)
        else:
            # scale based on height:
            if thumb_sz.height() > MAX_HEIGHT:
                thumb_sz *= (float(MAX_HEIGHT) / thumb_sz.height())
            else:
                max_thumb_sz *= (float(thumb_sz.height()) / MAX_HEIGHT)

        if thumb_sz != thumb.size():
            thumb = thumb.scaled(thumb_sz.width(), thumb_sz.height(),
                                 QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        # create base pixmap with the correct aspect ratio that the thumbnail will fit in
        # and fill it with a transparent colour:
        thumb_base = QtGui.QPixmap(max_thumb_sz)
        thumb_base.fill(QtGui.QColor(QtCore.Qt.transparent))

        # create a painter to paint into this pixmap:
        painter = QtGui.QPainter(thumb_base)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            # paint the thumbnail into this base making sure it's centered:
            diff = max_thumb_sz - thumb.size()
            offset = diff / 2
            brush = QtGui.QBrush(thumb)
            painter.setBrush(brush)
            painter.translate(offset.width(), offset.height())
            painter.drawRect(0, 0, thumb.width(), thumb.height())
        finally:
            painter.end()

        return thumb_base
