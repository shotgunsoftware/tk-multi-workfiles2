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
QPushButton containing a menu that allows selection of users from a list of available users.  The button
updates it's icon depending on the current selection in the menu.
"""

from sgtk.platform.qt import QtCore, QtGui

from .user_filter_menu import UserFilterMenu


class UserFilterButton(QtGui.QPushButton):
    """
    Button that when pressed will show the list of user sandboxes available.
    """

    users_selected = QtCore.Signal(object)# list of users

    _USER_STYLE_NONE = "none"
    _USER_STYLE_CURRENT = "current"
    _USER_STYLE_OTHER = "other"
    _USER_STYLE_ALL = "all"

    def __init__(self, parent):
        """
        Constructor.

        :param parent: Parent widget.
        """
        QtGui.QPushButton.__init__(self, parent)

        users_menu = UserFilterMenu(self)
        users_menu.users_selected.connect(self._on_menu_users_selected)
        self.setMenu(users_menu)
        self._update()

    # @property
    def _get_selected_users(self):
        """
        Retrieves the list of selected users in the user filter menu.

        :returns: List of selected users entities.
        """
        return self.menu().selected_users

    # selected_users.setter
    def _set_selected_users(self, users):
        """
        Sets the lists of users selected in the user filter menu.

        :param users: List of user entities.
        """
        self.menu().selected_users = users
        self._update()
    selected_users = property(_get_selected_users, _set_selected_users)

    # @property
    def _get_available_users(self):
        """
        Retrieves the list of users available for selection in the user filter menu.

        :returns: List of available users entities.
        """
        return self.menu().available_users

    # available_users.setter
    def _set_available_users(self, users):
        """
        Sets the list of users available for selection in the user filter menu.

        :users users: List of user entities.
        """
        self.menu().available_users = users
        self._update()
    available_users = property(_get_available_users, _set_available_users)

    def _on_menu_users_selected(self, users):
        """
        Called whenever the selection changes in the user filter menu.

        :params users: List of users that are selected.
        """
        self.users_selected.emit(users)
        self._update()

    def showEvent(self, event):
        """
        Ensures the widget look is updated when it is enabled or disabled.

        :param event: QtCore.QShowEvent object.
        """
        self._update()
        return QtGui.QPushButton.showEvent(self, event)

    def changeEvent(self, event):
        """
        Ensures the widget look is updated when it is enabled or disabled.

        :param event: QtCore.QEvent object.
        """
        if event.type() == QtCore.QEvent.EnabledChange:
            self._update()
        return QtGui.QPushButton.changeEvent(self, event)

    def _update(self):
        """
        Updates the status of the button.
        """
        # figure out the style to use:
        user_style = self._USER_STYLE_NONE
        if self.menu().isEnabled():
            if self.menu().current_user_selected:
                if self.menu().other_users_selected:
                    user_style = self._USER_STYLE_ALL
                else:
                    user_style = self._USER_STYLE_CURRENT
            elif self.menu().other_users_selected:
                user_style = self._USER_STYLE_OTHER

        # set the property on the filter btn:
        self.setProperty("user_style", user_style)

        # unpolish/repolish to update the style sheet:
        self.style().unpolish(self)
        self.ensurePolished()
        self.repaint()
