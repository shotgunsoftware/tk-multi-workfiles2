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
from sgtk.platform.qt import QtCore, QtGui

from .open_file_action import OpenFileAction

class OpenWorkfileAction(OpenFileAction):
    """
    """
    def __init__(self, read_only=False):
        """
        """
        if read_only:
            OpenFileAction.__init__(self, "open_workfile_readonly", "Open Work File (Read-only)")
        else:
            OpenFileAction.__init__(self, "open_workfile", "Open Work File")
        self._read_only = read_only
        
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file or not file.is_local or file.editable == self._read_only:
            return False

        return self._do_copy_and_open(None, file.path, None, not file.editable, environment.context, parent_ui)
    
