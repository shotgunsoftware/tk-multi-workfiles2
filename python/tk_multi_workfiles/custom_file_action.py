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

from .file_action import FileAction

class CustomFileAction(FileAction):
    def __init__(self, name, label):
        """
        """
        FileAction.__init__(self, label)
        self._name = name
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        # execute hook to perform the action
        # TODO
        pass