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

from .find_files import FileFinder

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
            self.environment = None
            self.file_info = {}# file.key:_CachedFileInfo()

    def __init__(self):
        """
        """
        self._cache = {}
        
    def add(self, environment, files_and_items):
        """
        """
        # first build the cache entry from the list of files:
        entry = _SearchCache._CacheEntry()
        entry.environment = environment
        for file, item in files_and_items:
            version_info = _SearchCache._CachedFileVersionInfo(file, weakref.ref(item))
            entry.file_info.setdefault(file.key, _SearchCache._CachedFileInfo()).versions[file.version] = version_info
        
        # construct the key:
        key_entity = (environment.context.task or environment.context.step 
                      or environment.context.entity or environment.context.project)
        key = self._construct_key(key_entity, environment.context.user)
        
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
        
        return (files, entry.environment)
        
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
            self.entity = None
            self.child_entities = []
            self.name = name
            self.is_leaf = False
            
        def __repr__(self):
            return ("%s\n"
                    " - Entity: %s\n"
                    " - Task: %s\n"
                    " - Step: %s\n"
                    " - Is leaf: %s\n%s"
                    % (self.name, self.entity, self.task, self.step, self.is_leaf, self.child_entities))
    
    # signals
    search_started = QtCore.Signal(object)
    files_found = QtCore.Signal(object)
    search_failed = QtCore.Signal(object, object)
    
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    GROUP_NODE_ROLE = _BASE_ROLE + 1
    FILE_ITEM_ROLE = _BASE_ROLE + 2
    ENVIRONMENT_ROLE = _BASE_ROLE + 6
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
        def __init__(self, file_item, environment):
            """
            """
            FileModel._BaseItem.__init__(self, typ=FileModel.FILE_NODE_TYPE)
            self._file_item = file_item
            if file_item:
                file_item.data_changed.connect(self._on_file_data_changed)
            self._environment = environment
            
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
            elif role == FileModel.ENVIRONMENT_ROLE:
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
            elif role == FileModel.ENVIRONMENT_ROLE:
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
    
    class _GroupItem(_BaseItem):
        """
        """
        def __init__(self, name, environment=None):
            FileModel._BaseItem.__init__(self, typ=FileModel.GROUP_NODE_TYPE, text=name)
            
            self._search_status = FileModel.SEARCHING
            self._search_msg = ""
            self._environment = environment
    
        @property
        def environment(self):
            return self._environment
    
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
            elif role == FileModel.ENVIRONMENT_ROLE:
                return self._environment
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
            elif role == FileModel.ENVIRONMENT_ROLE:
                self._environment = value
                self.emitDataChanged()
            elif role == FileModel.GROUP_NODE_ROLE:
                # can't be set!
                pass
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 
    
    def __init__(self, sg_data_retriever, parent=None):
        """
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        
        # sg data retriever is used to download thumbnails in the background
        self._sg_data_retriever = sg_data_retriever
        if self._sg_data_retriever:
            self._sg_data_retriever.work_completed.connect(self._on_data_retriever_work_completed)
            self._sg_data_retriever.work_failure.connect(self._on_data_retriever_work_failed)
        
        self._search_cache = _SearchCache()
        self._in_progress_searches = {}
        self._pending_thumbnail_requests = {}
        
        # we'll need a file finder to be able to find files:
        self._finder = FileFinder()
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        
    def get_file_versions(self, key, env):
        """
        """
        return self._search_cache.find_file_versions(key, env.context)

    def item_from_file(self, file, env):
        """
        """
        if not file or not env:
            return None
        
        # find the item using the cache:
        return self._search_cache.find_item_for_file(file.key, file.version, env.context)

    def refresh_files(self, search_details, force=False):
        """
        Asynchronously refresh the list of files in the model based on the
        supplied filters and context.
        """
        app = sgtk.platform.current_bundle()
        
        # stop all previous searches:
        search_ids = self._in_progress_searches.keys()
        self._in_progress_searches = {}
        for id in search_ids:
            self._finder.stop_search(id)
    
        # clear existing data from model:
        # (TODO) make sure this is safe!
        self.clear()
        
        for search in search_details:
            # add a 'group' item to the model:
            new_item = FileModel._GroupItem(search.name)
            new_item.set_search_status(FileModel.SEARCHING)
            self.invisibleRootItem().appendRow(new_item)
            new_index = new_item.index()

            # emit signal that we have started a new search for this index:
            self.search_started.emit(new_index)

            # add folder items for any children:
            for child in search.child_entities:
                child_name = child.get("name", "Entity")
                child_entity = child.get("entity")
                
                # add a folder item to the model:
                folder_item = FileModel._FolderItem(child_name, child_entity)
                folder_item.setIcon(QtGui.QIcon(":/tk-multi-workfiles/folder_512x400.png"))
                new_item.appendRow(folder_item)

            if not search.entity:
                # done!
                new_item.set_search_status(FileModel.SEARCH_COMPLETED)
                continue

            if not force:
                # check to see if we already have results from this search in the cache:
                cached_result = self._search_cache.find(search.entity)
                if cached_result:
                    # we have a cached result so lets just use this instead!
                    files, environment = cached_result
                    self._process_files(files, environment, new_item)
                    new_item.setData(environment, FileModel.ENVIRONMENT_ROLE)
                    new_item.set_search_status(FileModel.SEARCH_COMPLETED)
                    self.files_found.emit(new_item.index())
                    continue
            
            # start a search for this new group:
            search_id = self._finder.begin_search(search.entity)
            self._in_progress_searches[search_id] = new_item
        
    def _process_files(self, files, environment, parent_item):
        """
        """
        new_rows = []
        for file in files:
            # create a new model item for this file:
            new_item = FileModel._FileItem(file, environment)
            new_rows.append(new_item)

            # if this is from a published file then we want to retrieve the thumbnail
            # if one is available:                        
            if file.is_published and file.thumbnail_path and not file.thumbnail:
                # request the thumbnail using the data retriever:
                request_id = self._sg_data_retriever.request_thumbnail(file.thumbnail_path, 
                                                                       "PublishedFile", 
                                                                       file.published_file_id,
                                                                       "image")
                self._pending_thumbnail_requests[request_id] = (file, environment)

        # update cache:
        files_and_items = zip(files, new_rows)
        self._search_cache.add(environment, files_and_items)

        # add new rows to model:
        if new_rows:
            # we have new rows so lets add them to the model:
            parent_item.appendRows(new_rows)
        
    def _on_finder_files_found(self, search_id, file_list, environment):
        """
        Called when the finder has found some files.
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        parent_item = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])

        # process files:
        self._process_files(file_list, environment, parent_item)
            
        # update the parent group item to indicate that the search has been completed:
        if isinstance(parent_item, FileModel._GroupItem):
            parent_item.setData(environment, FileModel.ENVIRONMENT_ROLE)
            parent_item.set_search_status(FileModel.SEARCH_COMPLETED)
            
        # emit signal indicating that the search has been completed:
        self.files_found.emit(parent_item.index())
    
    def _on_finder_search_failed(self, search_id, error):
        """
        Called when the finder search fails for some reason!
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        parent_item = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])
        
        #print "SEARCH %d FAILED: %s" % (search_id, error)
        
        if isinstance(parent_item, FileModel._GroupItem):
            parent_item.set_search_status(FileModel.SEARCH_FAILED, error)
        
        # emit signal:
        self.search_failed.emit(parent_item.index(), error)        
        
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




