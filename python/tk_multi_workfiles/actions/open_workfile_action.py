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
    def __init__(self, is_latest, version, read_only):
        """
        """
        label = ""
        if is_latest:
            label = "Open"
        else:
            label = "Open v%03d" % version
        if read_only:
            label = "%s (Read-only)" % label
            
        OpenFileAction.__init__(self, label)
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file or not file.is_local:
            return False

        return self._do_copy_and_open(src_path = None, 
                                      dst_path = file.path,
                                      version = file.version, 
                                      read_only = file.editable, 
                                      new_ctx = environment.context, 
                                      parent_ui = parent_ui)
        
class ContinueFromPreviousWorkFileAction(OpenFileAction):
    """
    """
    def __init__(self, version):
        OpenFileAction.__init__(self, "Continue Working (as v%03d)" % version)
    
    def execute(self, file, file_versions, environment, parent_ui):
        pass
    
class CopyAndOpenFileInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def __init__(self):
        OpenFileAction.__init__(self, "Open in Current Work Area...")
    
    def execute(self, file, file_versions, environment, parent_ui):
        pass
    
class OpenPublishAction(OpenFileAction):
    """
    """
    def __init__(self, is_latest, version):
        label = ""
        if is_latest:
            label = "Open from the Publish Area"
        else:
            label = "Open v%03d from the Publish Area" % version
        
        OpenFileAction.__init__(self, label)
    
    def execute(self, file, file_versions, environment, parent_ui):
        pass

    
class ContinueFromPublishAction(OpenFileAction):
    """
    """
    def __init__(self, version):
        OpenFileAction.__init__(self, "Continue Working From Publish (as v%03d)" % version)
    
    def execute(self, file, file_versions, environment, parent_ui):
        pass
    
class CopyAndOpenPublishInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def __init__(self):
        OpenFileAction.__init__(self, "Open Publish in Current Work Area...")
    
    def execute(self, file, file_versions, environment, parent_ui):
        pass    
    
    
    