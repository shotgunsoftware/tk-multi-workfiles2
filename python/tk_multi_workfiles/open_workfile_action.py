# Copyright (c) 2013 Shotgun Software Inc.
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

from .file_action import FileAction
from .scene_operation import reset_current_scene, prepare_new_scene, open_file, OPEN_FILE_ACTION, NEW_FILE_ACTION

class OpenAction(FileAction):
    def __init__(self):
        """
        """
        FileAction.__init__(self, "open", "Open")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        # this is the smart action where all the logic goes
        # to decide what the actual action should be!
        print "Executing action: %s for file %s" % (self.name, file) 

    def _create_folders(self, ctx):
        """
        Create folders for specified context
        """
        self._app.log_debug("Creating folders for context %s" % ctx)
        
        # create folders:
        ctx_entity = ctx.task or ctx.entity or ctx.project
        self._app.sgtk.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), 
                                                   engine=self._app.engine.name)

    def _copy_file(self, source_path, target_path):
        """
        Use hook to copy a file from source to target path
        """
        self._app.log_debug("Copying file '%s' to '%s' via hook" % (source_path, target_path))
        self._app.execute_hook("hook_copy_file", 
                               source_path=source_path, 
                               target_path=target_path)

    def _restart_engine(self, ctx):
        """
        Set context to the new context.  This will
        clear the current scene and restart the
        current engine with the specified context
        """
        self._app.log_debug("Restarting the engine...")
        
        # restart engine:        
        try:
            current_engine_name = self._app.engine.name
            
            # stop current engine:            
            if sgtk.platform.current_engine(): 
                sgtk.platform.current_engine().destroy()
                
            # start engine with new context:
            sgtk.platform.start_engine(current_engine_name, ctx.sgtk, ctx)
        except Exception, e:
            raise TankError("Failed to change work area and start a new engine - %s" % e)

    def _do_copy_and_open(self, src_path, work_path, version, read_only, new_ctx, parent_ui):
        """
        Copies src_path to work_path, creates folders, restarts the engine and then opens 
        the file from work_path
        
        :param src_path:    The path of the file to copy
        :param work_path:   The destination work file path
        :param version:     The version of the work file to be opened
        :param read_only:   True if the work file should be opened read-only
        :param new_ctx:     The context that the work file should be opened in
        :returns:           True of the source file is copied and successfully opened
        """
        if not work_path or not new_ctx:
            # can't do anything!
            return False
           
        if src_path and src_path != work_path:
            # check that the source path exists:        
            if not os.path.exists(src_path):
                QtGui.QMessageBox.critical(parent_ui, "File doesn't exist!", 
                                           "The file\n\n%s\n\nCould not be found to open!" % src_path)
                return False
            
        if not new_ctx == self._app.context:
            # ensure folders exist.  This serves the
            # dual purpose of populating the path
            # cache and ensuring we can copy the file
            # if we need to
            try:
                self._create_folders(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to create folders!", 
                                           "Failed to create folders:\n\n%s!" % e)
                self._app.log_exception("Failed to create folders")
                return False
        
        # reset the current scene:
        try:
            if not reset_current_scene(self._app, OPEN_FILE_ACTION, self._context):
                self._app.log_debug("Failed to reset the current scene!")
                return False
        except Exception, e:
            QtGui.QMessageBox.critical(parent_ui, "Failed to reset the scene", 
                                       "Failed to reset the scene:\n\n%s\n\nUnable to continue!" % e)
            self._app.log_exception("Failed to reset the scene!")
            return False
    
        # if need to, copy the file
        if src_path and src_path != work_path:
            # check that local path doesn't already exist:
            if os.path.exists(work_path):
                #TODO: replace with Toolkit dialog
                answer = QtGui.QMessageBox.question(parent_ui, "Overwrite file?",
                                "The file\n\n%s\n\nalready exists.  Would you like to overwrite it?" % (work_path), 
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return False
                
            try:
                # make sure that the folder exists - this will handle any leaf folders that aren't
                # created by Toolkit (e.g. a dynamic static folder that isn't part of the schema)
                work_dir = os.path.dirname(work_path)
                self._app.ensure_folder_exists(work_dir)
                # copy file:
                self._copy_file(src_path, work_path)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Copy file failed!", 
                                           "Copy of file failed!\n\n%s!" % e)
                self._app.log_exception("Copy file failed")
                return False            
                    
        # switch context:
        if not new_ctx == self._app.context:
            try:
                # restart the engine with the new context
                self._restart_engine(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to change the work area", 
                            "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" % (new_ctx, e))
                self._app.log_exception("Failed to change the work area to %s!" % new_ctx)
                return False

        # open file
        try:
            open_file(self._app, OPEN_FILE_ACTION, self._context, work_path, version, read_only)
        except Exception, e:
            QtGui.QMessageBox.critical(parent_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (work_path, e))
            self._app.log_exception("Failed to open file %s!" % work_path)    
            return False
        
        return True

class OpenWorkfileAction(OpenAction):
    """
    """
    def __init__(self):
        """
        """
        OpenAction.__init__(self, "open_workfile", "Open Work File")
        
    def execute(self, file, file_versions, environment, parent_ui):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file or not file.is_local:
            return False

        if not file.editable:
            answer = QtGui.QMessageBox.question(parent_ui, "Open file read-only?",
                                                ("The work file you are opening: '%s', is "
                                                "read-only:\n\n%s.\n\nWould you like to continue?" 
                                                % (file.name, file.not_editable_reason)), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
                return False

        return self._do_copy_and_open(None, file.path, None, not file.editable, environment.context)
        
        """
        # trying to open a work file...
        src_path = None
        work_path = file.path
        
        # construct a context for this path to determine if it's in
        # a user sandbox or not:
        wp_ctx = self._app.sgtk.context_from_path(work_path, self._context)
        if wp_ctx.user:
            current_user = sgtk.util.get_current_user(self._app.sgtk)
            if current_user and current_user["id"] != wp_ctx.user["id"]:
                
                # file is in a user sandbox - construct path
                # for the current user's sandbox:
                try:                
                    # get fields from work path:
                    fields = self._work_template.get_fields(work_path)
                    
                    # add in the fields from the context with the current user:
                    local_ctx = wp_ctx.create_copy_for_user(current_user)
                    ctx_fields = local_ctx.as_template_fields(self._work_template)
                    fields.update(ctx_fields)
                    
                    # construct the local path from these fields:
                    local_path = self._work_template.apply_fields(fields)                     
                except Exception, e:
                    QtGui.QMessageBox.critical(parent_ui, "Failed to resolve file path", 
                                           ("Failed to resolve the user sandbox file path:\n\n%s\n\nto the local "
                                           "path:\n\n%s\n\nUnable to open file!" % (work_path, e)))
                    self._app.log_exception("Failed to resolve user sandbox file path %s" % work_path)
                    return False
        
                if local_path != work_path:
                    # more than just an open so prompt user to confirm:
                    #TODO: replace with Toolkit dialog
                    answer = QtGui.QMessageBox.question(parent_ui, "Open file from another user?",
                                                        ("The work file you are opening:\n\n%s\n\n"
                                                        "is in a user sandbox belonging to %s.  Would "
                                                        "you like to copy the file to your sandbox and open it?" 
                                                        % (work_path, wp_ctx.user["name"])), 
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                    if answer == QtGui.QMessageBox.Cancel:
                        return False

                    src_path = work_path
                    work_path = local_path      
                    
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.sgtk.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  

        return self._do_copy_and_open(src_path, work_path, None, not file.editable, new_ctx)
        """
    
