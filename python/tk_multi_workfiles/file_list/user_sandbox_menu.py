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
Menu that presents a list of users representing sandboxes in the file system (if used in the templates).
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

class UserSandboxMenu(QtGui.QMenu):
    """
    """
    users_selected = QtCore.Signal(object)# list of users
    
    class _User(object):
        def __init__(self, user, action=None):
            self.user = user
            self.action = action
    
    def __init__(self, parent=None):
        """
        """
        QtGui.QMenu.__init__(self, parent)
        
        app = sgtk.platform.current_bundle()
        self._current_user = sgtk.util.get_current_user(app.sgtk)
        self._current_user_id = self._current_user["id"] if self._current_user else None

        self._available_users = {}
        self._checked_user_ids = set([self._current_user_id])

        # build the base menu - this won't change:
        menu_action = QtGui.QWidgetAction(self)
        menu_label = QtGui.QLabel("<i>Choose Who To Display Files For</i>", self)
        ss = "QLabel {margin: 3px;}"
        menu_label.setStyleSheet(ss)
        menu_action.setDefaultWidget(menu_label)
        self.addAction(menu_action)
        self.addSeparator()

        action = QtGui.QAction("Show My Files", self)
        action.setCheckable(True)
        action.setChecked(True)
        toggled_slot = lambda toggled, uid=self._current_user_id: self._on_user_toggled(uid, toggled)
        action.toggled.connect(toggled_slot)
        self.addAction(action)

        self._all_users_action = QtGui.QAction("Show Files For All Other Users", self)
        self._all_users_action.setCheckable(True)
        self._all_users_action.toggled.connect(self._on_all_other_users_toggled)
        self.addAction(self._all_users_action)

        menu_action = QtGui.QWidgetAction(self)
        menu_label = QtGui.QLabel("<i>Other Users:</i>", self)
        ss = "QLabel {margin: 3px;margin-top: 6px;}"
        menu_label.setStyleSheet(ss)
        menu_action.setDefaultWidget(menu_label)
        self.addAction(menu_action)
        self.addSeparator()

    @property
    def current_user_selected(self):
        """
        """
        return self._current_user_id in self._checked_user_ids

    @property
    def other_users_selected(self):
        """
        """
        selected_user_ids = self._checked_user_ids & set(self._available_users.keys())
        return (len(selected_user_ids) > 1 
                or (len(selected_user_ids) == 1 and next(iter(selected_user_ids)) != self._current_user_id)) 

    def populate_users(self, users):
        """
        """
        # compile a list of users with existing actions if they have them:
        available_users = {}
        user_names_and_ids = []
        for user in users:
            if not user:
                continue

            user_name = user["name"]
            user_id = user["id"]

            if user_id == self._current_user_id:
                # don't add current user to list of other users!
                continue

            user_details = self._available_users.get(user_id)
            if user_details is None:
                # new user not currently in the menu:
                user_details = UserSandboxMenu._User(user)

            available_users[user_id] = user_details
            user_names_and_ids.append((user_name, user_id))

        # remove menu items for users that are no longer in the list:
        user_ids_to_remove = set(self._available_users.keys()) - set(available_users.keys())
        for id in user_ids_to_remove:
            self.removeAction(self._available_users[id].action)

        # sort list of users alphabetically:
        user_names_and_ids.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()) or cmp(x[1], y[1]))

        # add menu items for users as needed:
        all_users_checked = self._all_users_action.isChecked()
        users_changed = False
        actions_to_insert = []
        for user_name, user_id in user_names_and_ids:
            user_details = available_users.get(user_id)
            if user_details.action:
                # already have an action so insert any actions to insert before it:
                for action in actions_to_insert:
                    self.insertAction(user_details.action, action)
                actions_to_insert = []
                continue

            # need to create a new action:
            action = QtGui.QAction(user_name, self)
            action.setCheckable(True)
            toggled_slot = lambda toggled, uid=user_id: self._on_user_toggled(uid, toggled)
            action.toggled.connect(toggled_slot)

            # Figure out if the user should be checked:
            if user_id in self._checked_user_ids or all_users_checked:
                self._checked_user_ids.add(user_id)
                action.setChecked(True)
                users_changed = True

            # keep track of the new action:
            user_details.action = action
            actions_to_insert.append(action)

        # if there are any actions left to insert then append them at the end of the menu:
        for action in actions_to_insert:
            self.addAction(action)

        # update list of available users (the ones with menu items)
        self._available_users = available_users

        # update checked state of all users action:
        self._update_all_users_checked_state()

        if users_changed:
            # list of selected users has changed so emit changed signal:
            self._emit_users_selected()

    def clear(self):
        """
        """
        # clearing this menu just clears the list of available users:
        for user_details in self._available_users.values():
            self.removeAction(user_details.action)
        self._available_users = {}

    def mousePressEvent(self, event):
        """
        """
        active_action = self.activeAction()
        if active_action and active_action.isCheckable():
            active_action.toggle()
            return True
        else:
            QtGui.QMenu.mousePressEvent(self, event)

    def _on_user_toggled(self, user_id, toggled):
        """
        """
        users_changed = False
        if toggled:
            if user_id not in self._checked_user_ids:
                self._checked_user_ids.add(user_id)
                users_changed = True
        else:
            if user_id in self._checked_user_ids:
                self._checked_user_ids.remove(user_id)
                users_changed = True

        # make sure that the 'all users' checkbox is up-to-date:
        self._update_all_users_checked_state()

        if users_changed:
            self._emit_users_selected()

    def _update_all_users_checked_state(self):
        """
        """
        if not self._available_users:
            return

        all_checked = True
        for user_details in self._available_users.values():
            if not user_details.action.isChecked():
                all_checked = False

        if self._all_users_action.isChecked() != all_checked:
            signals_blocked = self._all_users_action.blockSignals(True)
            try:
                self._all_users_action.setChecked(all_checked)
            finally:
                self._all_users_action.blockSignals(signals_blocked)

    def _on_all_other_users_toggled(self, toggled):
        """
        """
        signals_blocked = self.blockSignals(True)
        users_changed = False
        try:
            # toggle all other user actions:
            for user_details in self._available_users.values():
                if user_details.action.isChecked() != toggled:
                    users_changed= True
                    user_details.action.setChecked(toggled)
        finally:
            self.blockSignals(signals_blocked)

        if users_changed:
            self._emit_users_selected()

    def _emit_users_selected(self):
        """
        """
        selected_user_ids = self._checked_user_ids & set(self._available_users.keys())
        users = [self._available_users[id].user for id in selected_user_ids]
        if self._current_user_id in self._checked_user_ids:
            users = [self._current_user] + users
        self.users_selected.emit(users)