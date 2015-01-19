# Copyright (c) 2014 Shotgun Software Inc.
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
from sgtk import TankError

overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
ShotgunOverlayWidget = overlay_widget.ShotgunOverlayWidget

from .find_files import FileFinder

class FileModelOverlayWidget(ShotgunOverlayWidget):
    """
    """
    
    def __init__(self, model=None, parent=None):
        """
        """
        ShotgunOverlayWidget.__init__(self, parent)
        
        self._model = None
        self._connect_to_model(model)
        
    def set_model(self, model):
        """
        """
        self.hide()
        
        # search for a FileModel:
        while isinstance(model, QtGui.QAbstractProxyModel):
            model = model.sourceModel()

        if isinstance(model, FileModel):
            self._connect_to_model(model)

    def _connect_to_model(self, model):
        """
        """
        if model == self._model:
            return
        
        if self._model:
            self._model.search_started.disconnect(self._on_search_started)
            self._model.files_found.disconnect(self._on_files_found)
            self._model.search_failed.disconnect(self._on_search_failed)
            self._model = None
            self.hide(hide_errors=True)            
            
        if model:
            self._model = model
            self._model.search_started.connect(self._on_search_started)
            self._model.files_found.connect(self._on_files_found)
            self._model.search_failed.connect(self._on_search_failed)
            
    def _on_search_started(self, idx):
        """
        """
        self.start_spin()
    
    def _on_files_found(self, idx):
        """
        """
        self.hide(hide_errors=True)
    
    def _on_search_failed(self, idx, msg):
        """
        """
        self.show_error_message(msg)


class FileModel(QtGui.QStandardItemModel):
    """
    """
    
    search_started = QtCore.Signal(object)
    files_found = QtCore.Signal(object)
    search_failed = QtCore.Signal(object, object)
    
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    NODE_TYPE_ROLE = _BASE_ROLE + 1
    (FILE_NODE_TYPE, GROUP_NODE_TYPE, FOLDER_NODE_TYPE) = range(3)
    FILE_ITEM_ROLE = _BASE_ROLE + 2
    
    class _BaseItem(QtGui.QStandardItem):
        """
        """
        def __init__(self, typ, text=None):
            """
            """
            QtGui.QStandardItem.__init__(self, text)
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
        def __init__(self, file_item):
            """
            """
            FileModel._BaseItem.__init__(self, typ=FileModel.FILE_NODE_TYPE)
            self._file_item = file_item
            
        @property
        def file_item(self):
            return self._file_item
    
        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == QtCore.Qt.DisplayRole:
                return "%s, v%0d" % (self._file_item.name, self._file_item.version)
            elif role == FileModel.FILE_ITEM_ROLE:
                return self._file_item
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
                self._file_item = value
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 
    
    class _FolderItem(_BaseItem):
        """
        """
        def __init__(self, name):
            FileModel._BaseItem.__init__(self, typ=FileModel.FOLDER_NODE_TYPE, text=name)
    
    class _GroupItem(_BaseItem):
        """
        """
        def __init__(self, name):
            FileModel._BaseItem.__init__(self, typ=FileModel.GROUP_NODE_TYPE, text=name)    
    
    
    def __init__(self, sg_data_retriever, parent=None):
        """
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        
        self._sg_data_retriever = sg_data_retriever
        
        # we'll need a file finder to be able to find files:
        self._finder = FileFinder()
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        
        self._in_progress_searches = {}
        
        
    def refresh_files(self, search_details):
        """
        Asynchronously refresh the list of files in the model based on the
        supplied filters and context.
        """
        # stop all previous searches:
        search_ids = self._in_progress_searches.keys()
        self._in_progress_searches = {}
        for id in search_ids:
            self._finder.stop_search(id)
    
        # clear existing data from model:
        self.clear()
        
        # start any searches necessary for the item and it's children!
        self._begin_searches_r(search_details, self.invisibleRootItem(), True)
        
    def _begin_searches_r(self, search_details, model_item, is_root=False):
        """
        """
        new_item = None
        if is_root:
            new_item = model_item
            
            # always want to search for the root item if we can:
            if search_details.entity or search_details.step or search_details.task:
                search_id = self._finder.begin_search(search_details)
                self._in_progress_searches[search_id] = model_item
                
                # emit signal that we have started a new search for this index:
                self.search_started.emit(model_item.index())
        
        elif search_details.is_leaf:
            # add a 'group' item to the model:
            new_item = FileModel._GroupItem(search_details.name)
            model_item.appendRow(new_item)
            new_index = new_item.index()
            
            # start a search for this new group:
            search_id = self._finder.begin_search(search_details)
            self._in_progress_searches[search_id] = new_item
            
            # emit signal that we have started a new search for this index:
            self.search_started.emit(new_index)
        else:
            # add a folder item to the model:
            new_item = FileModel._FolderItem(search_details.name)
            model_item.appendRow(new_item)
            
        # recurse over all children:
        for child_search_details in search_details.children:
            self._begin_searches_r(child_search_details, new_item)
        
        """
        new_model_item = QtGui.QStandardItem(search_details.name)
        model_item.appendRow(new_model_item)
        new_item_index = new_model_item.index() 
        
        if search_details.is_leaf:
            if search_details.entity or search_details.step or search_details.task:
                search_id = self._finder.begin_search(search_details)
                self._in_progress_searches[search_id] = new_model_item
            
        for child_search_details in search_details.children:
            self._begin_searches_r(child_search_details, new_model_item)
        """
        
    def _on_finder_files_found(self, search_id, files):
        """
        Called when the finder has found some files.
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        parent_model_item = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])
        
        print "FOUND %d FILES FOR SEARCH %d" % (len(files), search_id)
        
        # add files to model:
        for file in files:
            file_item = FileModel._FileItem(file)
            parent_model_item.appendRow(file_item)
            
        # emit signal:
        self.files_found.emit(parent_model_item.index())
    
    def _on_finder_search_failed(self, search_id, error):
        """
        Called when the finder search fails for some reason!
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        parent_model_item = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])
        
        # emit signal:
        self.search_failed.emit(parent_model_item.index(), error)



