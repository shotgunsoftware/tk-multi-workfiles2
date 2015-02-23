# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""

import sgtk
from sgtk.platform.qt import QtGui

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel

class MyTasksModel(ShotgunModel):
    """
    """
    _MAX_THUMB_WIDTH=512
    _MAX_THUMB_HEIGHT=512
    
    def __init__(self, filters, parent=None):
        """
        """
        ShotgunModel.__init__(self, parent=parent, download_thumbs=True)
        
        fields = ["image", "sg_status_list", "description", "entity", "content", "step"]
        self._load_data("Task", filters, ["id"], fields)
    
    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        self._refresh_data()      
    
    def _populate_default_thumbnail(self, item):
        """
        """
        pass
    
    def _populate_thumbnail(self, item, field, path):
        """
        """
        if field != "image":
            # there may be other thumbnails being loaded in as part of the data flow
            # (in particular, created_by.HumanUser.image) - these ones we just want to 
            # ignore and not display.
            return
    
        # set the item icon to be the thumbnail:
        item.setIcon(QtGui.QIcon(path))