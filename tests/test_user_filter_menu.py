# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank_test.tank_test_base import setUpModule  # noqa

from workfiles2_test_base import Workfiles2TestBase


class TestUserFilterMenu(Workfiles2TestBase):
    """
    Test the user filter menu that allows to select which sandbox to display in the
    file browser.
    """

    def setUp(self):
        """
        Fixtures setup
        """
        super(TestUserFilterMenu, self).setUp()

        # This is specific to this test, everything above should be refactored
        # into a Workfiles2TestBase class.
        UserFilterMenu = (
            self.tk_multi_workfiles.file_list.user_filter_menu.UserFilterMenu
        )

        # Create the menu and set all available users, taken from the base class.
        self._menu = UserFilterMenu(None)
        self._menu.available_users = [self.jeff, self.francis, self.rob]

        # This should have build a menu with 8 items.
        assert len(self._menu.actions()) == 8

        # We'll grab some of the actions from that menu so we can activate them
        # later on and introspect their state.
        self._show_my_files_action = self._menu.actions()[2]
        self._show_files_for_others_action = self._menu.actions()[3]

    def _dump_menu_state(self):
        """
        Dump menu state. Usefull for debugging"
        """
        for act in self._menu.actions():
            print(
                "Text: {0}, checked: {1}, enabled: {2}".format(
                    act.text(), act.isChecked(), act.isEnabled()
                )
            )

    def _find_action(self, name):
        """
        Find an action based on it's name.

        :param str name: Text of the QAction to search.

        :returns: A QAction or None if no action is found.
        """
        for act in self._menu.actions():
            if act.text() == name:
                return act
        return None

    @property
    def _francis_action(self):
        """
        :returns: QAction for item Francis
        """
        return self._find_action("Francis")

    @property
    def _rob_action(self):
        """
        :returns: QAction for item Rob
        """
        return self._find_action("Rob")

    def test_ordering(self):
        """
        Ensure the ordering of the users is as expected.
        """
        assert self._show_my_files_action.text() == "Show My Files"
        assert (
            self._show_files_for_others_action.text()
            == "Show Files For All Other Users"
        )
        assert self._menu.actions()[-2].text() == "Francis"
        assert self._menu.actions()[-1].text() == "Rob"

    def test_user_selection(self):
        """
        Validate user selection and menu state.
        """
        # First, try to toggle the state of the UI via calls on the API.
        # Selecting Jeff should set the current user selected attribute
        # and select his menu item.
        self._menu.selected_users = [self.jeff]
        self._test_state(
            current=True, others=False, jeff=True, francis=False, rob=False
        )

        # Selecting Rob should reset the current user selected attribute, set
        # the other selected attribute and select the Rob menu item.
        self._menu.selected_users = [self.rob]
        self._test_state(
            current=False, others=True, jeff=False, francis=False, rob=True
        )

        # Selecting Jeff and Rob should set both attributes and both users menu item.
        self._menu.selected_users = [self.rob, self.jeff]
        self._test_state(current=True, others=True, jeff=True, francis=False, rob=True)

        # Clearing the selection should disable everything.
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

        # Jeff is currently selected, and now Francis will be too
        self._francis_action.toggle()
        self._assert_selected(self.jeff, self.francis)
        self._test_state(current=True, others=True, jeff=True, francis=True, rob=False)

    def test_removing_users(self):
        """
        Ensure that removing users update the menu accordingly.
        """
        # Removing Francis from selected and available users should remove him
        # from the menu
        self._menu.selected_users = [self.rob]
        self._menu.available_users = [self.rob]
        # Current user is always present, but Francis is gone from the menu.
        self._test_state(current=False, others=True, jeff=False, francis=None, rob=True)

        # Removing Rob from available, but it was checked, so it should still
        # be checked, but disabled.
        self._menu.available_users = []
        # ... so menu item remains, but is disabled.
        self._test_state(
            current=False, others=False, jeff=False, francis=None, rob=True
        )
        assert self._rob_action.isEnabled() is False
        assert len(self._menu.actions()) == 7

    def _test_state(self, current, others, jeff, francis, rob):
        """
        Test the state of the menu.

        :param bool current: Asserts that menu.current_user_selected is True is current
        :param bool others: Asserts that menu.other_users_selected is others
        :param bool jeff: Asserts that Show My Files is checked is not.
        :param bool francis: Asserts that Francis is checked is not. If None, QAction must be missing
        :param bool rob: Asserts that Rob is checked is not. If None, QAction must be missing
        """
        assert self._menu.current_user_selected is current
        assert self._menu.other_users_selected is others
        assert self._show_my_files_action.isChecked() is jeff
        if type(francis) == bool:
            assert self._francis_action.isChecked() is francis
        else:
            assert self._francis_action is None
        if type(rob) == bool:
            assert self._rob_action.isChecked() is rob
        else:
            assert self._rob_action is None

    def _assert_selected(self, *users):
        """
        Assert that the passed in users are selected.

        :params *args users: *args of user entity dict that should be selected.
        """
        assert [u["id"] for u in self._menu.selected_users] == [u["id"] for u in users]
