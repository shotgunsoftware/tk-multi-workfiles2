# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Qt widget that presents the user with a list of entities
so that they can choose a context to work in.
"""
import sgtk

from .actions.context_change_action import ContextChangeAction
from .file_form_base import FileFormBase
from .ui.file_open_form import Ui_FileOpenForm


class ContextChangeForm(FileFormBase):
    def __init__(self, parent=None):
        super(ContextChangeForm, self).__init__(parent)

        self._context_change_env = None

        try:
            # doing this inside a try-except to ensure any exceptions raised don't
            # break the UI and crash the dcc horribly!
            self._do_init()
        except Exception:
            app = sgtk.platform.current_bundle()
            app.log_exception("Unhandled exception during Form construction!")

    def init_ui_file(self):
        """
        Returns the ui class to use, required by the base class.
        """
        return Ui_FileOpenForm()

    def _do_init(self):
        """ """
        super(ContextChangeForm, self)._do_init()

        # start by disabling buttons:
        self._ui.open_btn.hide()
        self._ui.new_file_btn.hide()
        self._ui.change_ctx_btn.setEnabled(False)
        self._ui.open_options_btn.hide()

        # hook up signals on controls:
        self._ui.change_ctx_btn.clicked.connect(self._on_context_change)
        self._ui.browser.task_double_clicked.connect(self._on_context_change)

        self._ui.browser.set_models(
            self._my_tasks_model,
            self._entity_models,
            None,
        )

        # initialize the browser widget:
        app = sgtk.platform.current_bundle()
        self._ui.browser.select_work_area(app.context)

    def _on_browser_work_area_changed(self, entity, breadcrumbs):
        """
        Slot triggered whenever the work area is changed in the browser.
        """
        env_details = super(ContextChangeForm, self)._on_browser_work_area_changed(
            entity, breadcrumbs
        )

        self._update_change_context_btn(env_details)

    def _update_change_context_btn(self, env):
        """
        Updates the current selected context, and updates the context change button state.
        When no environment is gathered from the context change button is disabled.
        """
        self._context_change_env = env
        if env:
            self._ui.change_ctx_btn.setEnabled(True)
        else:
            self._ui.change_ctx_btn.setEnabled(False)

    def _on_context_change(self, *_args):
        """
        Calls the context change action which will change the current engine's context and close the dialog.
        """
        context_change_action = ContextChangeAction(self._context_change_env)

        self._perform_action(context_change_action)
