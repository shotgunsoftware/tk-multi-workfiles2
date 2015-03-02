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

from .file_action import FileAction
from ..scene_operation import reset_current_scene, open_file, OPEN_FILE_ACTION

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
            open_file(self._app, OPEN_FILE_ACTION, new_ctx, dst_path, version, read_only)
        except Exception, e:
            QtGui.QMessageBox.critical(parent_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (dst_path, e))
            self._app.log_exception("Failed to open file %s!" % dst_path)    
            return False
        
        return True