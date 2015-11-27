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
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui

from .file_action import FileAction
from ..scene_operation import prepare_new_scene, reset_current_scene, NEW_FILE_ACTION

class NewFileAction(FileAction):
    """
    """

    @staticmethod
    def can_do_new_file(env):
        """
        Do some validation to see if it's possible to
        start a new file with the selected context.
        """
        can_do_new = (env.context != None 
                      and (env.context.entity or env.context.project)
                      and env.work_area_template != None)
        return can_do_new

    def __init__(self, file, file_versions, environment):
        """
        """
        FileAction.__init__(self, "New File", file, file_versions, environment)

    def execute(self, parent_ui):
        """
        Perform a new-scene operation initialized with
        the current context
        """
        if not NewFileAction.can_do_new_file(self.environment):
            # should never get here as the new button in the UI should
            # be disabled!
            return False

        try:
            # create folders and validate that we can save using the work template:
            try:
                # create folders if needed:
                NewFileAction.create_folders_if_needed(self.environment.context, self.environment.work_template)
                # and double check that we can get all context fields for the work template:
                self.environment.context.as_template_fields(self.environment.work_template, validate=True)
            except TankError, e:
                # log the original exception (useful for tracking down the problem) 
                self._app.log_exception("Unable to resolve template fields after folder creation!")
                # and raise a new, clearer exception for this specific use case:
                raise TankError("Unable to resolve template fields after folder creation!  This could mean "
                                "there is a mismatch between your folder schema and templates.  Please email "
                                "support@shotgunsoftware.com if you need help fixing this.") 

            # reset the current scene:
            if not reset_current_scene(self._app, NEW_FILE_ACTION, self.environment.context):
                self._app.log_debug("Unable to perform New Scene operation after failing to reset scene!")
                return False
    
            # prepare the new scene:
            prepare_new_scene(self._app, NEW_FILE_ACTION, self.environment.context)
    
            if not self.environment.context == self._app.context:
                # restart the engine with the new context
                FileAction.restart_engine(self.environment.context)

        except Exception, e:
            error_title = "Failed to complete '%s' action" % self.label
            QtGui.QMessageBox.information(parent_ui, "%s!" % error_title, "%s:\n\n%s!" % (error_title, e))
            self._app.log_exception(error_title)
            return False

        return True

