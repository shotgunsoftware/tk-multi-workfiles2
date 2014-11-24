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
from .util import get_templates_for_context

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel

class ShotgunPublishedFilesModel(ShotgunModel):
        
    def __init__(self, parent=None):
        """
        """
        ShotgunModel.__init__(self, parent)
        # (AD) TODO - get type from core
        self._published_file_type = "PublishedFile"
        
    def load_data(self, filters=None, fields=None):
        """
        """
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = [fields[0]]
        ShotgunModel._load_data(self, self._published_file_type, filters, hierarchy, fields)
        self._refresh_data()

class FileItem(QtGui.QStandardItem):
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
    
    def __init__(self, parent=None):
        """
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        
        self._sg_publishes_model = ShotgunPublishedFilesModel(self)
        self._sg_publishes_model.data_refreshed.connect(self._on_publishes_model_data_refreshed)
        
        #self._publishes_refreshed = False
        #self._work_files_refreshed = False
        
        
    def find_files(self, publish_filters, context):
        """
        """
        # clear current file list:
        self.clear()
        
        app = sgtk.platform.current_bundle()
        try:
            templates = get_templates_for_context(context, ["template_work", "template_publish"])
            work_template = templates.get("template_work")
            publish_template = templates.get("template_publish")
        except TankError, e:
            # had problems getting the work file settings for the specified context!
            app.log_debug("Failed to retrieve configuration: %s" % e)
            return

        finder = FileFinder(sgtk.platform.current_bundle())
        files = finder.find_files(work_template, publish_template, context)
        print "Found %d files!" % len(files)
        
        # and add them to the model:
        # ...
        for file in files:
            file_item = FileItem(file)
            self.appendRow(file_item)
        
        # clear the current model contents:
        
        # trigger async updates of publishes...
        #self._sg_publishes_model.load_data(publish_filters)
        
        # ...and work files
        
        
        
        # update the model:
        
    def _on_publishes_model_data_refreshed(self, data_changed):
        """
        """
        if not data_changed:
            return
        
        # update this model to say that the data has changed...
        print "Found %s publishes!" % self._sg_publishes_model.rowCount()
        




