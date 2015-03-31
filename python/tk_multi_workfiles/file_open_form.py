# Copyright (c) 2014 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Qt widget that presents the user with a list of work files and publishes
so that they can choose one to open
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .actions.file_action import SeparatorFileAction
from .actions.file_action_factory import FileActionFactory

from .file_operation_form import FileOperationForm
from .ui.file_open_form import Ui_FileOpenForm

class FileOpenForm(FileOperationForm):
    """
    UI for opening a publish or work file.  Presents a list of available files to the user
    so that they can choose one to open in addition to any other user-definable actions.
    """
    perform_action = QtCore.Signal(object, object, object, object) # action, file, file_versions, environment
    
    @property
    def exit_code(self):
        return self._exit_code
    
    def __init__(self, init_callback, parent=None):
        """
        Construction
        """
        FileOperationForm.__init__(self, parent)
        
        self._exit_code = QtGui.QDialog.Rejected
        
        # create the action factory - this is used to generate actions
        # for the selected file
        self._action_factory = FileActionFactory()
        
        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)

        # tmp - disable some controls that currently don't work!
        self._ui.new_file_btn.setEnabled(False)
        self._ui.open_options_btn.hide()
        
        # initialize the browser widget:
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        self._ui.browser.create_new_task.connect(self._on_create_new_task)
        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(self._on_browser_file_double_clicked)
        self._ui.browser.file_context_menu_requested.connect(self._on_browser_context_menu_requested)

        # hook up all other controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.open_btn.clicked.connect(self._on_open)
        
        self._selected_file = None
        self._selected_file_env = None
        self._default_open_action = None
        self._on_selected_file_changed()

        # call init callback:
        if init_callback:
            init_callback(self)
            
        app = sgtk.platform.current_bundle()
        ctx_entity = app.context.task or app.context.step or app.context.entity
        self._ui.browser.select_entity(ctx_entity["type"], ctx_entity["id"])

    def select_entity(self, entity):
        """
        :param entity:  The entity or task to select in the current tree/my tasks view.  If it can't be found
                        then attempt to switch tabs if it can be found in a different tab! 
        """
        # TODO
        pass

    def _on_browser_file_selected(self, file, env):
        """
        """
        self._selected_file = file
        self._selected_file_env = env
        self._on_selected_file_changed()
    
    def _on_browser_file_double_clicked(self, file, env):
        """
        """
        self._selected_file = file
        self._selected_file_env = env
        self._on_selected_file_changed()
        self._on_open()
    
    def _on_selected_file_changed(self):
        """
        """
        # get the available actions for this file:
        file_actions = []
        if self._selected_file and self._selected_file_env:
            file_versions = self._file_model.get_file_versions(self._selected_file.key, self._selected_file_env) or {}
            file_actions = self._action_factory.get_actions(
                                        self._selected_file, 
                                        file_versions, 
                                        self._selected_file_env,
                                        workfiles_visible=self._ui.browser.work_files_visible, 
                                        publishes_visible=self._ui.browser.publishes_visible
                                        )
        
        if not file_actions:
            # disable both the open and open options buttons:
            self._ui.open_btn.setEnabled(False)
            self._ui.open_options_btn.setEnabled(False)
            return
        
        # update the open button:
        self._ui.open_btn.setEnabled(True)
        self._ui.open_btn.setText(file_actions[0].label)
        self._default_open_action = file_actions[0]
        
        # if we have more than one action then update the open options button:
        if len(file_actions) > 1:
            # enable the button:
            self._ui.open_options_btn.setEnabled(True)
            
            # build the menu and add the actions to it:
            menu = self._ui.open_options_btn.menu()
            if not menu:
                menu = QtGui.QMenu(self._ui.open_options_btn)
                self._ui.open_options_btn.setMenu(menu)
            menu.clear()
            self._populate_open_menu(menu, self._selected_file, self._selected_file_env, file_actions[1:])
        else:
            # just disable the button:
            self._ui.open_options_btn.setEnabled(False)

    def _on_browser_context_menu_requested(self, file, env, pnt):
        """
        """
        if not file:
            return
        
        # get the file actions:
        file_actions = []
        file_versions = self._file_model.get_file_versions(file.key, env) or {}
        file_actions = self._action_factory.get_actions(
                                        file,
                                        file_versions, 
                                        env,
                                        workfiles_visible=self._ui.browser.work_files_visible, 
                                        publishes_visible=self._ui.browser.publishes_visible
                                        )
                                                    
        if not file_actions:
            return

        # build the context menu:
        context_menu = QtGui.QMenu(self.sender())
        self._populate_open_menu(context_menu, file, env, file_actions[1:])
        
        # map the point to a global position:
        pnt = self.sender().mapToGlobal(pnt)
        
        # finally, show the context menu:
        context_menu.exec_(pnt)

    def _populate_open_menu(self, menu, file, env, file_actions):
        """
        """
        add_separators = False
        for action in file_actions:
            if isinstance(action, SeparatorFileAction):
                if add_separators:
                    menu.addSeparator()
                    
                # ensure that we only add separators after at least one action item and
                # never more than one!
                add_separators = False
            else:
                q_action = QtGui.QAction(action.label, menu)
                slot = lambda a=action, f=file, e=env: self._on_open_action_triggered(a, f, e)
                q_action.triggered[()].connect(slot)
                menu.addAction(q_action)
                add_separators = True      
        
    def _on_open(self):
        """
        """
        if not self._default_open_action or not self._selected_file:
            return
        
        self._on_open_action_triggered(self._default_open_action, 
                                       self._selected_file,
                                       self._selected_file_env)

    def _on_open_action_triggered(self, action, file, env):
        """
        """
        if (not action
            or not file
            or not self._file_model):
            # can't do anything!
            return
        
        # get the item info for the selected item:
        file_versions = self._file_model.get_file_versions(file.key, env) or {}
        
        # emit signal to perform the default action.  This may result in the dialog
        # being closed so no further work should be attempted after this call
        self.perform_action.emit(action, file, file_versions, env)

    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()










