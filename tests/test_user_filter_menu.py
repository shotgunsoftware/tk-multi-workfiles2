# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

from tank_test.tank_test_base import TankTestBase
from tank_test.tank_test_base import setUpModule  # noqa

import sgtk
from tank_test.tank_test_base import SealedMock


class TestUserFilterMenu(TankTestBase):
    """
    Baseclass for all Workfiles2 unit tests.

    This sets up the fixtures, starts an engine and provides
    the following members:

    - self.engine: The test engine running
    - self.app: The test app running
    - self.tk_multi_workfiles: The tk_multi_workfiles module

    """

    def setUp(self):
        """
        Fixtures setup
        """
        super(TestUserFilterMenu, self).setUp()

        sgtk.set_authenticated_user(SealedMock(login="jeff"))
        self.jeff = self.mockgun.create("HumanUser", {"name": "Jeff", "login": "jeff"})
        self.francis = self.mockgun.create(
            "HumanUser", {"name": "Francis", "login": "Francis"}
        )
        self.rob = self.mockgun.create("HumanUser", {"name": "Rob", "login": "rob"})

        self.setup_fixtures()

        # Add these to mocked shotgun
        self.add_to_sg_mock_db([self.project])

        # run folder creation for the project
        self.tk.create_filesystem_structure(self.project["type"], self.project["id"])

        # now make a context
        context = self.tk.context_from_entity(self.project["type"], self.project["id"])

        # and start the engine
        self.engine = sgtk.platform.start_engine("tk-testengine", self.tk, context)
        # This ensures that the engine will always be destroyed.
        self.addCleanup(self.engine.destroy)

        # Ensure a QApplication instance for the tests.
        self._qapp = sgtk.platform.qt.QtGui.QApplication.instance()
        if not self._qapp:
            self._qapp = sgtk.platform.qt.QtGui.QApplication([])

        self.app = self.engine.apps["tk-multi-workfiles2"]
        self.tk_multi_workfiles = self.app.import_module("tk_multi_workfiles")

        # This is specific to this test, everything above should be refactored
        # into a Workfiles2TestBase class.
        self.UserFilterMenu = (
            self.tk_multi_workfiles.file_list.user_filter_menu.UserFilterMenu
        )

    def test_menu(self):
        self._menu = self.UserFilterMenu(self._qapp.activeWindow())

        self._menu.available_users = [self.jeff, self.francis, self.rob]

        assert len(self._menu.actions()) == 8
        # Grab some widgets.
        self._show_my_files_action = self._menu.actions()[2]
        self._show_files_for_others_action = self._menu.actions()[3]
        self._francis_action = self._menu.actions()[6]
        self._rob_action = self._menu.actions()[7]
        assert self._show_my_files_action.text() == "Show My Files"
        assert (
            self._show_files_for_others_action.text()
            == "Show Files For All Other Users"
        )
        assert self._francis_action.text() == "Francis"
        assert self._rob_action.text() == "Rob"

        # First, try to toggle the state of the UI via calls on the API.
        self._menu.selected_users = [self.jeff]

        self._test_state(
            current=True, others=False, jeff=True, francis=False, rob=False
        )

        self._menu.selected_users = [self.rob]
        self._test_state(
            current=False, others=True, jeff=False, francis=False, rob=True
        )

        self._menu.selected_users = [self.rob, self.jeff]
        self._test_state(current=True, others=True, jeff=True, francis=False, rob=True)

        self._menu.selected_users = []
        self._test_state(
            current=False, others=False, jeff=False, francis=False, rob=False
        )

        # Then, try to toggle the state by triggering actions
        self._show_my_files_action.toggle()
        self._assert_selected(self.jeff)
        self._test_state(
            current=True, others=False, jeff=True, francis=False, rob=False
        )

        self._francis_action.toggle()
        self._assert_selected(self.jeff, self.francis)

        self._test_state(current=True, others=True, jeff=True, francis=True, rob=False)

    def _test_state(self, current, others, jeff, francis, rob):
        assert self._menu.current_user_selected is current
        assert self._menu.other_users_selected is others
        assert self._show_my_files_action.isChecked() is jeff
        assert self._francis_action.isChecked() is francis
        assert self._rob_action.isChecked() is rob

    def _assert_selected(self, *users):
        assert [u["id"] for u in self._menu.selected_users] == [u["id"] for u in users]
