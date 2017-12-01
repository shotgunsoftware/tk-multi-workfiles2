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
    def __init__(self, file_item, environment):
        """
        """
        FileAction.__init__(self, "Save As", file_item, None, environment)

    def execute(self, parent_ui):
        """
        """
        if (not self.file or not self.file.path 
            or not self.environment or not self.environment.context):
            return False

        # switch context:
        previous_context = self._app.context
        if not self.environment.context == self._app.context:
            try:
                # Change the current context
                FileAction.change_context(self.environment.context)
            except Exception, e:
                QtGui.QMessageBox.critical(parent_ui, "Failed to change the work area", 
                    "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" 
                    % (self.environment.context, e))
                self._app.log_exception("Failed to change the work area to %s!" % self.environment.context)
                return False

        # and save the current file as the new path:
        try:
            save_file(self._app, SAVE_FILE_AS_ACTION, self.environment.context, self.file.path)
        except Exception, e:
            QtGui.QMessageBox.critical(None, "Failed to save file!", "Failed to save file:\n\n%s" % e)
            self._app.log_exception("Failed to save file!")
            FileAction.restore_context(parent_ui, previous_context)
            return False

        try:
            self._app.log_metric("Saved Workfile")
        except:
            # ignore all errors. ex: using a core that doesn't support metrics
            pass

        return True
