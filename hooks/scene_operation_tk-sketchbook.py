# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.
#

import sgtk
from sgtk.platform.qt import QtCore, QtGui

import sketchbook_api

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the current scene
    """

    def execute(
        self,
        operation,
        file_path,
        context,
        parent_action,
        file_version,
        read_only,
        **kwargs
    ):
        """
        Main hook entry point

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
                                all others     - True if operation was successfully completed,
                                                 otherwise False
        """
        if operation == "current_path":
            """
            Get current file path
            """
            return sketchbook_api.get_current_path()

        elif operation == "open":
            """
            File Open
            """
            # The reset operation should have been called before open, but just incase
            # make sure to check that the user will not lose any of their changes.
            success = self.save_or_discard_changes()
            if success:
                sketchbook_api.open_file(file_path)
            return success

        elif operation == "save":
            """
            File Save
            """
            sketchbook_api.save_file()
            return True

        elif operation == "save_as":
            """
            File Save As
            """
            sketchbook_api.save_file_as(file_path)
            return True

        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            success = self.save_or_discard_changes()
            if success:
                # Force the document to reset (e.g. changes will be discarded)
                sketchbook_api.reset(True)
            return success

        elif operation == "prepare_new":
            # Nothing to do
            return True

    def save_or_discard_changes(self):
        """
        Check if the current SketchBook document has any changes. Open a dialog to ask the user
        to save their changes, if any, or proceed with discarding any changes.
        """

        result = True
        restore_cursor = False

        while sketchbook_api.is_current_document_dirty():
            if not restore_cursor:
                restore_cursor = True
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.ArrowCursor)

            answer = QtGui.QMessageBox.question(
                None,
                "Save",
                "Your document has unsaved changes. Save before proceeding?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel,
            )

            if answer == QtGui.QMessageBox.Cancel:
                result = False
                break

            if answer == QtGui.QMessageBox.No:
                break

            self.parent.engine.show_save_dialog()

        if restore_cursor:
            QtGui.QApplication.restoreOverrideCursor()

        return result
