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

from .open_file_action import OpenFileAction, CopyAndOpenInCurrentWorkAreaAction, ContinueFromFileAction

from ..user_cache import g_user_cache

class OpenWorkfileAction(OpenFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        all_versions = [v for v, f in file_versions.iteritems()]
        max_version = max(all_versions) if all_versions else 0

        sandbox_user = None
        if (environment and environment.contains_user_sandboxes
            and environment.context and environment.context.user and g_user_cache.current_user
            and environment.context.user["id"] != g_user_cache.current_user["id"]):
            sandbox_user = environment.context.user.get("name", "Unknown").split(" ")[0]

        label = ""
        if file.version == max_version:
            label = "Open"
        else:
            label = "Open v%03d" % file.version
        if not file.editable:
            label = "%s (Read-only)" % label
        if sandbox_user is not None:
            label = "%s from %s's Sandbox" % (label, sandbox_user)
            
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

class ContinueFromWorkFileAction(ContinueFromFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        label = ""
        if (environment and environment.contains_user_sandboxes
            and environment.context and environment.context.user and g_user_cache.current_user
            and environment.context.user["id"] != g_user_cache.current_user["id"]):
            sandbox_user = environment.context.user.get("name", "Unknown").split(" ")[0]
            label = "Continue Working from %s's File" % sandbox_user
        else:
            label = "Continue Working"

        ContinueFromFileAction.__init__(self, label, file, file_versions, environment)

    def execute(self, parent_ui):
        """
        """
        if (not self.file.is_local
            or not self.environment.work_template):
            return False

        # source path is the file path:
        src_path = self.file.path

        return self._continue_from(src_path, self.environment.work_template, parent_ui)

class CopyAndOpenFileInCurrentWorkAreaAction(CopyAndOpenInCurrentWorkAreaAction):
    """
    Action that copies a file to the current work area as the next available version
    and opens it from there
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

        return self._open_in_current_work_area(self.file.path, self.environment.work_template, 
                                               self.file, self.environment, parent_ui)

