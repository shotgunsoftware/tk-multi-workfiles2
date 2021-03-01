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
from sgtk import support_url

from .file_action import FileAction
from .action import Action
from ..scene_operation import prepare_new_scene, reset_current_scene, NEW_FILE_ACTION


class NewFileAction(Action):
    """
    This action creates a new file in the given environment.
    """

    @staticmethod
    def can_do_new_file(env):
        """
        Do some validation to see if it's possible to
        start a new file with the selected context.
        """
        can_do_new = (
            env.context is not None
            and (env.context.entity or env.context.project)
            and env.work_area_template is not None
        )
        return can_do_new

    def __init__(self, environment):
        """
        Constructor.

        :param environment: A WorkArea instance of where the new file will go.
        """
        Action.__init__(self, "New File")
        self._environment = environment

    def execute(self, parent_ui):
        """
        Perform a new-scene operation initialized with the current context.

        :param parent_ui: Parent dialog executing this action.
        """
        if not NewFileAction.can_do_new_file(self._environment):
            # should never get here as the new button in the UI should
            # be disabled!
            return False

        try:
            # create folders and validate that we can save using the work template:
            try:
                # create folders if needed:
                FileAction.create_folders_if_needed(
                    self._environment.context, self._environment.work_template
                )
                # and double check that we can get all context fields for the work template:
                self._environment.context.as_template_fields(
                    self._environment.work_template, validate=True
                )
            except TankError as tank_error:
                self._app.log_exception(
                    "Unable to resolve template fields after folder creation!"
                )

                error_title = "Failed to complete '{}' action".format(self.label)
                error_text = "{title}:\n\n{body}".format(
                    title=error_title,
                    body=(
                        "Unable to resolve template fields after folder creation!  This could mean "
                        "there is a mismatch between your folder schema and templates. Please "
                        "contact us via {} if you need help fixing this.".format(
                            support_url
                        )
                    ),
                )
                error_details = str(tank_error)

                msg_box = QtGui.QMessageBox(
                    QtGui.QMessageBox.Information,
                    error_title,
                    error_text,
                    QtGui.QMessageBox.Ok,
                    parent_ui,
                )
                msg_box.setDefaultButton(QtGui.QMessageBox.Ok)
                if error_details:
                    msg_box.setDetailedText(error_details)

                msg_box.exec_()
                return False

            else:
                # reset the current scene:
                if not reset_current_scene(
                    self._app, NEW_FILE_ACTION, self._environment.context
                ):
                    self._app.log_debug(
                        "Unable to perform New Scene operation after failing to reset scene!"
                    )
                    return False

                # prepare the new scene:
                prepare_new_scene(self._app, NEW_FILE_ACTION, self._environment.context)

                if not self._environment.context == self._app.context:
                    # Change context
                    FileAction.change_context(self._environment.context)

        except Exception as e:
            error_title = "Failed to complete '%s' action" % self.label
            QtGui.QMessageBox.information(
                parent_ui, error_title, "%s:\n\n%s" % (error_title, e)
            )
            self._app.log_exception(error_title)
            return False
        else:
            try:
                self._app.log_metric("New Workfile")
            except:
                # ignore all errors. ex: using a core that doesn't support metrics
                pass

        return True
