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
from sgtk.platform.qt import QtGui

from .actions.file_action_factory import FileActionFactory
from .actions.action import SeparatorAction, ActionGroup
from .actions.file_action import FileAction
from .actions.new_file_action import NewFileAction

from .file_form_base import FileFormBase
from .ui.file_open_form import Ui_FileOpenForm

from .work_area import WorkArea
from .util import  get_template_user_keys


class FileOpenForm(FileFormBase):
    """
    UI for opening a publish or work file.  Presents a list of available files to the user
    so that they can choose one to open in addition to any other user-definable actions.
    """
    @property
    def exit_code(self):
        return self._exit_code

    def __init__(self, parent=None):
        """
        Construction
        """
        app = sgtk.platform.current_bundle()

        FileFormBase.__init__(self, parent)

        self._exit_code = QtGui.QDialog.Rejected

        self._new_file_env = None
        self._default_open_action = None

        self._navigating = False

        try:
            # doing this inside a try-except to ensure any exceptions raised don't
            # break the UI and crash the dcc horribly!
            self._do_init()
        except:
            app.log_exception("Unhandled exception during File Open Form construction!")

    def _do_init(self):
        """
        """
        app = sgtk.platform.current_bundle()

        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)

        # start by disabling buttons:
        self._ui.open_btn.setEnabled(False)
        self._ui.open_options_btn.setEnabled(False)

        # tmp - disable some controls that currently don't work!
        self._ui.open_options_btn.hide()

        # hook up signals on controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.open_btn.clicked.connect(self._on_open)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)

        self._ui.browser.file_context_menu_requested.connect(self._on_browser_context_menu_requested)

        self._ui.browser.create_new_task.connect(self._on_create_new_task)
        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(self._on_browser_file_double_clicked)
        self._ui.browser.work_area_changed.connect(self._on_browser_work_area_changed)
        self._ui.browser.step_filter_changed.connect(self._apply_step_filtering)

        self._ui.nav.navigate.connect(self._on_navigate)
        self._ui.nav.home_clicked.connect(self._on_navigate_home)

        # initialize the browser widget:
        self._ui.browser.show_user_filtering_widget(self._is_using_user_sandboxes())
        self._ui.browser.set_models(
            self._my_tasks_model,
            self._entity_models,
            self._file_model,
        )
        current_file = self._get_current_file()
        self._ui.browser.select_work_area(app.context)
        self._ui.browser.select_file(current_file, app.context)


    def _is_using_user_sandboxes(self):
        """
        Checks if any template is using user sandboxing in the current configuration.

        :returns: True is user sandboxing is used, False otherwise.
        """
        app = sgtk.platform.current_bundle()

        for t in app.sgtk.templates.itervalues():
            if get_template_user_keys(t):
                return True

        return False


    def closeEvent(self, event):
        """
        Called when the widget is being closed - do as much as possible here to help the GC

        :param event:   The close event
        """
        # clean up the browser:
        self._ui.browser.shut_down()

        # be sure to call the base clase implementation
        return FileFormBase.closeEvent(self, event)

    def _on_browser_file_selected(self, file, env):
        """
        """
        self._on_selected_file_changed(file, env)
        self._update_new_file_btn(env)

    def _on_browser_work_area_changed(self, entity, breadcrumbs):
        """
        Slot triggered whenever the work area is changed in the browser.
        """
        env_details = None
        if entity:
            # (AD) - we need to build a context and construct the environment details
            # instance for it but this may be slow enough that we should cache it!
            # Keep an eye on it and consider threading if it's noticeably slow!
            app = sgtk.platform.current_bundle()
            context = app.sgtk.context_from_entity_dictionary(entity)
            try:
                env_details = WorkArea(context)
            except sgtk.TankError:
                # We can ignore the error reporting here. The browser is already
                # updating it's various file views and they will display the same
                # error. Which is good, because file open dialog doesn't have a
                # widget dedicated to error reporting.
                env_details = None

        self._update_new_file_btn(env_details)

        if not self._navigating:
            destination_label = breadcrumbs[-1].label if breadcrumbs else "..."
            self._ui.nav.add_destination(destination_label, breadcrumbs)
        self._ui.breadcrumbs.set(breadcrumbs)

    def _on_browser_file_double_clicked(self, file, env):
        """
        """
        self._on_selected_file_changed(file, env)
        self._update_new_file_btn(env)
        self._on_open()

    def _on_navigate(self, breadcrumb_trail):
        """
        """
        if not breadcrumb_trail:
            return

        # awesome, just navigate to the breadcrumbs:
        self._ui.breadcrumbs.set(breadcrumb_trail)
        self._navigating = True
        try:
            self._ui.browser.navigate_to(breadcrumb_trail)
        finally:
            self._navigating = False

    def _on_navigate_home(self):
        """
        Navigate to the current work area
        """
        # navigate to the current work area in the browser:
        app = sgtk.platform.current_bundle()
        self._ui.browser.select_work_area(app.context)

    def _on_selected_file_changed(self, file, env):
        """
        """
        # get the available actions for this file:
        file_actions = self._get_available_file_actions(file, env)

        if not file_actions:
            # disable both the open and open options buttons:
            self._ui.open_btn.setEnabled(False)
            self._ui.open_options_btn.setEnabled(False)
            self._default_open_action = None
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
            self._populate_open_menu(menu, file_actions[1:])
        else:
            # just disable the button:
            self._ui.open_options_btn.setEnabled(False)

    def _update_new_file_btn(self, env):
        """
        """
        if env and NewFileAction.can_do_new_file(env):
            self._new_file_env = env
        else:
            self._new_file_env = None
        self._ui.new_file_btn.setEnabled(self._new_file_env is not None)

    def _on_browser_context_menu_requested(self, file, env, pnt):
        """
        """
        if not file:
            return

        # get the file actions:
        file_actions = self._get_available_file_actions(file, env)
        if not file_actions:
            return

        # build the context menu:
        context_menu = QtGui.QMenu(self.sender())
        self._populate_open_menu(context_menu, file_actions[1:])

        # map the point to a global position:
        pnt = self.sender().mapToGlobal(pnt)

        # finally, show the context menu:
        context_menu.exec_(pnt)

    def _get_available_file_actions(self, file_item, env):
        """
        Retrieves the actions for a given file.

        :param file_item: FileItem to retrieve the actions for.
        :param env: WorkArea instance representing the context for this particular file.

        :returns: List of Actions.
        """
        if not file_item or not env or not self._file_model:
            return []

        file_actions = FileActionFactory(
            env,
            self._file_model,
            workfiles_visible=self._ui.browser.work_files_visible,
            publishes_visible=self._ui.browser.publishes_visible
        ).get_actions(file_item)
        return file_actions

    def _populate_open_menu(self, menu, file_actions):
        """
        Creates menu entries based on a list of file actions.

        :param menu: Target menu for the entries.
        :param file_actions: List of Actions to add under the menu.
        """
        add_separators = False
        for action in file_actions:
            if isinstance(action, SeparatorAction):
                if add_separators:
                    menu.addSeparator()
                # ensure that we only add separators after at least one action item and
                # never more than one!
                add_separators = False
            elif isinstance(action, ActionGroup):
                # This is an action group, so we'll add the entries in a sub-menu.
                self._populate_open_menu(menu.addMenu(action.label), action.actions)
                add_separators = True
            else:
                q_action = QtGui.QAction(action.label, menu)
                slot = lambda a=action: self._perform_action(a)
                q_action.triggered[()].connect(slot)
                menu.addAction(q_action)
                add_separators = True

    def _on_open(self):
        """
        """
        if not self._default_open_action:
            return

        # perform the action - this may result in the UI being closed so don't do
        # anything after this call!
        self._perform_action(self._default_open_action)

    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()

    def _on_new_file(self):
        """
        """
        if not self._new_file_env or not NewFileAction.can_do_new_file(self._new_file_env):
            return

        new_file_action = NewFileAction(self._new_file_env)

        # perform the action - this may result in the UI being closed so don't do
        # anything after this call!
        self._perform_action(new_file_action)

    def _perform_action(self, action):
        """
        """
        if not action:
            return

        # some debug:
        app = sgtk.platform.current_bundle()
        if isinstance(action, FileAction) and action.file:
            app.log_debug("Performing action '%s' on file '%s, v%03d'"
                          % (action.label, action.file.name, action.file.version))
        else:
            app.log_debug("Performing action '%s'" % action.label)

        # execute the action:
        close_dialog = action.execute(self)

        # if this is successful then close the form:
        if close_dialog:
            self._exit_code = QtGui.QDialog.Accepted
            self.close()
        else:
            # refresh all models in case something changed as a result of
            # the action (especially important with custom actions):
            self._refresh_all_async()
