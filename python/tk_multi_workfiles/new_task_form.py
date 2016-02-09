# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
New Task Form.
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .util import value_to_str

get_type_display_name = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_globals"
).get_type_display_name


class NewTaskForm(QtGui.QWidget):
    """
    Form for requesting details needed to create a new Shotgun task.
    """

    @property
    def exit_code(self):
        """
        Exit code of the dialog.

        :returns: QtGui.QDialog.Accepted or QtGui.QDialog.Rejected
        """
        return self._exit_code

    @property
    def hide_tk_title_bar(self):
        """
        Hint to hide the Toolkit title bar.

        :returns: True.
        """
        return True

    def __init__(self, entity, step, user, parent):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._app = sgtk.platform.current_bundle()
        self._entity = entity
        self._user = user
        self._exit_code = QtGui.QDialog.Rejected

        # set up the UI
        from .ui.new_task_form import Ui_NewTaskForm
        self._ui = Ui_NewTaskForm()
        self._ui.setupUi(self)

        # populate entity name
        entity_name = "%s %s" % (
            get_type_display_name(self._entity["type"]),
            self._entity.get("code") or entity.get("name")
        )
        self._ui.entity.setText(entity_name)

        # populate user
        username = self._user.get("name") if self._user else None
        self._ui.assigned_to.setText(username or "<unassigned>")

        # populate pipeline steps for this entity type:
        sg_result = self._app.shotgun.find("Step", [["entity_type", "is", self._entity["type"]]], ["code", "id"])
        self._pipeline_step_dict = {}
        for item in sg_result:
            step_name = item.get("code")
            if step_name is None:
                step_name = "Unnamed Step"
            self._ui.pipeline_step.addItem(step_name, item["id"])
            self._pipeline_step_dict[item["id"]] = item

        # try to figure out a default pipeline step and task name
        if step:
            # update menu to show the same step as the current app context:
            step_id = step["id"]
            idx = self._ui.pipeline_step.findData(step_id)
            if idx != -1:
                self._ui.pipeline_step.setCurrentIndex(idx)

            # update task name text edit to be the same as the step name if we have one:
            step_name = self._pipeline_step_dict.get(step_id, {}).get("code", "")
            self._ui.task_name.setText(step_name)

        # Select the task name text as the user will probably
        # want to change this first!
        self._ui.task_name.setFocus()
        self._ui.task_name.selectAll()

        validator = self._app.execute_hook_method(
            "create_new_task_hook",
            "create_task_name_validator"
        )
        if validator:
            # Take ownership since the widget doesn't.
            validator.setParent(self)
            self._ui.task_name.setValidator(validator)

        # hook up controls:
        self._ui.create_btn.clicked.connect(self._on_create_btn_clicked)

        # initialize line to be plain and the same colour as the text:
        self._ui.break_line.setFrameShadow(QtGui.QFrame.Plain)
        clr = QtGui.QApplication.palette().text().color()
        self._ui.break_line.setStyleSheet("#break_line{color: rgb(%d,%d,%d);}" % (clr.red() * 0.75, clr.green() * 0.75, clr.blue() * 0.75))

    def _get_pipeline_step(self):
        """
        :returns: The selected pipeline step.
        """
        step_id = self._ui.pipeline_step.itemData(self._ui.pipeline_step.currentIndex())

        # convert from QVariant object if itemData is returned as such
        if hasattr(QtCore, "QVariant") and isinstance(step_id, QtCore.QVariant):
            step_id = step_id.toPyObject()

        return self._pipeline_step_dict[step_id]

    def _get_task_name(self):
        """
        :returns: The task name entered by the user.
        """
        return value_to_str(self._ui.task_name.text())

    def _set_warning(self, msg):
        """
        Display a warning inside the dialog.

        :param msg: Message to display.
        """
        self._ui.warning.setText("<p style='color:rgb%s'>Failed to create a new task: %s</p>" % (self._app.warning_color, msg))

    def _on_create_btn_clicked(self):
        """
        Called when the user is ready to create the task.
        """
        if len(self._get_task_name()) == 0:
            self._set_warning("Please enter a task name.")
            return

        try:
            self._app.execute_hook_method(
                "create_new_task_hook",
                "create_new_task",
                name=self._get_task_name(),
                pipeline_step=self._get_pipeline_step(),
                entity=self._entity,
                assigned_to=self._user
            )
            self._exit_code = QtGui.QDialog.Accepted
            self.close()
        except sgtk.TankError, e:
            self._set_warning(str(e))
