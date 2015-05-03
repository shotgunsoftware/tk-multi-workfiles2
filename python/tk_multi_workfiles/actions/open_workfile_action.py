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

from ..environment_details import EnvironmentDetails
from ..file_item import FileItem
from ..find_files import FileFinder

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


class CopyAndOpenInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def _open_in_current_work_area(self, src_path, src_template, parent_ui):
        """
        """
        # get info about the current work area:
        app = sgtk.platform.current_bundle()
        dst_env = EnvironmentDetails(app.context)
        if not dst_env.work_template:
            # should never happen!
            app.log_error("Unable to copy the file '%s' to the current work area as no valid "
                          "work template could be found" % src_path)
            return False

        # determine the set of fields for the destination file in the current work area:
        #
        # get fields from file path using the source work template:
        fields = src_template.get_fields(src_path)

        # get the template fields for the current context using the current work template: 
        context_fields = dst_env.context.as_template_fields(dst_env.work_template)

        # this will overide any context fields obtained from the source path:
        fields.update(context_fields)

        # build the destination path from these fields:
        dst_file_path = ""
        try:
            dst_file_path = dst_env.work_template.apply_fields(fields)
        except TankError, e:
            app.log_error("Unable to copy the file '%s' to the current work area as Toolkit is "
                          "unable to build the destination file path: %s" % (src_path, e))
            return False

        if "version" in dst_env.work_template.keys:
            # need to figure out the next version:

            # build a file key from the fields: 
            file_key = FileItem.build_file_key(fields, 
                                               dst_env.work_template, 
                                               dst_env.version_compare_ignore_fields)
    
            # look for all files that match this key:
            finder = FileFinder()
            found_files = finder.find_files(dst_env.work_template, 
                                            dst_env.publish_template, 
                                            dst_env.context, 
                                            file_key)

            # get the max version:
            versions = [file.version for file in found_files]
            fields["version"] = (max(versions or [0]) + 1)

            # and rebuild the path:
            dst_file_path = dst_env.work_template.apply_fields(fields)

        # Should there be a prompt here?

        # copy and open the file:
        return self._do_copy_and_open(src_path, 
                                      dst_file_path, 
                                      version = None, 
                                      read_only = False, 
                                      new_ctx = dst_env.context, 
                                      parent_ui = parent_ui)


class CopyAndOpenFileInCurrentWorkAreaAction(CopyAndOpenInCurrentWorkAreaAction):
    """
    """
    def __init__(self):
        CopyAndOpenInCurrentWorkAreaAction.__init__(self, "Open in Current Work Area...")

    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if (not file
            or not file.is_local
            or not environment.work_template):
            return False

        return self._open_in_current_work_area(file.path, environment.work_template, parent_ui)


    
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
    
class CopyAndOpenPublishInCurrentWorkAreaAction(CopyAndOpenInCurrentWorkAreaAction):
    """
    """
    def __init__(self):
        CopyAndOpenInCurrentWorkAreaAction.__init__(self, "Open Publish in Current Work Area...")

    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if (not file
            or not file.is_published
            or not environment.publish_template):
            return False

        return self._open_in_current_work_area(file.publish_path, environment.publish_template, parent_ui)
    
    