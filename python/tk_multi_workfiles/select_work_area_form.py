# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import threading

import tank
from tank import TankError
from tank.platform.qt import QtCore, QtGui

from .task_browser import TaskBrowserWidget

class SelectWorkAreaForm(QtGui.QWidget):
    
    [SELECT_WORK_AREA, CHANGE_WORK_AREA, CHANGE_WORK_AREA_NO_NEW] = range(3)
    
    def __init__(self, app, handler, mode=SELECT_WORK_AREA, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._app = app
        self._handler = handler
        self._mode = mode
        self._do_new_scene = False
        
        # get the current work area's entity and task
        ctx = self._handler.get_current_work_area()
        self._current_context_task = ctx.task if ctx else None
        self._current_context_entity = ctx.entity if ctx else None        
        
        self._exit_code = QtGui.QDialog.Rejected
        self._settings = QtCore.QSettings("Shotgun Software", "tk-multi-workfiles")

        # set up the UI
        from .ui.select_work_area_form import Ui_SelectWorkAreaForm
        self._ui = Ui_SelectWorkAreaForm() 
        self._ui.setupUi(self)
        
        # set up the entity browser:
        self._ui.entity_browser.set_app(self._app)
        self._ui.entity_browser.selection_changed.connect(self._on_entity_selected)
        
        types_to_load = self._app.get_setting("sg_entity_types", [])
        types_str = "Entities"
        if types_to_load:
            types_nice_names = [ tank.util.get_entity_type_display_name(self._app.tank, x) for x in types_to_load ]
            
            plural_types = [ "%ss" % x for x in types_nice_names] # no fanciness (sheep, box, nucleus etc)
            if len(plural_types) == 1:
                # "Shots"
                types_str = plural_types[0]
            else:
                # "Shots, Assets & Sequences"
                types_str = ", ".join(plural_types[:-1])
                types_str += " & %s" % plural_types[-1]
        self._ui.entity_browser.set_label(types_str)
        
        # set up the task browser:
        self._ui.task_browser.set_app(self._app)
        self._ui.task_browser.selection_changed.connect(self._on_task_selected)
        self._ui.task_browser.action_requested.connect(self._on_context_selected)
        self._ui.task_browser.set_label("Tasks")
        
        # mode specific:
        self._ui.select_new_btn.setVisible(self._mode == SelectWorkAreaForm.CHANGE_WORK_AREA)
        self._ui.select_btn.setText("Change Work Area" if self._mode != SelectWorkAreaForm.SELECT_WORK_AREA else "Select")
        
        # connect the buttons:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.select_btn.clicked.connect(self._on_context_selected)
        self._ui.select_new_btn.clicked.connect(self._on_select_and_new)
       
       # enable/disable task creation 
        self._can_create_tasks = self._app.get_setting("allow_task_creation")
        if self._can_create_tasks:
            self._ui.new_task_btn.clicked.connect( self._on_create_new_task )
        else:
            self._ui.new_task_btn.setVisible(False)
        
        # set up the 'Only Show My Tasks' checkbox:
        self._ui.mine_only_cb.toggled.connect(self._on_mine_only_cb_toggled)
        try:
            # this qsettings stuff seems super flaky on different platforms
            # - although setting is saved as an int, it can get loaded as either an 
            # int or a string, hence the double casting to int and then bool.
            show_mine_only = bool(int(self._settings.value("show_mine_only", True)))
            self._ui.mine_only_cb.setChecked(show_mine_only)    
        except Exception, e:
            self._app.log_warning("Cannot restore state of 'Only Show My Tasks' checkbox: %s" % e)

        # reload:
        self._reload_entities()
        
    @property
    def exit_code(self):
        """
        The exit code of the dialog. Not really relevant to call until after the dialog has closed.
        """
        return self._exit_code
        
    @property
    def context(self):
        """
        A context object representing the current selection
        """
        
        # get the selected task:
        task = self._ui.task_browser.selected_task
        
        # try to create a context:
        ctx = None
        if task:
            ctx = self._app.tank.context_from_entity("Task", task.get("id"))
        else:
            # no task selected so use entity instead:
            entity = self._ui.entity_browser.selected_entity
            if entity:
                ctx = self._app.tank.context_from_entity(entity.get("type"), entity.get("id"))
                
        return ctx        

    @property
    def do_new_scene(self):
        """
        Indicating that the user exited the dialog with a desire to have the current scene reset.
        """
        return self._do_new_scene
        
    def closeEvent(self, event):
        """
        Make sure that the various background threads are closed
        """
        self._ui.entity_browser.destroy()
        self._ui.task_browser.destroy()
        # okay to close!
        event.accept()
    
    def _on_cancel(self):
        """
        The cancelled
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()    
        
    def _on_context_selected(self):
        """
        The user pressed the change context button
        """
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
        
    def _on_select_and_new(self):
        """
        The user pressed the new scene button 
        """
        self._do_new_scene = True
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
        
    def _on_create_new_task(self):
        """
        Called when create task button is clicked
        """
        
        # get the current entity:
        current_entity = self._ui.entity_browser.selected_entity
        if current_entity is None:
            QtGui.QMessageBox.warning(self,
                                      "Please select an Entity!",
                                      "Please select an Entity that you want to add a Task to.")
            return

        # get the current user:
        current_user = tank.util.get_current_user(self._app.tank)

        # show new task dialog:
        from .wrapper_dialog import WrapperDialog
        from .new_task_form import NewTaskForm
        form = NewTaskForm(self._app, current_entity, current_user)
        
        res = WrapperDialog.show_modal(form, "Create New Task", parent=self)
        if res == QtGui.QDialog.Accepted:
            # get details from form:
            entity = form.entity
            assigned_to = form.assigned_to
            pipeline_step = form.pipeline_step
            task_name = form.task_name
            
            new_task = None
            try:
                new_task = self._handler.create_new_task(task_name, pipeline_step, entity, assigned_to)
            except TankError, e:
                QtGui.QMessageBox.warning(self,
                                      "Failed to create new task!",
                                      ("Failed to create a new task '%s' for pipeline step '%s' on entity '%s %s':\n\n%s" 
                                       % (task_name, pipeline_step.get("code"), entity["type"], entity["code"], e)))
            else:
                # reload tasks, selecting the new task:
                self._reload_tasks(new_task)

    def _on_mine_only_cb_toggled(self):
        """
        Called when my tasks only checkbox is toggled
        """
        # remember setting - save value as an int as this
        # can be handled across all operating systems!
        # - on Windows & Linux, boolean & int settings are 
        # returned as strings when queried!
        show_mine_only = self._ui.mine_only_cb.isChecked()
        self._settings.setValue("show_mine_only", int(show_mine_only))
        
        # reload entity list:
        self._reload_entities()
                
        
    def _on_entity_selected(self):
        """
        Called when the selected entity is changed
        """
        self._reload_tasks()
        
    def _on_task_selected(self):
        """
        Called when the selected task is changed
        """
        self._update_ui()
        
    def _reload_entities(self):
        """
        Called to reload the list of entities
        """
        
        # preserve selection.
        currently_selected_entity = self._ui.entity_browser.selected_entity
                    
        # clear both entity and task lists:
        self._ui.entity_browser.clear()
        self._ui.task_browser.clear()
        
        # reload entities
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
        
        if currently_selected_entity:
            # re-select previous selection
            d["entity"] = currently_selected_entity
        else:
            # select the current context entity 
            d["entity"] = self._current_context_entity
            
        self._ui.entity_browser.load(d)
        
    def _reload_tasks(self, selected_task = None):
        """
        Called to reload the list of tasks based on the 
        currently selected entity
        """
        
        # reset task widget completely
        self._ui.task_browser.clear()
        
        curr_selection = self._ui.entity_browser.get_selected_item()
        if curr_selection is None:
            self._ui.task_browser.set_message("Please select an item in the listing to the left.")
            self._update_ui()
            return

        # pass in data to task retreiver
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
        d["entity"] = curr_selection.sg_data
        d["can_create_tasks"] = self._can_create_tasks
        
        # now figure out which item to select
        if selected_task:
            # select specifically requested item
            d["task"] = selected_task
        
        else:
            # the currently selected entity represents the current context.
            # in this case, hint by defaulting to the task that represents the context
            #
            # note that this task that we hint may not be in the list of loaded tasks
            # in that case, nothing is selected
            d["task"] = self._current_context_task
        
        # pass in the sg data dump for the entity to the task loader code
        self._ui.task_browser.load(d)
        
        self._update_ui()
        
    def _update_ui(self):
        """
        Update UI following a change
        """
        current_entity = self._ui.entity_browser.selected_entity
        self._ui.select_btn.setEnabled(current_entity is not None)
        self._ui.new_task_btn.setEnabled(current_entity is not None)
        
        
        
