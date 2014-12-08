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

from .find_files import FileFinder

class ModelFileItem(QtGui.QStandardItem):
    def __init__(self, file_item):
        
        item_name = "%s, v%0d" % (file_item.name, file_item.version)
        
        QtGui.QStandardItem.__init__(self, item_name)
        
        self._file_item = file_item
        
    @property
    def file_item(self):
        return self._file_item

overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
ShotgunOverlayWidget = overlay_widget.ShotgunOverlayWidget

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
            
    def _on_search_started(self):
        """
        """
        self.start_spin()
    
    def _on_files_found(self):
        """
        """
        self.hide(hide_errors=True)
    
    def _on_search_failed(self, msg):
        """
        """
        self.show_error_message(msg)


class FileModel(QtGui.QStandardItemModel):
    """
    """
    
    search_started = QtCore.Signal()
    files_found = QtCore.Signal()
    search_failed = QtCore.Signal(object)
    
    def __init__(self, parent=None):
        """
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        
        # we'll need a file finder to be able to find files:
        self._finder = FileFinder()
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        self._current_search_id = None
        
    def refresh_files(self, publish_filters, context):
        """
        Asynchronously refresh the list of files in the model based on the
        supplied filters and context.
        """
        # stop previous search:
        if self._current_search_id != None:
            self._finder.stop_search(self._current_search_id)
            self._current_search_id = None
        
        # emit search started signal:
        self.search_started.emit()        
        
        # clear existing data from model:
        self.clear()
        
        # start a new search with the file finder:
        self._current_search_id = self._finder.begin_search(publish_filters, context)
        
    def _on_finder_files_found(self, search_id, files):
        """
        Called when the finder has found some files.
        """
        if search_id != self._current_search_id:
            # ignore result
            return
        
        # add files to model:
        for file in files:
            file_item = ModelFileItem(file)
            self.appendRow(file_item)
            
        # emit signal:
        self.files_found.emit()
             
    
    def _on_finder_search_failed(self, search_id, error):
        """
        Called when the finder search fails for some reason!
        """
        if search_id != self._current_search_id:
            # ignore result
            return
        
        # emit signal:
        self.search_failed.emit(error)



