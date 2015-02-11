# Copyright (c) 2013 Shotgun Software Inc.
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
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel

class SgPublishedFilesModel(ShotgunModel):
        
    def __init__(self, id, parent=None):
        """
        """
        ShotgunModel.__init__(self, parent, download_thumbs=False, asynchronous=False)
        # (AD) TODO - get type from core
        self._published_file_type = "PublishedFile"
        
        self._id = id
        
    @property
    def id(self):
        return self._id
        
    def load_data(self, filters=None, fields=None):
        """
        """
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = [fields[0]]
        return self._load_data(self._published_file_type, filters, hierarchy, fields)
        
    def refresh(self):
        """
        """
        self._refresh_data()
        
    def get_sg_data(self):
        sg_data = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            sg_data.append(item.get_sg_data())
        return sg_data