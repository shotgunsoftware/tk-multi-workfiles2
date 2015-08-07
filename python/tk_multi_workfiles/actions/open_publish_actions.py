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

class OpenPublishAction(OpenFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        all_versions = [v for v, f in file_versions.iteritems()]
        max_version = max(all_versions) if all_versions else 0
        
        label = ""
        if file.version == max_version:
            label = "Open from the Publish Area"
        else:
            label = "Open v%03d from the Publish Area" % file.version
        
        OpenFileAction.__init__(self, label, file, file_versions, environment)
    
    def execute(self, parent_ui):
        """
        """
        if not self.file or not self.file.is_published:
            return False
        
        return self._do_copy_and_open(src_path = None, 
                                      dst_path = self.file.publish_path,
                                      version = self.file.version, 
                                      read_only = self.file.editable, 
                                      new_ctx = self.environment.context, 
                                      parent_ui = parent_ui)
    
class ContinueFromPublishAction(ContinueFromFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        ContinueFromFileAction.__init__(self, "Continue Working From Publish", file, file_versions, environment)

    def execute(self, parent_ui):
        """
        """
        if (not self.file.is_published 
            or not self.environment.publish_template):
            return False

        # source path is the file publish path:
        src_path = self.file.publish_path

        return self._continue_from(src_path, self.environment.publish_template, parent_ui)

class CopyAndOpenPublishInCurrentWorkAreaAction(CopyAndOpenInCurrentWorkAreaAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        CopyAndOpenInCurrentWorkAreaAction.__init__(self, "Open Publish in Current Work Area...", file, file_versions, environment)

    def execute(self, parent_ui):
        """
        """
        if (not self.file
            or not self.file.is_published
            or not self.environment.publish_template):
            return False

        return self._open_in_current_work_area(self.file.publish_path, self.environment.publish_template, 
                                               self.file, self.environment, parent_ui)
