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
from sgtk import TankError

from .file_finder import FileFinder

class _SearchCache(object):
    """
    """
    class _CachedFileVersionInfo(object):
        def __init__(self, file, model_item_ref=None):
            self.file = file
            self.model_item_ref = model_item_ref
    
    class _CachedFileInfo(object):
        def __init__(self):
            self.versions = {}# file.version:_CachedFileVersionInfo #file 

    class _CacheEntry(object):
        def __init__(self):
            self.work_area = None
            self.file_info = {}# file.key:_CachedFileInfo()

    def __init__(self):
        """
        """
        self._cache = {}
        
    def add(self, work_area, files_and_items):
        """
        """
        # first build the cache entry from the list of files:
        entry = _SearchCache._CacheEntry()
        entry.work_area = work_area
        for file, item in files_and_items:
            version_info = _SearchCache._CachedFileVersionInfo(file, weakref.ref(item))
            entry.file_info.setdefault(file.key, _SearchCache._CachedFileInfo()).versions[file.version] = version_info
        
        # construct the key:
        key_entity = (work_area.context.task or work_area.context.step 
                      or work_area.context.entity or work_area.context.project)
        key = self._construct_key(key_entity, work_area.context.user)
        
        self._cache[key] = entry
    
    def find_file_versions(self, file_key, ctx):
        """
        """
        key_entity = ctx.task or ctx.step or ctx.entity or ctx.project
        key = self._construct_key(key_entity, ctx.user)
        entry = self._cache.get(key)
        if not entry:
            # return None as we don't have a cached result for this context!
            return None
        
        file_info = entry.file_info.get(file_key)
        if not file_info:
            return {}
        
        return dict([(v, info.file) for v, info in file_info.versions.iteritems()])

    def find_item_for_file(self, file_key, file_version, ctx):
        """
        """
        key_entity = ctx.task or ctx.step or ctx.entity or ctx.project
        key = self._construct_key(key_entity, ctx.user)
        entry = self._cache.get(key)
        if not entry:
            # return None as we don't have a cached result for this context!
            return None
        
        file_info = entry.file_info.get(file_key)
        if not file_info:
            return None
        
        version_info = file_info.versions.get(file_version)
        if version_info == None or not version_info.model_item_ref:
            return None
        
        return version_info.model_item_ref()

    def find(self, entity, user=None):
        """
        """
        key = self._construct_key(entity, user)
        entry = self._cache.get(key)
        if not entry:
            return None

        files = []
        for file_info in entry.file_info.values():
            files.extend([version_info.file for version_info in file_info.versions.values()])
        
        return (files, entry.work_area)
        
    def _construct_key(self, entity, user):
        """
        """
        # add in defaults for project and user if they aren't set:
        app = sgtk.platform.current_bundle()
        user = user or app.context.user

        key_parts = []
        key_parts.append((entity["type"], entity["id"]) if entity else None)
        key_parts.append((user["type"], user["id"]) if user else None)
        return tuple(key_parts)

class FileModel(QtGui.QStandardItemModel):
    """
    """
    class SearchDetails(object):
        def __init__(self, name=None):
            self.name = name
            self.entity = None
            self.child_entities = []
            self.is_leaf = False

        def __repr__(self):
            return ("%s\n"
                    " - Entity: %s\n"
                    " - Is leaf: %s\n%s"
                    % (self.name, self.entity, self.is_leaf, self.child_entities))
    
    # signals
    #search_started = QtCore.Signal(object)
    #files_found = QtCore.Signal(object)
    #search_failed = QtCore.Signal(object, object)
    
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    GROUP_NODE_ROLE = _BASE_ROLE + 1
    FILE_ITEM_ROLE = _BASE_ROLE + 2
    WORK_AREA_ROLE = _BASE_ROLE + 6
    SEARCH_STATUS_ROLE = _BASE_ROLE + 3
    SEARCH_MSG_ROLE = _BASE_ROLE + 4

    NODE_TYPE_ROLE = _BASE_ROLE + 5
    (FILE_NODE_TYPE, GROUP_NODE_TYPE, FOLDER_NODE_TYPE) = range(3)
    
    (SEARCHING, SEARCH_COMPLETED, SEARCH_FAILED) = range(3)
    
    class _BaseItem(QtGui.QStandardItem):
        """
        """
        def __init__(self, typ, text=None):
            """
            """
            QtGui.QStandardItem.__init__(self, text or "")
            self._type = typ
            
        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.NODE_TYPE_ROLE:
                return self._type
            else:
                # just return the default implementation:
                return QtGui.QStandardItem.data(self, role)
    
        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.NODE_TYPE_ROLE:
                # do nothing as the data can't be set:
                pass
            else:
                # call the base implementation:
                QtGui.QStandardItem.setData(self, value, role) 
    
    class _FileItem(_BaseItem):
        """
        """
        def __init__(self, file_item, environment, search_id=None):
            """
            """
            FileModel._BaseItem.__init__(self, typ=FileModel.FILE_NODE_TYPE)
            self._file_item = file_item
            if file_item:
                file_item.data_changed.connect(self._on_file_data_changed)
            self._environment = environment
            self.search_id = search_id

        @property
        def file_item(self):
            return self._file_item
        
        @property
        def environment(self):
            return self._environment

        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == QtCore.Qt.DisplayRole:
                return "%s, v%0d" % (self._file_item.name, self._file_item.version)
            elif role == FileModel.FILE_ITEM_ROLE:
                return self._file_item
            elif role == FileModel.WORK_AREA_ROLE:
                return self._environment
            else:
                # just return the default implementation:
                return FileModel._BaseItem.data(self, role)
    
        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == QtCore.Qt.DisplayRole:
                # do nothing as it can't be set!
                pass
            elif role == FileModel.FILE_ITEM_ROLE:
                if self._file_item:
                    file_item.data_changed.disconnect(self._on_file_data_changed)
                self._file_item = value
                if self._file_item:
                    file_item.data_changed.connect(self._on_file_data_changed)
                self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                self._environment = value
                self.emitDataChanged()
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 
    
        def _on_file_data_changed(self):
            """
            """
            self.emitDataChanged()
    
    class _FolderItem(_BaseItem):
        """
        """
        def __init__(self, name, entity):
            FileModel._BaseItem.__init__(self, typ=FileModel.FOLDER_NODE_TYPE, text=name)
            self._entity = entity
            
        @property
        def entity(self):
            return self._entity
    
    class _GroupItem(_BaseItem):
        """
        """
        def __init__(self, name, entity=None, work_area=None):
            FileModel._BaseItem.__init__(self, typ=FileModel.GROUP_NODE_TYPE, text=name)
            
            self._search_status = FileModel.SEARCH_COMPLETED
            self._search_msg = ""
            self._work_area = work_area
            self._entity = entity
    
        @property
        def entity(self):
            return self._entity
    
        @property
        def work_area(self):
            return self._work_area
        @work_area.setter
        def work_area(self, work_area):
            self._work_area = work_area
            self.emitDataChanged()

        @property
        def search_status(self):
            return self._search_status

        def set_search_status(self, status, msg=None):
            self._search_status = status
            self._search_msg = msg
            self.emitDataChanged()

        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                return self._search_status
            elif role == FileModel.SEARCH_MSG_ROLE:
                return self._search_msg
            elif role == FileModel.WORK_AREA_ROLE:
                return self._work_area
            elif role == FileModel.GROUP_NODE_ROLE:
                # always return true!
                return True
            else:
                # just return the default implementation:
                return FileModel._BaseItem.data(self, role)
    
        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                self._search_status = value
                self.emitDataChanged()
            elif role == FileModel.SEARCH_MSG_ROLE:
                self._search_msg = value
                self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                self._environment = value
                self.emitDataChanged()
            elif role == FileModel.GROUP_NODE_ROLE:
                # can't be set!
                pass
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 
    
    # Signal emitted when the available sandbox users have changed
    available_sandbox_users_changed = QtCore.Signal(object)
    
    def __init__(self, sg_data_retriever, parent=None):
        """
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        
        app = sgtk.platform.current_bundle()
        
        # sg data retriever is used to download thumbnails in the background
        self._sg_data_retriever = sg_data_retriever
        if self._sg_data_retriever:
            self._sg_data_retriever.work_completed.connect(self._on_data_retriever_work_completed)
            self._sg_data_retriever.work_failure.connect(self._on_data_retriever_work_failed)
        
        # details about the current entities and users that are represented
        # in this model.
        self._current_searches = []
        self._current_users = [sgtk.util.get_current_user(app.sgtk)]
        self._entity_work_areas = {}
        self._entity_user_group_map = {}
        self._in_progress_searches = {}

        self._search_cache = _SearchCache()
        self._pending_thumbnail_requests = {}
        
        # we'll need a file finder to be able to find files:
        self._finder = FileFinder()
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.publishes_found.connect(self._on_finder_publishes_found)
        self._finder.search_completed.connect(self._on_finder_search_completed)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        self._finder.work_area_found.connect(self._on_finder_work_area_found)
        
    def get_file_versions(self, key, env):
        """
        """
        return self._search_cache.find_file_versions(key, env.context)

    def item_from_file(self, file, context):
        """
        """
        if not file or not context:
            return None
        
        # find the item using the cache:
        return self._search_cache.find_item_for_file(file.key, file.version, context)

    # Interface for modifying the entities in the model:
    def set_entity_searches(self, searches):
        """
        """
        # stop any in-progress searches:
        self._stop_in_progress_searches()

        # update groups:
        self._current_searches = searches or []
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    # Interface for modifying the users in the model:
    def set_users(self, users):
        """
        """
        # stop any in-progress searches:
        self._stop_in_progress_searches()

        # update groups:
        self._current_users = users or []
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    def async_refresh(self):
        """
        """
        # stop any current searches:
        self._stop_in_progress_searches()
        # and restart all searches:
        self._start_searches()

    def clear(self):
        """
        """
        # stop all current searches:
        self._stop_in_progress_searches()

        # clear existing data from model:
        # (TODO) make sure this is safe!
        QtGui.QStandardItemModel.clear(self)

    # ------------------------------------------------------------------------------------------
    # protected methods

    def _group_items(self):
        """
        """
        for ri in range(self.invisibleRootItem().rowCount()):
            child_item = self.invisibleRootItem().child(ri)
            if isinstance(child_item, FileModel._GroupItem):
                yield child_item

    def _file_items(self, parent_item):
        """
        """
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, FileModel._FileItem):
                yield child_item

    def _entity_key(self, entity_dict):
        """
        """
        if not entity_dict:
            return (None, None)
        else:
            return (entity_dict.get("type"), entity_dict.get("id"))

    def _start_searches(self):
        """
        """
        if not self._current_searches:
            # nothing to do!
            return

        for search in self._current_searches:
            
            if not search.entity:
                continue
            
            # update all existing group items for this entity and all users to indicate
            # that we are searching for files
            entity_key = self._entity_key(search.entity)
            for user in self._current_users:
                user_key = self._entity_key(user)
                group_key = (entity_key, user_key)
                group_idx = self._entity_user_group_map.get(group_key)
                if group_idx and group_idx.isValid():
                    # update it to indicate that searching has started:
                    group_item = self.itemFromIndex(group_idx)
                    group_item.set_search_status(FileModel.SEARCHING)

            # and actually start the search:
            search_id = self._finder.begin_search(search.entity, self._current_users)
            self._in_progress_searches[search_id] = search

    def _stop_in_progress_searches(self):
        """
        """
        search_ids = self._in_progress_searches.keys()
        self._in_progress_searches = {}
        for id in search_ids:
            #print "Stopping search %s" % id
            self._finder.stop_search(id)

    def _update_groups(self):
        """
        """
        app = sgtk.platform.current_bundle()

        valid_group_keys = set()
        if self._current_searches and self._current_users:

            # get details about the users to run searches for:
            current_user = sgtk.util.get_current_user(app.sgtk)
            current_user_key = self._entity_key(current_user)
            have_current_user = False
            for user in self._current_users:
                if self._entity_key(user) == current_user_key:
                    have_current_user = True
                    break
            primary_user_key = current_user_key if have_current_user else self._entity_key(self._current_users[0])

            # iterate over the searches, making sure that group nodes exist as needed
            previous_group_idx = None
            for search in self._current_searches:
                if not search.entity:
                    # this search doesn't represent an entity so we won't need to search
                    # for files.  In which case we can just add a group item with the
                    # correct name and be done with it!  We also only need one of these
                    # rather than (potentially) one per user!
                    continue

                entity_key = self._entity_key(search.entity)

                # iterate over each user for this group:
                for user in self._current_users:

                    user_key = self._entity_key(user)
                    group_key = (entity_key, user_key)
                    current_group_idx = self._entity_user_group_map.get(group_key)

                    if current_group_idx is not None:
                        # check validity of this model index:
                        if not current_group_idx.isValid():
                            # item has been removed and index is no longer valid!
                            current_group_idx = None
                            del self._entity_user_group_map[group_key]

                    if not current_group_idx:
                        # we don't have a group node for this entity/user combination:
                        cached_result = self._search_cache.find(search.entity, user)
                        if (user_key == primary_user_key or cached_result):
                            # always add a group for the primary user or if we already have a cached result:
                            group_item = FileModel._GroupItem(search.name, search.entity)
                            self.invisibleRootItem().insertRow(previous_group_idx.row()+1 if previous_group_idx else 0, 
                                                               group_item)
                            current_group_idx = QtCore.QPersistentModelIndex(group_item.index())
                            self._entity_user_group_map[group_key] = current_group_idx 

                            if cached_result:
                                # we have a cached result so populate the group:
                                files, environment = cached_result
                                self._process_files(files, environment, group_item)
                                group_item.work_area = environment

                    if current_group_idx:
                        # make sure the name and entity children are up-to-date:
                        group_item = self.itemFromIndex(current_group_idx)
                        self._update_group_child_entity_items(group_item, search.child_entities or [])

                        # keep track of the last valid group index:
                        previous_group_idx = current_group_idx

                    valid_group_keys.add(group_key)

        # remove any groups that are no longer needed:
        new_group_map = {}
        for group_key, group_idx in self._entity_user_group_map.iteritems():
            if group_key not in valid_group_keys:
                if group_idx.isValid():
                    # remove group:
                    self.removeRow(group_idx.row(), group_idx.parent())
            else:
                new_group_map[group_key] = group_idx
        self._entity_user_group_map = new_group_map

    def _update_group_child_entity_items(self, parent_item, child_details):
        """
        """
        # build a map, mapping from entity to item for all current children:
        entity_item_map = {}
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, FileModel._FolderItem):
                child_name = child_item.text()
                child_entity = child_item.entity
                child_key = (child_name, child_entity["type"], child_entity["id"])
                entity_item_map[child_key] = child_item

        # add any children that aren't already children of the parent item:
        valid_child_keys = set()
        for details in child_details:
            child_name = details.get("name", "Entity")
            child_entity = details.get("entity")
            child_key = (child_name, child_entity["type"], child_entity["id"])
            current_item = entity_item_map.get(child_key)
            if current_item is None:
                # add a new folder item to the model:
                folder_item = FileModel._FolderItem(child_name, child_entity)
                folder_item.setIcon(QtGui.QIcon(":/tk-multi-workfiles2/folder_512x400.png"))
                parent_item.appendRow(folder_item)
            # keep track of all valid child keys:
            valid_child_keys.add(child_key)

        # finally, remove any children that are no longer needed
        for key in (set(entity_item_map.keys()) - valid_child_keys):
            parent_item.removeRow(entity_item_map[key].index().row())

    def _process_files(self, files, environment, parent_item, have_local=True, have_publishes=True):
        """
        """
        # get details about existing items:
        files_and_items = {}
        prev_local_file_versions = set()
        prev_publish_file_versions = set()
        for model_item in self._file_items(parent_item):
            file = model_item.file_item
            file_version_key = (file.key, file.version)
            files_and_items[file_version_key] = (file, model_item)
            if file.is_local:
                prev_local_file_versions.add(file_version_key)
            if file.is_published:
                prev_publish_file_versions.add(file_version_key)

        # iterate through files, adding items or updating them as needed:
        new_rows = []
        valid_file_versions = set()
        for new_file in files:
            file_version_key = (new_file.key, new_file.version)
            current_file, model_item = files_and_items.get(file_version_key, (None, None))
            if current_file and model_item:
                # update the existing file:
                if new_file.is_published:
                    current_file.update(is_published=True, publish_path=new_file.publish_path, details=new_file.details)
                if new_file.is_local:
                    current_file.update(is_local=True, path=new_file.path, details=new_file.details)
            else:
                # add a new item:
                model_item = FileModel._FileItem(new_file, environment)#, search_id)
                new_rows.append(model_item)
                files_and_items[file_version_key] = (new_file, model_item)

            valid_file_versions.add(file_version_key)

            # if this is from a published file then we want to retrieve the thumbnail
            # if one is available:
            if new_file.is_published and new_file.thumbnail_path and not new_file.thumbnail:
                # request the thumbnail using the data retriever:
                request_id = self._sg_data_retriever.request_thumbnail(new_file.thumbnail_path, 
                                                                       "PublishedFile", 
                                                                       new_file.published_file_id,
                                                                       "image")
                self._pending_thumbnail_requests[request_id] = (new_file, environment)

        # update any files that are no longer in the corresponding set:
        if have_local:
            for file_version in prev_local_file_versions:
                if file_version not in valid_file_versions:
                    # file is no longer local!
                    file, _ = files_and_items[file_version]
                    file.update(is_local=False)

        if have_publishes:
            for file_version in prev_publish_file_versions:
                if file_version not in valid_file_versions:
                    # file is no longer a publish!
                    file, _ = files_and_items[file_version]
                    file.update(is_published=False)

        # figure out the set of file-version keys that are no longer valid and should be removed
        # completely from the model:
        file_versions_to_remove = set()
        if have_local:
            if not have_publishes:
                # all local that aren't published
                file_versions_to_remove = prev_local_file_versions - prev_publish_file_versions
            else:
                # all local and all published
                file_versions_to_remove = prev_local_file_versions | prev_publish_file_versions
        elif have_publishes:
            # all published that aren't local
            file_versions_to_remove = prev_publish_file_versions - prev_local_file_versions
        # substract all valid files from the set:
        file_versions_to_remove = file_versions_to_remove - valid_file_versions

        # update the cache:
        valid_files_and_items = [f for k, f in files_and_items.iteritems() if k not in file_versions_to_remove]
        self._search_cache.add(environment, valid_files_and_items)

        # remove items:
        for file_version_key in file_versions_to_remove:
            _, item_to_remove = files_and_items[file_version_key]
            item_to_remove.parent().removeRow(item_to_remove.row())

        # and finally, add new rows to the model:
        if new_rows:
            # we have new rows so lets add them to the model:
            parent_item.appendRows(new_rows)

    def _on_finder_work_area_found(self, search_id, work_area):
        """
        Called when the finder has found a work area for the search.
        """
        #print "[%d] Found Sandbox Users: %s" % (search_id, work_area.work_area_sandbox_users)
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        search = self._in_progress_searches[search_id]
        entity_key = self._entity_key(search.entity)

        # keep track of work area for this entity:
        self._entity_work_areas[entity_key] = work_area

        # consolidate list of sandbox users for all current work areas:
        users_by_id = {}
        handled_entities = set()
        for search in self._in_progress_searches.values():
            entity_key = self._entity_key(search.entity)
            if entity_key in handled_entities:
                continue
            handled_entities.add(entity_key)

            area = self._entity_work_areas.get(entity_key)
            if area:
                for user in area.sandbox_users:
                    if user:
                        users_by_id[user["id"]] = user

        self.available_sandbox_users_changed.emit(users_by_id.values())

    def _on_finder_files_found(self, search_id, file_list, environment):
        """
        Called when the finder has found some files.
        """
        #print "Found %d files for search %s, user '%s'" % (len(file_list), search_id, environment.context.user["name"])
        self._process_found_files(search_id, file_list, environment, have_local=True, have_publishes=False)
    
    def _on_finder_publishes_found(self, search_id, file_list, environment):
        """
        """
        #print "Found %d publishes for search %s, user '%s'" % (len(file_list), search_id, environment.context.user["name"])
        self._process_found_files(search_id, file_list, environment, have_local=False, have_publishes=True)

    def _process_found_files(self, search_id, file_list, environment, have_local, have_publishes):
        """
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        search = self._in_progress_searches[search_id]
        search_user = environment.context.user

        # find the group item for this search:
        group_key = (self._entity_key(search.entity), self._entity_key(search_user))
        group_idx = self._entity_user_group_map.get(group_key)
        group_item = None
        if group_idx and group_idx.isValid():
            group_item = self.itemFromIndex(group_idx)
            # and make sure the environment is up-to-date:
            group_item.work_area = environment
        else:
            if not file_list:
                # no files so don't bother creating a group!
                return

            # we don't have a group item for this search so lets add one now:
            group_item = FileModel._GroupItem(search.name, search.entity, environment)
            # (TODO) need to insert it into the right place in the list!
            self.invisibleRootItem().appendRow(group_item)
            group_idx = QtCore.QPersistentModelIndex(group_item.index())
            self._entity_user_group_map[group_key] = group_idx

            # add children
            self._update_group_child_entity_items(group_item, search.child_entities or [])

        # process files:
        self._process_files(file_list, environment, group_item, have_local, have_publishes)#, search_id)

    def _on_finder_search_completed(self, search_id):
        """
        Called when the finder search is completed
        """
        #print "Search %s completed" % search_id
        self._process_search_completion(search_id, FileModel.SEARCH_COMPLETED)

    def _on_finder_search_failed(self, search_id, error_msg):
        """
        Called when the finder search fails for some reason!
        """
        #print "Search %d failed - %s" % (search_id, error_msg)
        self._process_search_completion(search_id, FileModel.SEARCH_FAILED, error_msg)

    def _process_search_completion(self, search_id, status, error_msg=None):
        """
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        search = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])

        entity_key = self._entity_key(search.entity)
        for user in self._current_users:
            group_key = (entity_key, self._entity_key(user))
            group_idx = self._entity_user_group_map.get(group_key)
            if not group_idx or not group_idx.isValid():
                continue

            group_item = self.itemFromIndex(group_idx)
            group_item.set_search_status(status, error_msg)

    def _on_data_retriever_work_completed(self, uid, request_type, data):
        """
        """
        if uid not in self._pending_thumbnail_requests:
            return
        file, env = self._pending_thumbnail_requests[uid]
        del(self._pending_thumbnail_requests[uid])
        
        thumb_path = data.get("thumb_path")
        if not thumb_path:
            return

        # create a pixmap for the path:
        thumb = self._build_thumbnail(thumb_path)
        if not thumb:
            return

        # update the thumbnail on the file for this item:
        file.thumbnail = thumb
    
        # See of there are any work file versions of this file that don't have a
        # thumbnail that could make use of this thumbnail:
        file_versions = self.get_file_versions(file.key, env) or {}
        
        for v, file_version in sorted(file_versions.iteritems(), reverse=True):
            if (v > file_version.version 
                or file_version.is_published 
                or (not file_version.is_local)
                or file_version.thumbnail_path
                or file_version.thumbnail):
                continue

            # we can use the thumbnail for this version of the work file - yay!             
            file_version.thumbnail = thumb

    def _build_thumbnail(self, thumb_path):
        """
        """
        # load the thumbnail
        thumb = QtGui.QPixmap(thumb_path)
        if not thumb or thumb.isNull():
            return
        
        # make sure the thumbnail is a good size with the correct aspect ratio:
        MAX_WIDTH = 576#96
        MAX_HEIGHT = 374#64
        ASPECT = float(MAX_WIDTH)/MAX_HEIGHT
        
        thumb_sz = thumb.size()
        thumb_aspect = float(thumb_sz.width())/thumb_sz.height()
        max_thumb_sz = QtCore.QSize(MAX_WIDTH, MAX_HEIGHT)
        if thumb_aspect >= ASPECT:
            # scale based on width:
            if thumb_sz.width() > MAX_WIDTH:
                thumb_sz *= (float(MAX_WIDTH)/thumb_sz.width())
            else:
                max_thumb_sz *= (float(thumb_sz.width())/MAX_WIDTH)
        else:
            # scale based on height:
            if thumb_sz.height() > MAX_HEIGHT:
                thumb_sz *= (float(MAX_HEIGHT)/thumb_sz.height())
            else:
                max_thumb_sz *= (float(thumb_sz.height())/MAX_HEIGHT)

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
            offset = diff/2
            brush = QtGui.QBrush(thumb)
            painter.setBrush(brush)
            painter.translate(offset.width(), offset.height())
            painter.drawRect(0, 0, thumb.width(), thumb.height())
        finally:
            painter.end()
        
        return thumb_base
    
    def _on_data_retriever_work_failed(self, uid, error_msg):
        """
        """
        if uid in self._pending_thumbnail_requests:
            del(self._pending_thumbnail_requests[uid])
        #print "Failed to find thumbnail for id %s: %s" % (uid, error_msg)        




