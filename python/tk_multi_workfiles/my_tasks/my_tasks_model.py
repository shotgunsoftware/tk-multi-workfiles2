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
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

class MyTasksModel(ShotgunEntityModel):
    """
    """
    def __init__(self, filters, extra_display_fields, parent, bg_task_manager=None):
        """
        """
        self.extra_display_fields = extra_display_fields or []
        fields = ["image", "sg_status_list", "description", "entity", "content", "step", "project"]
        fields.extend(self.extra_display_fields)

        ShotgunEntityModel.__init__(self, "Task", filters, ["id"], fields, parent,
                                    download_thumbs=True, 
                                    bg_task_manager=bg_task_manager)

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
        #item.setIcon(QtGui.QIcon(path))