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

from ..wrapper_dialog import WrapperDialog
from ..open_options_form import OpenOptionsForm
from ..user_cache import g_user_cache

class InteractiveOpenAction(OpenFileAction):

    def __init__(self, file, file_versions, environment, workfiles_visible, publishes_visible):
        """
        """
        OpenFileAction.__init__(self, "Open", file, file_versions, environment)
        
        self._workfiles_visible = workfiles_visible
        self._publishes_visible = publishes_visible

    def execute(self, parent_ui):
        """
        """
        if not self.file:
            return False
        
        # this is the smart action where all the logic tries to decide what the actual 
        # action should be!
        #print "Opening file '%s' which is in user sandbox '%s'" % (self.file.path, self.environment.context.user["name"])

        # get information about the max local & publish versions:
        local_versions = [v for v, f in self.file_versions.iteritems() if f.is_local]
        publish_versions = [v for v, f in self.file_versions.iteritems() if f.is_published]
        max_local_version = max(local_versions) if local_versions else None
        max_publish_version = max(publish_versions) if publish_versions else None
        max_version = max(0,max_local_version, max_publish_version)

        if (self._publishes_visible and self.file.is_published
            and (not self._workfiles_visible or not self.file.is_local)):
            # opening a publish and either not showing work files or the file isn't local
            if self.file.version < max_publish_version:
                # opening an old version of a publish!
                return self._open_previous_publish(self.file, self.environment, parent_ui)
            else:
                # opening the most recent version of a publish!
                latest_work_file = None
                if max_local_version != None:
                    latest_work_file = self.file_versions[max_local_version]
                return self._open_publish_with_check(self.file, latest_work_file, self.environment, max_version+1, parent_ui)        

        elif (self._workfiles_visible and self.file.is_local):
            # opening a workfile and either not showing publishes or the file hasn't been published
            # OR
            # opening a file that is both local and published and both are visible in the view!
            # (is this the right thing to do when a file is both local and a publish??)
            if self.file.version < max_local_version:
                # opening an old version of work file:
                return self._open_previous_workfile(self.file, self.environment, parent_ui)
            else:
                # opening the most recent version of a work file!
                latest_publish = None
                if max_publish_version != None:
                    latest_publish = self.file_versions[max_publish_version]
                return self._open_workfile_with_check(self.file, latest_publish, self.environment, max_version+1, parent_ui)
        else:
            # this shouldn't happen and is in here primarily for debug purposes!
            raise NotImplementedError("Unsure what action to take when opening this file!")

        # didn't do anything!        
        return False
        
    def _open_workfile_with_check(self, work_file, publish_file, env, next_version, parent_ui):
        """
        Function called when user clicks Open for a file
        in the Work Area
        """

        # different options depending if the publish file is more 
        # recent or not:
        open_mode = OpenOptionsForm.OPEN_WORKFILE
        if publish_file and work_file.compare_with_publish(publish_file) < 0:
            # options are different if the publish and work files are the same path as there
            # doesn't need to be the option of opening the publish read-only.
            publish_requires_copy = True
            
            if env.publish_template == env.work_template:
                if "version" not in env.publish_template.keys:
                    publish_requires_copy = False
            
            form = OpenOptionsForm(None, self._app, work_file, publish_file, OpenOptionsForm.OPEN_WORKFILE_MODE, 
                                   next_version, publish_requires_copy)
            open_mode = WrapperDialog.show_modal(form, parent_ui, "Found a More Recent Publish!")
            
        if open_mode == OpenOptionsForm.OPEN_WORKFILE:
            # open the work file:
            if not self._open_workfile(work_file, env, parent_ui):
                return False
        elif open_mode == OpenOptionsForm.OPEN_PUBLISH:
            # open the published file instead:
            if not self._open_publish_as_workfile(publish_file, env, next_version, parent_ui):
                return False
        else:
            # cancelled so stop!
            return False
        
        return True

    def _open_previous_workfile(self, file, env, parent_ui):
        """
        Open a previous version of a work file - this just opens
        it directly without any file copying or validation
        """
        # Confirm how the previous work file should be opened:
        # (TODO) expand this out to allow opening directly or option to continue 
        # working as the next work file
        answer = QtGui.QMessageBox.question(parent_ui, "Open Previous Work File?",
                                            ("Continue opening the old work file\n\n    %s (v%d)\n\n"
                                             "from the work area?" % (file.name, file.version)), 
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if answer != QtGui.QMessageBox.Yes:
            return False
        
        return self._do_copy_and_open(None, file.path, file.version, False, env.context, parent_ui)
        
        
    def _open_publish_with_check(self, publish_file, work_file, env, next_version, parent_ui):
        """
        Function called when user clicks Open for a file
        in the Publish Area
        """
        # options are different if the publish and work files are the same path as there
        # doesn't need to be the option of opening the publish read-only.
        publish_requires_copy = True
        if env.publish_template == env.work_template:
            if "version" not in env.publish_template.keys:
                publish_requires_copy = False
        
        # different options depending if the work file is more 
        # recent or not:
        dlg_title = ""
        if work_file and work_file.compare_with_publish(publish_file) > 0:
            dlg_title = "Found a More Recent Work File!"
        else:
            dlg_title = "Open Publish"    
            work_file = None
            
        if work_file or publish_requires_copy:
            # show dialog with options to user:
            open_mode = OpenOptionsForm.OPEN_PUBLISH
            
            mode = OpenOptionsForm.OPEN_PUBLISH_MODE if publish_requires_copy else OpenOptionsForm.OPEN_PUBLISH_NO_READONLY_MODE 
            form = OpenOptionsForm(None, self._app, work_file, publish_file, mode, next_version, publish_requires_copy)
            open_mode = WrapperDialog.show_modal(form, parent_ui, dlg_title)
                
            if open_mode == OpenOptionsForm.OPEN_WORKFILE:
                # open the work file:
                return self._open_workfile(work_file, env, parent_ui)
            elif open_mode == OpenOptionsForm.OPEN_PUBLISH:
                # open the published file instead:
                return self._open_publish_as_workfile(publish_file, env, next_version, parent_ui)
            elif open_mode == OpenOptionsForm.OPEN_PUBLISH_READONLY:
                # open the published file read-only instead:
                return self._open_publish_read_only(publish_file, env, parent_ui)
            else:
                return False
        else:
            # just open the published file:
            return self._open_publish_as_workfile(publish_file, env, next_version, parent_ui)

    def _open_workfile(self, file, env, parent_ui):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file.editable:
            answer = QtGui.QMessageBox.question(parent_ui, "Open file read-only?",
                                                ("The work file you are opening: '%s', is "
                                                "read-only:\n\n%s.\n\nWould you like to continue?" 
                                                % (file.name, file.not_editable_reason)), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
                return False
        
        # trying to open a work file...
        src_path = None
        work_path = file.path
        
        # construct a context for this path to determine if it's in
        # a user sandbox or not:
        if env.context.user:
            current_user = g_user_cache.current_user
            if current_user and current_user["id"] != env.context.user["id"]:

                # file is in a user sandbox - construct path
                # for the current user's sandbox:
                try:
                    # get fields from work path:
                    fields = env.work_template.get_fields(work_path)

                    # add in the fields from the context with the current user:
                    local_ctx = env.context.create_copy_for_user(current_user)
                    ctx_fields = local_ctx.as_template_fields(env.work_template)
                    fields.update(ctx_fields)

                    # construct the local path from these fields:
                    local_path = env.work_template.apply_fields(fields)
                except Exception, e:
                    QtGui.QMessageBox.critical(parent_ui, "Failed to resolve file path", 
                                           ("Failed to resolve the user sandbox file path:\n\n%s\n\nto the local "
                                           "path:\n\n%s\n\nUnable to open file!" % (work_path, e)))
                    self._app.log_exception("Failed to resolve user sandbox file path %s" % work_path)
                    return False

                if local_path != work_path:
                    # more than just an open so prompt user to confirm:
                    answer = QtGui.QMessageBox.question(parent_ui, "Open file from another user?",
                                                        ("The work file you are opening:\n\n%s\n\n"
                                                        "is in a user sandbox belonging to %s.  Would "
                                                        "you like to copy the file to your sandbox and open it?" 
                                                        % (work_path, env.context.user["name"])), 
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                    if answer == QtGui.QMessageBox.Cancel:
                        return False

                    src_path = work_path
                    work_path = local_path

        return self._do_copy_and_open(src_path, work_path, None, not file.editable, env.context, parent_ui)

    def _open_previous_publish(self, file, env, parent_ui):
        """
        Open a previous version of a publish file from the publish area
        """
        # confirm how the previous published file should be opened:
        # (TODO) expand this out to allow opening directly or option to continue 
        # working as the next work file
        answer = QtGui.QMessageBox.question(parent_ui, "Open Previous Publish?",
                                            ("Continue opening the old published file\n\n    %s (v%d)\n\n"
                                             "from the publish area?" % (file.name, file.version)), 
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if answer != QtGui.QMessageBox.Yes:
            return False        
        
        return self._do_copy_and_open(src_path = None, 
                                      dst_path = file.publish_path, 
                                      version = file.version, 
                                      read_only = True, 
                                      new_ctx = env.context, 
                                      parent_ui = parent_ui)
        
    def _open_publish_read_only(self, file, env, parent_ui):
        """
        Open a previous version of a publish file from the publish 
        area - this just opens it directly without any file copying 
        or validation
        """
        return self._do_copy_and_open(src_path = None, 
                                      dst_path = file.publish_path, 
                                      version = file.version,
                                      read_only = True, 
                                      new_ctx = env.context, 
                                      parent_ui = parent_ui)
        
    def _open_publish_as_workfile(self, file, env, new_version, parent_ui):
        """
        Open the published file - this will construct a new work path from the 
        work template and the publish fields before copying it and opening it 
        as a new work file
        """
        if not file or not file.is_published:
            return False

        if not file.editable:
            answer = QtGui.QMessageBox.question(parent_ui, "Open file read-only?",
                                                ("The published file you are opening: '%s', is "
                                                "read-only:\n\n%s.\n\nWould you like to continue?" 
                                                % (file.name, file.not_editable_reason)), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
                return False

        # trying to open a publish:
        work_path = None
        src_path = file.publish_path
        
        # early check to see if the publish path & work path will actually be different:
        if env.publish_template == env.work_template and "version" not in env.publish_template.keys:
            # assume that the work and publish paths will actally be the same!
            work_path = src_path
        else:
            # get the work path for the publish:
            try:
                # get fields for the path:                
                fields = env.publish_template.get_fields(src_path)
    
                # construct a context for the path:
                sp_ctx = self._app.sgtk.context_from_path(src_path, env.context)
    
                # if current user is defined, update fields to use this:
                current_user = g_user_cache.current_user
                if current_user and sp_ctx.user and sp_ctx.user["id"] != current_user["id"]:
                    sp_ctx = sp_ctx.create_copy_for_user(current_user)
                    
                # finally, use context to populate additional fields:
                ctx_fields = sp_ctx.as_template_fields(env.work_template)
                fields.update(ctx_fields)
            
                # add next version to fields:                
                fields["version"] = new_version
                
                # construct work path:
                work_path = env.work_template.apply_fields(fields)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to get work file path", 
                                       ("Failed to resolve work file path from publish path:\n\n%s\n\n%s\n\n"
                                       "Unable to open file!" % (src_path, e)))
                self._app.log_exception("Failed to resolve work file path from publish path: %s" % src_path)
                return False

        return self._do_copy_and_open(src_path, work_path, None, not file.editable, env.context, parent_ui)

        
        
        
        
        
        
        
        