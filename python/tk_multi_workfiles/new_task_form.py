# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank.platform.qt import QtCore, QtGui

class NewTaskForm(QtGui.QWidget):
    """
    Form for requesting details needed to create
    a new Shotgun task 
    """
    
    @property
    def exit_code(self):
        return self._exit_code    
    
    def __init__(self, app, entity, user, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._app = app
        self._entity = entity
        self._user = user
        self._exit_code = QtGui.QDialog.Rejected
        
        # set up the UI
        from .ui.new_task_form import Ui_NewTaskForm
        self._ui = Ui_NewTaskForm()
        self._ui.setupUi(self)

        # populate entity name
        entity_name = "%s %s" % (self._entity["type"], self._entity["code"])
        self._ui.entity.setText(entity_name)
        
        # populate user
        username = self._user["name"] if self._user else "<unassigned>"
        self._ui.assigned_to.setText(username)
        
        # populate pipeline steps
        sg_result = self._app.shotgun.find("Step", [["entity_type", "is", self._entity["type"]]], ["code", "id"])
        self._pipeline_step_dict = {}
        for item in sg_result:
            step_name = item.get("code")
            if step_name is None:
                step_name = "Unnamed Step"
            self._ui.pipeline_step.addItem(step_name, item["id"])
            self._pipeline_step_dict[item["id"]] = item
        
        # try to figure out a default pipeline step and task name
        if self._app.context.step:
            # update menu to show the same step as the current app context:
            step_id = self._app.context.step["id"]
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
            
        # hook up controls:
        self._ui.create_btn.clicked.connect(self._on_create_btn_clicked)

        # initialize line to be plain and the same colour as the text:        
        self._ui.break_line.setFrameShadow(QtGui.QFrame.Plain)
        clr = QtGui.QApplication.palette().text().color()
        self._ui.break_line.setStyleSheet("#break_line{color: rgb(%d,%d,%d);}" % (clr.red() * 0.75, clr.green() * 0.75, clr.blue() * 0.75))

    @property
    def entity(self):
        return self._entity
    
    @property
    def assigned_to(self):
        return self._user
    
    @property
    def pipeline_step(self):
        """
        Return the selected pipeline step:
        """
        step_id = self._ui.pipeline_step.itemData(self._ui.pipeline_step.currentIndex())

        # convert from QVariant object if itemData is returned as such
        if hasattr(QtCore, "QVariant") and isinstance(step_id, QtCore.QVariant):
            step_id = step_id.toPyObject()
        
        return self._pipeline_step_dict[step_id]
    
    @property
    def task_name(self):
        return self._safe_to_string(self._ui.task_name.text())

    def _on_create_btn_clicked(self):
        self._exit_code = QtGui.QDialog.Accepted
        self.close()

    def _safe_to_string(self, value):
        """
        Safely convert the value to a string - handles
        QtCore.QString if usign PyQt
        """
        if isinstance(value, basestring):
            # it's a string anyway so just return
            return value
        
        if hasattr(QtCore, "QString"):
            # running PyQt!
            if isinstance(value, QtCore.QString):
                # QtCore.QString inherits from str but supports 
                # unicode, go figure!  Lets play safe and return
                # a utf-8 string
                return str(value.toUtf8())
        
        # For everything else, just return as string
        return str(value)

