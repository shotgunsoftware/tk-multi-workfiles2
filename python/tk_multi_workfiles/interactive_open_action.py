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

from .wrapper_dialog import WrapperDialog

class InteractiveOpenAction(OpenFileAction):

    def __init__(self):
        """
        """
        OpenFileAction.__init__(self, "open", "Open")


    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if not file:
            return
        
        # this is the smart action where all the logic goes
        # to decide what the actual action should be!
        print "Executing action: %s for file %s" % (self.name, file)

        # get information about the max local & publish versions:
        local_versions = [v for v, f in file_versions.iteritems() if f.is_local]
        publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
        max_local_version = max(local_versions) if local_versions else None
        max_publish_version = max(publish_versions) if publish_versions else None
        max_version = max(max_local_version, max_publish_version)
        
        if file.is_local:
            if file.version < max_local_version:
                # TODO - what if this is also a publish and the publish _is_ the most recent?
                # should it offer to open the work file or the publish?  Should it offer to
                # continue working from either??
                #
                # The default behaviour may depend on what's visible in the UI, e.g.:
                # - publishes !work files == default open the publish
                # - work files !publishes == default open the work file
                # - work files & publishes == ???
                return self._open_previous_workfile(file, environment, parent_ui)
            else:
                # opening the most recent version of a work file!
                latest_publish = None
                if max_publish_version != None:
                    latest_publish = file_versions[max_publish_version]
                return self._open_workfile_with_check(file, latest_publish, environment, max_version+1, parent_ui)
                
        elif file.is_published:
            if file.version < max_publish_version:
                # opening an old version of a publish!
                return self._open_publish_read_only(file, environment, False, parent_ui)
            else:
                # opening the most recent version of a publish!
                latest_work_file = None
                if max_work_version != None:
                    latest_work_file = file_versions[max_work_version]
                self._open_publish_with_check(file, latest_work_file, environment, max_version+1, parent_ui)            
        
    def _open_workfile_with_check(self, work_file, publish_file, env, next_version, parent_ui):
        """
        Function called when user clicks Open for a file
        in the Work Area
        """

        # different options depending if the publish file is more 
        # recent or not:
        from .open_file_form import OpenFileForm        
        open_mode = OpenFileForm.OPEN_WORKFILE
        if publish_file and work_file.compare_with_publish(publish_file) < 0:
            # options are different if the publish and work files are the same path as there
            # doesn't need to be the option of opening the publish read-only.
            publish_requires_copy = True
            
            if env.publish_template == env.work_template:
                if "version" not in env.publish_template.keys:
                    publish_requires_copy = False
            
            form = OpenFileForm(self._app, work_file, publish_file, OpenFileForm.OPEN_WORKFILE_MODE, 
                                next_version, publish_requires_copy)
            open_mode = WrapperDialog.show_modal(form, "Found a More Recent Publish!", parent=parent_ui)
            
        if open_mode == OpenFileForm.OPEN_WORKFILE:
            # open the work file:
            if not self._open_workfile(work_file, env, parent_ui):
                return False
        elif open_mode == OpenFileForm.OPEN_PUBLISH:
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
        # opening an old version of a work file - this currently does the previous behaviour
        # of just opening the file with no copying...  Should it also prompt to ask the user
        # if they want to continue working from this file (copy and continue)?
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
            from .open_file_form import OpenFileForm
            open_mode = OpenFileForm.OPEN_PUBLISH
            
            mode = OpenFileForm.OPEN_PUBLISH_MODE if publish_requires_copy else OpenFileForm.OPEN_PUBLISH_NO_READONLY_MODE 
            form = OpenFileForm(self._app, work_file, publish_file, mode, next_version, publish_requires_copy)
            open_mode = WrapperDialog.show_modal(form, dlg_title, parent=parent_ui)
                
            if open_mode == OpenFileForm.OPEN_WORKFILE:
                # open the work file:
                return self._open_workfile(work_file, env, parent_ui)
            elif open_mode == OpenFileForm.OPEN_PUBLISH:
                # open the published file instead:
                return self._open_publish_as_workfile(publish_file, env, next_version, parent_ui)
            elif open_mode == OpenFileForm.OPEN_PUBLISH_READONLY:
                # open the published file read-only instead:
                self._open_publish_read_only(publish_file, env, True, parent_ui)
            else:
                return False
        elif not work_file:
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
            current_user = sgtk.util.get_current_user(self._app.sgtk)
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
        
    def _open_publish_read_only(self, file, env, is_latest, parent_ui):
        """
        Open a previous version of a publish file from the publish 
        area - this just opens it directly without any file copying 
        or validation
        """
        return self._do_copy_and_open(None, file.publish_path, file.version if is_latest else None, 
                                      True, env.context, parent_ui)
        
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
                current_user = sgtk.util.get_current_user(self._app.sgtk)
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
        
        
        
        
        
        
        
        
        
        