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
        print "FOUND FILES"
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
        print "FOUND FILES FAILED: '%s'" % error
        if search_id != self._current_search_id:
            # ignore result
            return
        
        # emit signal:
        self.search_failed.emit(error)
        
    #def find_files(self, publish_filters, context):
    #    """
    #    """
    #    # clear current file list:
    #    self.clear()
    #    
    #    app = sgtk.platform.current_bundle()
    #    try:
    #        templates = get_templates_for_context(context, ["template_work", "template_publish"])
    #        work_template = templates.get("template_work")
    #        publish_template = templates.get("template_publish")
    #    except TankError, e:
    #        # had problems getting the work file settings for the specified context!
    #        app.log_debug("Failed to retrieve configuration: %s" % e)
    #        return
    #
    #    finder = FileFinder(sgtk.platform.current_bundle())
    #    files = finder.find_files(work_template, publish_template, context)
    #    print "Found %d files!" % len(files)
    #    
    #    # and add them to the model:
    #    # ...
    #    for file in files:
    #        file_item = FileItem(file)
    #        self.appendRow(file_item)
    #
    #    
    #def _on_publishes_model_data_refreshed(self, data_changed):
    #    """
    #    """
    #    if not data_changed:
    #        return
    #    
    #    # update this model to say that the data has changed...
    #    print "Found %s publishes!" % self._sg_publishes_model.rowCount()
        




