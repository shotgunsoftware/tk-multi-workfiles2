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
    
    create_task = QtCore.Signal()
    
    def __init__(self, app, init_cb=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self)
        
        self._app = app
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
            show_mine_only = bool(self._settings.value("show_mine_only", True))
            self._ui.mine_only_cb.setChecked(show_mine_only)
        except Exception, e:
            self._app.log_warning("Cannot restore state of 'Only Show My Tasks' checkbox: %s" % e)
        
        if init_cb:
            init_cb(self)
        
        # reload:
        self.reload()
        
    @property
    def exit_code(self):
        return self._exit_code
        
    @property
    def context(self):
        return self._get_context()
    """
    @context.setter
    def context(self, value):
        pass
    """
     
    def reload(self):
        """
        Called to reload data in the UI
        """
        # reload entities:
        self._reload_entities()
        
        # and reload tasks based on 
        # currently selected entity
        self._reload_tasks()
    
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
        self.create_task.emit()

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
            
    """
    def create_new_task(self):

        curr_selection = self._ui.entity_browser.get_selected_item()
        if curr_selection is None:
                QtGui.QMessageBox.warning(self, 
                                          "Please select an Entity!", 
                                          "Please select an Entity that you want to add a Task to.")
                return
            
        # do new task
        new_task = NewTaskDialog(self._app, curr_selection.sg_data, self)
        # need to keep the reference alive otherwise the window is destroyed
        if new_task.exec_() == QtGui.QDialog.Accepted:
            # do it!
            task_id = new_task.create_task()
            
            # refresh - in case they cancel the context set, the dialog is up to date.
            self.setup_task_list()
        
            # and set the context to point here!
            self._set_context(task_id)
    """
         
    def _on_mine_only_cb_toggled(self):
        """
        Called when mine-only checkbox is toggled
        """
        # remember setting:
        settings_val = self._ui.mine_only_cb.isChecked()
        self._settings.setValue("show_mine_only", settings_val)
        
        # reload entity list:
        self.reload()
                
        
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
        # clear both entity and task lists:
        self._ui.entity_browser.clear()
        self._ui.task_browser.clear()
        
        # reload entities:
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
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
        
        # pass in data to task retreiver
        d = {}
        d["own_tasks_only"] = self._ui.mine_only_cb.isChecked()
        d["entity"] = curr_selection.sg_data

        # pass in the sg data dump for the entity to the task loader code
        self._ui.task_browser.load(d)
        
        self._update_ui()
        
    def _update_ui(self):
        """
        Update UI following a change
        """
        current_entity = self._ui.entity_browser.selected_entity
        self._ui.select_btn.setEnabled(current_entity is not None)
        
    """
    def set_context(self):
        curr_selection = self._ui.task_browser.get_selected_item()
        if curr_selection is None:
            return

        self._set_context(curr_selection.sg_data.get("id"))
    """

    def _clear_current_scene_maya(self):
        """
        Clears the current scene. Does a file -> new.
        Maya implementation.
        returns False on cancel, true on success.
        """
        
        import pymel.core as pm
        import maya.cmds as cmds

        status = True
        
        if cmds.file(query=True, modified=True):
            
            # changes have been made to the scene
            res = QtGui.QMessageBox.question(self,
                                             "Save your scene?",
                                             "Your scene has unsaved changes. Save before proceeding?",
                                             QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
            
            if res == QtGui.QMessageBox.Cancel:
                status = False

            elif res == QtGui.QMessageBox.No:
                # don't save!
                cmds.file(newFile=True, force=True)
            
            else:
                # save before!
                
                if pm.sceneName() != "":
                    # scene has a name!
                    # normal save
                    cmds.file(save=True, force=True)
                    cmds.file(newFile=True, force=True)
                else:
                    # scene does not have a name. 
                    # save as dialog
                    cmds.SaveSceneAs()
                    # not sure about return value here, so check the scene!
                    if cmds.file(query=True, modified=True):
                        # still unsaved changes
                        # assume user clicked cancel in dialog
                        status = False

        return status
        
        
        
        
        
        
    def _clear_current_scene_motionbuilder(self):
        """
        Clears the current scene. Does a file -> new.
        Motionbuilder implementation.
        returns False on cancel, true on success.
        """
        from pyfbsdk import FBApplication
        status = True

        fb_app = FBApplication()

        res = QtGui.QMessageBox.question(self,
                                         "Save your scene?",
                                         "Your scene has unsaved changes. Save before proceeding?",
                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)

        if res == QtGui.QMessageBox.Cancel:
            status = False
            
        elif res == QtGui.QMessageBox.No:
            # don't save!
            fb_app.FileNew()
            
        else:
            # save before!
            fb_app.FileSave()
            fb_app.FileNew()

        return status
        



    def _set_context(self, task_id):
        """
        Set context based on selected task
        """

        try:
            ctx = self._app.tank.context_from_entity("Task", task_id)
        except Exception, e:            
            QtGui.QMessageBox.critical(self, 
                                       "Cannot Resolve Task!", 
                                       "Cannot resolve this task into a context: %s" % e)
            return


        res = QtGui.QMessageBox.question(self,
                                         "Change work area?",
                                         "This will switch your work area to the "
                                         "selected Task. Are you sure you want to continue?",
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel)

        if res == QtGui.QMessageBox.Ok:            
            
            # first clear the scene
            if self._app.engine.name == "tk-maya":
                
                if not self._clear_current_scene_maya():
                    # return back to dialog
                    return
            
            elif self._app.engine.name == "tk-3dsmax":
                
                from Py3dsMax import mxs
                
                if mxs.getSaveRequired():
                    # not an empty scene
                    # this will ask the user if they want to reset
                    mxs.resetMaxFile()
                    
                if mxs.getSaveRequired():
                    # if save is still required, this means that the user answered No
                    # when asked to reset. So now, exit and don't carry out the switch
                    return
                
            
            elif self._app.engine.name == "tk-motionbuilder":
                if not self._clear_current_scene_motionbuilder():
                    # return back to dialog
                    return
                
                
            # note - on nuke, we always start from a clean scene, so no need to check.
                
            # ok scene is clear. Now switch!
            
            # Try to create path for the context.  
            try:
                self._app.tank.create_filesystem_structure("Task", task_id, engine=self._app.engine.name)
                current_engine_name = self._app.engine.name            
                if tank.platform.current_engine(): 
                    tank.platform.current_engine().destroy()
                tank.platform.start_engine(current_engine_name, ctx.tank, ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(self, 
                                           "Could not Switch!", 
                                           "Could not change work area and start a new " 
                                           "engine. This can be because the task doesn't "
                                           "have a step. Details: %s" % e)
                return
            
            
            # close dialog
            self.close()
        
        
        
        
        