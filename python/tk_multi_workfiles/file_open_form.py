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
from .actions.new_file_action import NewFileAction

from .file_form_base import FileFormBase
from .ui.file_open_form import Ui_FileOpenForm

from .work_area import WorkArea
from .util import get_template_user_keys


class FileOpenForm(FileFormBase):
    """
    UI for opening a publish or work file.  Presents a list of available files to the user
    so that they can choose one to open in addition to any other user-definable actions.
    """

    def __init__(self, parent=None):
        """Construction"""

        super(FileOpenForm, self).__init__(parent)

        self._app = sgtk.platform.current_bundle()

        self._new_file_env = None
        self._default_open_action = None

        try:
            # doing this inside a try-except to ensure any exceptions raised don't
            # break the UI and crash the dcc horribly!
            self._do_init()
        except Exception:
            self._app.log_exception("Unhandled exception during Form construction!")

    def init_ui_file(self):
        """
        Returns the ui class to use, required by the base class.
        """
        return Ui_FileOpenForm()

    def _do_init(self):
        """ """
        super(FileOpenForm, self)._do_init()

        # start by disabling buttons:
        self._ui.change_ctx_btn.hide()
        self._ui.open_btn.setEnabled(False)
        self._ui.open_options_btn.setEnabled(False)
        # tmp - disable some controls that currently don't work!
        self._ui.open_options_btn.hide()

        self._ui.open_btn.clicked.connect(self._on_open)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)

        self._ui.browser.file_context_menu_requested.connect(
            self._on_browser_context_menu_requested
        )

        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(
            self._on_browser_file_double_clicked
        )

        # initialize the browser widget:
        self._ui.browser.show_user_filtering_widget(self._is_using_user_sandboxes())
        show_check_refs = self._app.get_setting("show_check_references_option", False)
        self._ui.browser.show_check_references_widget(show_check_refs)
        self._ui.browser.set_models(
            self._my_tasks_model,
            self._entity_models,
            self._file_model,
        )
        current_file = self._get_current_file()
        app = sgtk.platform.current_bundle()
        self._ui.browser.select_work_area(app.context)
        self._ui.browser.select_file(current_file, app.context)

    def _is_using_user_sandboxes(self):
        """
        Checks if any template is using user sandboxing in the current configuration.

        :returns: True is user sandboxing is used, False otherwise.
        """
        app = sgtk.platform.current_bundle()

        for t in app.sgtk.templates.values():
            if get_template_user_keys(t):
                return True

        return False

    def _on_browser_file_selected(self, file, env):
        """ """
        self._on_selected_file_changed(file, env)
        self._update_new_file_btn(env)

    def _on_browser_work_area_changed(self, entity, breadcrumbs):
        """
        Slot triggered whenever the work area is changed in the browser.
        """
        env_details = super(FileOpenForm, self)._on_browser_work_area_changed(
            entity, breadcrumbs
        )
        self._update_new_file_btn(env_details)

    def _on_browser_file_double_clicked(self, file, env):
        """ """
        self._on_selected_file_changed(file, env)
        self._update_new_file_btn(env)
        self._on_open()

    def _on_selected_file_changed(self, file, env):
        """ """
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
        """ """
        if env and NewFileAction.can_do_new_file(env):
            self._new_file_env = env
        else:
            self._new_file_env = None
        self._ui.new_file_btn.setEnabled(self._new_file_env is not None)

    def _on_browser_context_menu_requested(self, file, env, pnt):
        """ """
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
            publishes_visible=self._ui.browser.publishes_visible,
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
                q_action.triggered[()].connect(
                    lambda a=action, checked=False: self._perform_action(a)
                )
                menu.addAction(q_action)
                add_separators = True

    def _on_open(self):
        """ """
        if not self._default_open_action:
            return

        # perform the action - this may result in the UI being closed so don't do
        # anything after this call!
        self._perform_action(self._default_open_action)

    def _on_new_file(self):
        """ """
        if not self._new_file_env or not NewFileAction.can_do_new_file(
            self._new_file_env
        ):
            return

        new_file_action = NewFileAction(self._new_file_env)

        # perform the action - this may result in the UI being closed so don't do
        # anything after this call!
        self._perform_action(new_file_action)
