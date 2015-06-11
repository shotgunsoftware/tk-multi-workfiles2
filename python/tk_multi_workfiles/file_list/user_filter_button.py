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

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from ..user_cache import g_user_cache

from .user_filter_menu import UserFilterMenu

class UserFilterButton(QtGui.QPushButton):
    """
    """
    users_selected = QtCore.Signal(object)# list of users
    
    def __init__(self, parent=None):
        """
        """
        QtGui.QPushButton.__init__(self, parent)

        users_menu = UserFilterMenu(self)
        users_menu.users_selected.connect(self._on_menu_users_selected)
        self.setMenu(users_menu)
        self._update()

    #@property
    def _get_selected_users(self):
        return self.menu().selected_users
    #selected_users.setter
    def _set_selected_users(self, users):
        self.menu().selected_users = users
        self._update()
    selected_users = property(_get_selected_users, _set_selected_users)

    #@property
    def _get_available_users(self):
        return self.menu().available_users
    # available_users.setter
    def _set_available_users(self, users):
        self.menu().available_users = users
        self._update()
    available_users = property(_get_available_users, _set_available_users)

    def _on_menu_users_selected(self, users):
        """
        """
        self.users_selected.emit(users)
        self._update()

    def _update(self):
        """
        """
        USER_STYLE_NONE = "none"
        USER_STYLE_CURRENT = "current"
        USER_STYLE_OTHER = "other"
        USER_STYLE_ALL = "all"

        # figure out the style to use:
        user_style = USER_STYLE_NONE
        if self.menu().current_user_selected:
            if self.menu().other_users_selected:
                user_style = USER_STYLE_ALL
            else:
                user_style = USER_STYLE_CURRENT
        elif self.menu().other_users_selected:
            user_style = USER_STYLE_OTHER

        # set the property on the filter btn:
        self.setProperty("user_style", user_style)

        # unpolish/repolish to update the style sheet:
        self.style().unpolish(self)
        self.ensurePolished()
        self.repaint()