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
    
class ContinueFromPublishAction(OpenFileAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        """
        """
        all_versions = [v for v, f in file_versions.iteritems()]
        max_version = max(all_versions) if all_versions else 0
        
        OpenFileAction.__init__(self, "Continue Working From Publish (as v%03d)" % (max_version+1), file, file_versions, environment)
        self._version = max_version+1
    
    def execute(self, parent_ui):
        """
        """
        if (not self.file.is_published 
            or not self.environment.context
            or not self.environment.work_template
            or not self.environment.publish_template):
            return False
        
        # source path is the file publish path:
        src_path = self.file.publish_path
        
        # build dst path for the next version of this file:
        fields = self.environment.publish_template.get_fields(src_path)
        ctx_fields = self.environment.context.as_template_fields(self.environment.work_template)
        fields.update(ctx_fields)
        fields["version"] = self._version
        dst_path = self.environment.work_template.apply_fields(fields)
        
        # TODO - add validation?
        
        return self._do_copy_and_open(src_path, dst_path, None, not self.file.editable, 
                                      self.environment.context, parent_ui)
        
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

        return self._open_in_current_work_area(self.file.publish_path, self.environment.publish_template, parent_ui)
