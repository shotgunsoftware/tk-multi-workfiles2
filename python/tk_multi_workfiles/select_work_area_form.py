"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os
import sys
import threading

import tank
from tank.platform.qt import QtCore, QtGui

from .task_browser import TaskBrowserWidget

class SelectWorkAreaForm(QtGui.QWidget):
    
    def __init__(self, app, handler, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._app = app
        self._handler = handler
        
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
        #self._ui.task_browser.action_requested.connect(self._on_context_selected)
        self._ui.task_browser.set_label("Tasks")
        
        # connect the buttons:
        self._ui.select_btn.clicked.connect(self._on_context_selected)
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        
        #TODO: implement task creation!
        can_create_tasks = False#self._app.get_setting("allow_task_creation")        
        if can_create_tasks:
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
        ctx = self._handler.get_current_work_area()
        self._initial_task_to_select = ctx.task if ctx else None
        self._reload_entities(ctx.entity if ctx else None)
        
    @property
    def exit_code(self):
        return self._exit_code
        
    @property
    def context(self):
        return self._get_context()
        
    def closeEvent(self, event):
        """
        Make sure that the various background threads are closed
        """
        self._ui.entity_browser.destroy()
        self._ui.task_browser.destroy()
        # okay to close!
        event.accept()
    
    def _on_cancel(self):
        self._exit_code = QtGui.QDialog.Rejected
        self.close()    
        
    def _on_context_selected(self):
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
        
    def _on_create_new_task(self):
        """
        Called when create task button is clicked
        """
        # run new task:
        self._handler.create_new_task()

    def _get_context(self):
        """
        Return a context for the current selection
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
         
    def _on_mine_only_cb_toggled(self):
        """
        Called when mine-only checkbox is toggled
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
        
    def _reload_entities(self, entity_to_select = None):
        """
        Called to reload the list of entities
        """
        if not entity_to_select:
            entity_to_select = self._ui.entity_browser.selected_entity
            self._initial_task_to_select = None
        
        # clear both entity and task lists:
        self._ui.entity_browser.clear()
        self._ui.task_browser.clear()
        
        # reload entities:
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
        d["entity"] = entity_to_select
        self._ui.entity_browser.load(d)
        
    def _reload_tasks(self):
        """
        Called to reload the list of tasks based on the 
        currently selected entity
        """
        self._ui.task_browser.clear()
        
        curr_selection = self._ui.entity_browser.get_selected_item()
        if curr_selection is None:
            self._ui.task_browser.set_message("Please select an item in the listing to the left.")
            self._update_ui()
            return

        task_to_select = self._ui.task_browser.selected_task
        if not task_to_select:
            task_to_select = self._initial_task_to_select
        
        # pass in data to task retreiver
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
        d["entity"] = curr_selection.sg_data
        d["task"] = task_to_select
        
        # pass in the sg data dump for the entity to the task loader code
        self._ui.task_browser.load(d)
        
        self._update_ui()
        
    def _update_ui(self):
        """
        Update UI following a change
        """
        current_entity = self._ui.entity_browser.selected_entity
        self._ui.select_btn.setEnabled(current_entity is not None)
