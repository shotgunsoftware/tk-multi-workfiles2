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
Qt widget that presents the user with a list of work files and publishes
so that they can choose one to open
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .actions.file_action import SeparatorFileAction
from .actions.file_action_factory import FileActionFactory
from .actions.new_file_action import NewFileAction

from .file_operation_form import FileOperationForm
from .ui.file_open_form import Ui_FileOpenForm

from .environment_details import EnvironmentDetails

from .breadcrumb_widget import Breadcrumb

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
        
        self._selected_file = None
        self._selected_file_env = None
        self._default_open_action = None
        
        self._navigating = False
        
        # create the action factory - this is used to generate actions
        # for the selected file
        self._action_factory = FileActionFactory()

        try:
            # doing this inside a try-except to ensure any exceptions raised don't 
            # break the UI and crash the dcc horribly!
            self._init(init_callback)
        except:
            app.log_exception("Unhandled exception during File Save Form construction!")

    def _init(self, init_callback):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)

        # start by dissabling buttons:
        self._ui.open_btn.setEnabled(False)
        self._ui.open_options_btn.setEnabled(False)

        # tmp - disable some controls that currently don't work!
        self._ui.open_options_btn.hide()
        #self._ui.history_btns.hide()
        #self._ui.breadcrumbs.hide()
            
        # hook up signals on controls:
        self._ui.browser.create_new_task.connect(self._on_create_new_task)
        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(self._on_browser_file_double_clicked)
        self._ui.browser.file_context_menu_requested.connect(self._on_browser_context_menu_requested)
        self._ui.browser.work_area_changed.connect(self._on_browser_work_area_changed)
        self._ui.browser.breadcrumbs_dropped.connect(self._on_browser_dropped_breadcrumbs)

        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.open_btn.clicked.connect(self._on_open)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)
        
        self._ui.nav.navigate.connect(self._on_navigate)
        self._ui.nav.home_clicked.connect(self._on_navigate_home)
        
        # initialize the browser widget:
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        env = EnvironmentDetails(app.context)
        current_file = self._get_current_file(env)
        self._ui.browser.initialize(env, current_file)

        # initialize the UI
        self._on_selected_file_changed()
        self._update_new_file_btn()

        # call init callback:
        if init_callback:
            init_callback(self)
        
    def select_entity(self, entity):
        """
        :param entity:  The entity or task to select in the current tree/my tasks view.  If it can't be found
                        then attempt to switch tabs if it can be found in a different tab! 
        """
        # TODO
        pass

    def _on_navigate(self, destination):
        """
        """
        if isinstance(destination, EnvironmentDetails):
            # add in some placeholder breadcrumbs that represent the environment context.
            # these will be replaced as soon as something is selected in the app (either manually
            # or by this process selecting something!)
            env = destination

            breadcrumbs = []
            #if env.context.project:
            #    breadcrumbs.append(Breadcrumb("<b>Project</b> %s" % env.context.project["name"]))
            if env.context.entity:
                breadcrumbs.append(Breadcrumb("<b>%s</b> %s" % (env.context.entity["type"], env.context.entity["name"])))
            if env.context.step:
                breadcrumbs.append(Breadcrumb("<b>Step</b> %s" % env.context.step["name"]))
            if env.context.task:
                breadcrumbs.append(Breadcrumb("<b>Task</b> %s" % env.context.task["name"]))

            self._ui.breadcrumbs.set(breadcrumbs)
            self._navigating = True
            try:
                self._ui.browser.select_environment(env)
            finally:
                self._navigating = False
        #else:
        #    self._ui.breadcrumbs.set(destination)
        #    signals_blocked = self._ui.browser.blockSignals(True)
        #    try:
        #        self._ui.browser.navigate_to_breadcrumbs(destination)
        #    finally:
        #        self._ui.browser.blockSignals(signals_blocked)

    def _on_navigate_home(self):
        """
        """
        app = sgtk.platform.current_bundle()
        env = EnvironmentDetails(app.context)
        self._on_navigate(env)

    def _on_browser_file_selected(self, file, env):
        """
        """
        self._selected_file = file
        self._selected_file_env = env
        self._on_selected_file_changed()
        self._update_new_file_btn()

    def _on_browser_dropped_breadcrumbs(self, breadcrumbs):
        """
        """
        self._ui.breadcrumbs.set(breadcrumbs)
            
    def _on_browser_work_area_changed(self, entity):
        """
        """
        #print "WORK AREA CHANGED: %s" % entity
        
        env_details = None
        if entity:
            # (AD) - we need to build a context and construct the environment details 
            # instance for it but this may be slow enough that we should thread it...
            # Keep an eye on it and consider threading if it's noticeably slow!
            app = sgtk.platform.current_bundle()
            context = app.sgtk.context_from_entity_dictionary(entity)
            env_details = EnvironmentDetails(context)
        
        self._selected_file_env = env_details
        self._update_new_file_btn()

        if not self._navigating:
            self._ui.nav.add_destination("Unknown", env_details)
    
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

    def _update_new_file_btn(self):
        """
        """
        if self._selected_file_env and NewFileAction.can_do_new_file(self._selected_file_env):
            self._ui.new_file_btn.setEnabled(True)
        else:
            self._ui.new_file_btn.setEnabled(False)

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

    def _on_new_file(self):
        """
        """
        if not self._selected_file_env or not NewFileAction.can_do_new_file(self._selected_file_env):
            return
        
        new_file_action = NewFileAction()
        
        # emit signal to perform the action.  This may result in the dialog
        # being closed so no further work should be attempted after this call
        self.perform_action.emit(new_file_action, None, None, self._selected_file_env)










