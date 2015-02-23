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

class FileAction(object):
    def __init__(self, label):
        """
        """
        self._app = sgtk.platform.current_bundle()
        self._label = label
        
    @property
    def label(self):
        return self._label
    
    def execute(self, file, file_versions, environment, parent_ui):
        raise NotImplementedError()

class SeparatorFileAction(FileAction):
    def __init__(self):
        FileAction.__init__(self, "---")
        
    def execute(self, file, file_versions, environment, parent_ui):
        # do nothing!
        pass
