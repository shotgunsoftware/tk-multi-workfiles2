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
        self._version = version
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if (not file.is_local
            or not environment.work_template):
            return False
        
        # source path is the file path:
        src_path = file.path
        
        # build dst path for the next version of this file:
        fields = environment.work_template.get_fields(src_path)
        fields["version"] = self._version
        dst_path = environment.work_template.apply_fields(fields)
        
        # TODO - add validation?
        
        return self._do_copy_and_open(src_path, dst_path, None, not file.editable, 
                                      environment.context, parent_ui)
    
class CopyAndOpenFileInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def __init__(self):
        OpenFileAction.__init__(self, "Open in Current Work Area...")
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if (not file
            or not file.is_local):
            return False
        
        # gather information for this file in the current work area:
        
        
        raise NotImplementedError()
    
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
        """
        """
        if not file or not file.is_published:
            return False
        
        return self._do_copy_and_open(src_path = None, 
                                      dst_path = file.publish_path,
                                      version = file.version, 
                                      read_only = file.editable, 
                                      new_ctx = environment.context, 
                                      parent_ui = parent_ui)
    
class ContinueFromPublishAction(OpenFileAction):
    """
    """
    def __init__(self, version):
        OpenFileAction.__init__(self, "Continue Working From Publish (as v%03d)" % version)
        self._version = version
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if (not file.is_published 
            or not environment.context
            or not environment.work_template
            or not environment.publish_template):
            return False
        
        # source path is the file publish path:
        src_path = file.publish_path
        
        # build dst path for the next version of this file:
        fields = environment.publish_template.get_fields(src_path)
        ctx_fields = environment.context.as_template_fields(environment.work_template)
        fields.update(ctx_fields)
        fields["version"] = self._version
        dst_path = environment.work_template.apply_fields(fields)
        
        # TODO - add validation?
        
        return self._do_copy_and_open(src_path, dst_path, None, not file.editable, 
                                      environment.context, parent_ui)
    
class CopyAndOpenPublishInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def __init__(self):
        OpenFileAction.__init__(self, "Open Publish in Current Work Area...")
    
    def execute(self, file, file_versions, environment, parent_ui):
        raise NotImplementedError()    
    
    
    