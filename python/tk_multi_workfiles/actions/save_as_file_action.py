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
from sgtk.platform.qt import QtCore, QtGui

from .file_action import FileAction
from ..scene_operation import save_file, SAVE_FILE_AS_ACTION

class SaveAsFileAction(FileAction):
    """
    """
    def __init__(self):
        """
        """
        FileAction.__init__(self, "Save As")

    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        if not file or not file.path or not environment or not environment.context:
            return False

        # switch context:
        if not environment.context == self._app.context:
            try:
                # restart the engine with the new context
                self._restart_engine(environment.context)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to change the work area", 
                    "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" % (environment.context, e))
                self._app.log_exception("Failed to change the work area to %s!" % environment.context)
                return False

        try:
            # we used to always create folders but this seems unnecessary as the folders should have been
            # created when the work area was set - either as part of the launch process or when switching
            # work area within the app.
            # To be on the safe side though, we'll check if the directory that the file is being saved in
            # to exists and run create folders if it doesn't - this covers any potential edge cases where
            # the Work area has been set without folder creation being run correctly.
            dir = os.path.dirname(file.path)
            if not dir or not os.path.exists(dir):
                # work files always operates in some sort of context, either project, entity or task
                ctx_entity =  environment.context.task or  environment.context.entity or  environment.context.project
                self._app.log_debug("Creating folders for context %s" %  environment.context)
                self._app.sgtk.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"))
                # finally, make sure that the folder exists - this will handle any leaf folders that aren't
                # created above (e.g. a dynamic static folder that isn't part of the schema)
                self._app.ensure_folder_exists(dir)
    
            # and save the current file as the new path:
            save_file(self._app, SAVE_FILE_AS_ACTION,  environment.context, file.path)
        except Exception, e:
            QtGui.QMessageBox.critical(None, "Failed to save file!", "Failed to save file:\n\n%s" % e)
            self._app.log_exception("Something went wrong while saving!")
            return False
        
        return True