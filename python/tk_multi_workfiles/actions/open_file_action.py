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
import os

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from sgtk import TankError

from .file_action import FileAction
from ..scene_operation import reset_current_scene, open_file, OPEN_FILE_ACTION
from ..work_area import WorkArea
from ..file_item import FileItem
from ..file_finder import FileFinder
from ..user_cache import g_user_cache

class OpenFileAction(FileAction):
    """
    """

    def _copy_file(self, source_path, target_path):
        """
        Use hook to copy a file from source to target path
        """
        self._app.log_debug("Copying file '%s' to '%s' via hook" % (source_path, target_path))
        self._app.execute_hook("hook_copy_file", 
                               source_path=source_path, 
                               target_path=target_path)

    def _do_copy_and_open(self, src_path, dst_path, version, read_only, new_ctx, parent_ui):
        """
        Copies src_path to dst_path, creates folders, restarts the engine and then opens 
        the file from dst_path
        
        :param src_path:    The path of the file to copy
        :param dst_path:    The destination file path to open
        :param version:     The version of the work file to be opened
        :param read_only:   True if the work file should be opened read-only
        :param new_ctx:     The context that the work file should be opened in
        :returns:           True of the source file is copied and successfully opened
        """
        if not dst_path or not new_ctx:
            # can't do anything!
            return False
           
        if src_path and src_path != dst_path:
            # check that the source path exists:        
            if not os.path.exists(src_path):
                QtGui.QMessageBox.critical(parent_ui, "File doesn't exist!", 
                                           "The file\n\n%s\n\nCould not be found to open!" % src_path)
                return False
            
        if new_ctx != self._app.context:
            # ensure folders exist.  This serves the
            # dual purpose of populating the path
            # cache and ensuring we can copy the file
            # if we need to
            try:
                FileAction.create_folders(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to create folders!", 
                                           "Failed to create folders:\n\n%s!" % e)
                self._app.log_exception("Failed to create folders")
                return False
        
        # reset the current scene:
        try:
            if not reset_current_scene(self._app, OPEN_FILE_ACTION, new_ctx):
                self._app.log_debug("Failed to reset the current scene!")
                return False
        except Exception, e:
            QtGui.QMessageBox.critical(parent_ui, "Failed to reset the scene", 
                                       "Failed to reset the scene:\n\n%s\n\nUnable to continue!" % e)
            self._app.log_exception("Failed to reset the scene!")
            return False
    
        # if need to, copy the file
        if src_path and src_path != dst_path:
            # check that local path doesn't already exist:
            if os.path.exists(dst_path):
                #TODO: replace with Toolkit dialog
                answer = QtGui.QMessageBox.question(parent_ui, "Overwrite file?",
                                "The file\n\n%s\n\nalready exists.  Would you like to overwrite it?" % (dst_path), 
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return False
                
            try:
                # make sure that the folder exists - this will handle any leaf folders that aren't
                # created by Toolkit (e.g. a dynamic static folder that isn't part of the schema)
                dst_dir = os.path.dirname(dst_path)
                self._app.ensure_folder_exists(dst_dir)
                # copy file:
                self._copy_file(src_path, dst_path)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Copy file failed!", 
                                           "Copy of file failed!\n\n%s!" % e)
                self._app.log_exception("Copy file failed")
                return False            
                    
        # switch context:
        previous_context = self._app.context
        if not new_ctx == self._app.context:
            try:
                # Change the curent context.
                FileAction.change_context(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to change the work area", 
                            "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" % (new_ctx, e))
                self._app.log_exception("Failed to change the work area to %s!" % new_ctx)
                return False

        # open file
        try:
            is_file_opened = open_file(self._app, OPEN_FILE_ACTION, new_ctx, dst_path, version, read_only)
        except Exception, e:
            QtGui.QMessageBox.critical(parent_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (dst_path, e))
            self._app.log_exception("Failed to open file %s!" % dst_path)
            FileAction.restore_context(parent_ui, previous_context)
            return False
        # Test specifically for False. Legacy open hooks return None, which means success.
        if is_file_opened is False:
            FileAction.restore_context(parent_ui, previous_context)
            return False

        try:
            self._app.log_metric("Opened Workfile")
        except:
            # ignore all errors. ex: using a core that doesn't support metrics
            pass

        return True


class CopyAndOpenInCurrentWorkAreaAction(OpenFileAction):
    """
    """
    def _open_in_current_work_area(self, src_path, src_template, file, src_work_area, parent_ui):
        """
        """
        # get info about the current work area:
        app = sgtk.platform.current_bundle()
        # no need to try/except this WorkArea object creation, since if we're here it means the
        # context is fully configured.
        dst_work_area = WorkArea(app.context)
        if not dst_work_area.work_template:
            # should never happen!
            app.log_error("Unable to copy the file '%s' to the current work area as no valid "
                          "work template could be found" % src_path)
            return False

        # determine the set of fields for the destination file in the current work area:
        #
        # get fields from file path using the source work template:
        fields = src_template.get_fields(src_path)

        # get the template fields for the current context using the current work template: 
        context_fields = dst_work_area.context.as_template_fields(dst_work_area.work_template)

        # this will overide any context fields obtained from the source path:
        fields.update(context_fields)

        # get the sandbox user name if there is one:
        sandbox_user_name = None
        if (src_work_area and src_work_area.contains_user_sandboxes
            and src_work_area.context and src_work_area.context.user and g_user_cache.current_user
            and src_work_area.context.user["id"] != g_user_cache.current_user["id"]):
            sandbox_user_name = src_work_area.context.user.get("name", "Unknown")

        src_version = None
        dst_version = None
        if "version" in dst_work_area.work_template.keys:
            # need to figure out the next version:
            src_version = fields["version"]

            # build a file key from the fields: 
            file_key = FileItem.build_file_key(fields, 
                                               dst_work_area.work_template, 
                                               dst_work_area.version_compare_ignore_fields)
    
            # look for all files that match this key:
            finder = FileFinder()
            found_files = finder.find_files(dst_work_area.work_template, 
                                            dst_work_area.publish_template, 
                                            dst_work_area.context, 
                                            file_key)

            # get the max version:
            versions = [file.version for file in found_files]
            dst_version = (max(versions or [0]) + 1)

            fields["version"] = dst_version

        # confirm we should copy and open the file:
        msg = "'%s" % file.name
        if src_version:
            msg += ", v%03d" % src_version
        msg += "'"
        if sandbox_user_name is not None:
            msg += " is in %s's Work Area (%s)." % (sandbox_user_name, src_work_area.context)
        else:
            msg += " is in a different Work Area (%s)." % (src_work_area.context)
        msg += ("\n\nWould you like to copy the file to your current Work Area (%s)" % (dst_work_area.context))
        if dst_version:
            msg += " as version v%03d" % dst_version
        msg += " and open it from there?" 

        answer = QtGui.QMessageBox.question(parent_ui, "Open file in current Work Area?", msg,
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        if answer != QtGui.QMessageBox.Yes:
            return False

        # build the destination path from the fields:
        dst_file_path = ""
        try:
            dst_file_path = dst_work_area.work_template.apply_fields(fields)
        except TankError, e:
            app.log_error("Unable to copy the file '%s' to the current work area as Toolkit is "
                          "unable to build the destination file path: %s" % (src_path, e))
            return False

        # copy and open the file:
        return self._do_copy_and_open(src_path, 
                                      dst_file_path, 
                                      version = None, 
                                      read_only = False, 
                                      new_ctx = dst_work_area.context, 
                                      parent_ui = parent_ui)

class ContinueFromFileAction(OpenFileAction):
    """
    """
    def __init__(self, label, file, file_versions, environment):
        """
        """
        # Q. should the next version include the current version?
        all_versions = [v for v, f in file_versions.iteritems()] + [file.version]
        max_version = max(all_versions)
        self._version = max_version+1
        label = "%s (as v%03d)" % (label, self._version) 
        OpenFileAction.__init__(self, label, file, file_versions, environment)
    
    def _continue_from(self, src_path, src_template, parent_ui):
        """
        """
        # get the destination work area for the current user:
        dst_work_area = self.environment.create_copy_for_user(g_user_cache.current_user)
        app = sgtk.platform.current_bundle()
        if not dst_work_area.work_template:
            # should never happen!
            app.log_error("Unable to copy the file '%s' to the current work area as no valid "
                          "work template could be found" % src_path)
            return False

        # build dst path for the next version of this file:
        fields = src_template.get_fields(src_path)

        # get the template fields for the current context using the current work template: 
        context_fields = dst_work_area.context.as_template_fields(dst_work_area.work_template)

        # this will overide any context fields obtained from the source path:
        fields.update(context_fields)

        # update version:
        fields["version"] = self._version

        # build the destination path:
        dst_path = dst_work_area.work_template.apply_fields(fields)

        # copy and open the file:
        return self._do_copy_and_open(src_path, dst_path, None, not self.file.editable, 
                                      dst_work_area.context, parent_ui)
