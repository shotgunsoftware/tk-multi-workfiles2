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
Action to create a new file.
"""

from sgtk import TankError
from sgtk.platform.qt import QtGui

from .file_action import FileAction
from .action import Action


class ContextChangeAction(Action):
    """
    This action changes the current engine context.
    """

    def __init__(self, environment):
        """
        Constructor.

        :param environment: A WorkArea instance of where the new file will go.
        """
        Action.__init__(self, "Change Context")
        self._environment = environment

    def execute(self, parent_ui):
        """
        Perform a new-scene operation initialized with the current context.

        :param parent_ui: Parent dialog executing this action.
        """

        try:
            # create folders and validate that we can save using the work template:
            try:
                # create folders if needed:
                FileAction.create_folders_if_needed(
                    self._environment.context, self._environment.work_template
                )
                # and double check that we can get all context fields for the work template:

            except TankError:
                # log the original exception (useful for tracking down the problem)
                self._app.log_exception("Unable to run folder creation!")

            if not self._environment.context == self._app.context:
                # Change context
                FileAction.change_context(self._environment.context)

        except Exception as e:
            error_title = "Failed to complete '%s' action" % self.label
            QtGui.QMessageBox.information(
                parent_ui, "%s" % error_title, "%s:\n\n%s" % (error_title, e)
            )
            self._app.log_exception(error_title)
            return False

        return True
