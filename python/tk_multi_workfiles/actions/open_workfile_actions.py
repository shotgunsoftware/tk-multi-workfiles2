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
from sgtk import TankError

from .open_file_action import OpenFileAction, CopyAndOpenInCurrentWorkAreaAction

from ..environment_details import EnvironmentDetails
from ..file_item import FileItem
from ..file_finder import FileFinder

class OpenWorkfileAction(OpenFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        all_versions = [v for v, f in file_versions.iteritems()]
        max_version = max(all_versions) if all_versions else 0

        label = ""
        if file.version == max_version:
            label = "Open"
        else:
            label = "Open v%03d" % file.version
        if not file.editable:
            label = "%s (Read-only)" % label
            
        OpenFileAction.__init__(self, label, file, file_versions, environment)
        
    def execute(self, parent_ui):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not self.file or not self.file.is_local:
            return False

        return self._do_copy_and_open(src_path = None, 
                                      dst_path = self.file.path,
                                      version = self.file.version, 
                                      read_only = self.file.editable, 
                                      new_ctx = self.environment.context, 
                                      parent_ui = parent_ui)
        
class ContinueFromPreviousWorkFileAction(OpenFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        all_versions = [v for v, f in file_versions.iteritems()]
        max_version = max(all_versions) if all_versions else 0
        
        OpenFileAction.__init__(self, "Continue Working (as v%03d)" % (max_version+1), file, file_versions, environment)
        self._version = max_version+1
    
    def execute(self, parent_ui):
        """
        """
        if (not self.file.is_local
            or not self.environment.work_template):
            return False
        
        # source path is the file path:
        src_path = self.file.path
        
        # build dst path for the next version of this file:
        fields = self.environment.work_template.get_fields(src_path)
        fields["version"] = self._version
        dst_path = self.environment.work_template.apply_fields(fields)
        
        # TODO - add validation?
        
        return self._do_copy_and_open(src_path, dst_path, None, not self.file.editable, 
                                      self.environment.context, parent_ui)

class CopyAndOpenFileInCurrentWorkAreaAction(CopyAndOpenInCurrentWorkAreaAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        CopyAndOpenInCurrentWorkAreaAction.__init__(self, "Open in Current Work Area...", file, file_versions, environment)

    def execute(self, parent_ui):
        """
        """
        if (not self.file
            or not self.file.is_local
            or not self.environment.work_template):
            return False

        return self._open_in_current_work_area(self.file.path, self.environment.work_template, parent_ui)

