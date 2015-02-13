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
        
        """
        def _on_open_publish(self, publish_file, work_file):
        def _on_open_workfile(self, work_file, publish_file):
        def _on_open_previous_publish(self, file):
        def _on_open_previous_workfile(self, file):
        def _on_new_file(self):
        """
        
        if file.is_local:
            if file.version < max_local_version:
                # opening an old version of a work file!
                pass
                #def _on_open_previous_workfile(self, file):
            else:
                # opening the most recent version of a work file!
                latest_publish = None
                if max_publish_version != None:
                    latest_publish = file_versions[max_publish_version]
                return self._on_open_workfile(file, latest_publish, environment, max_version+1, parent_ui)
                
        elif file.is_published:
            if file.version < max_publish_version:
                # opening an old version of a publish!
                pass
                #def _on_open_previous_publish(self, file):
            else:
                # opening the most recent version of a publish!
                pass
                #def _on_open_publish(self, publish_file, work_file):
        
        
    def _on_open_workfile(self, work_file, publish_file, env, next_version, parent_ui):
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
            if not self._do_open_workfile(work_file, env, parent_ui):
                return False
        elif open_mode == OpenFileForm.OPEN_PUBLISH:
            # open the published file instead:
            if not self._do_open_publish_as_workfile(publish_file, next_version):
                return False
        else:
            # cancelled so stop!
            return False
        
        return True
        
    def _do_open_workfile(self, file, env, parent_ui):
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
        
        
        
        
        
        
        
        
        
        