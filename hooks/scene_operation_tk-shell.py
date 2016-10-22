# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import sgtk
from sgtk.platform.qt import QtGui

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the current scene.
    """

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point.

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """
        engine = self.parent.engine

        engine.log_debug("scene_operation.execute.%s" % operation)
        engine.log_debug("    file_path: %s" % file_path)
        engine.log_debug("    context: %s" % context)
        engine.log_debug("    parent_action: %s" % parent_action)
        engine.log_debug("    file_version: %s" % file_version)
        engine.log_debug("    read_only: %s" % read_only)

        if operation == "current_path":
            return os.getcwd()
        elif operation == "reset":
            return True
        elif operation == "open":
            return QtGui.QMessageBox.question(
                None, "", "Are you sure you want to open?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            ) == QtGui.QMessageBox.Yes
