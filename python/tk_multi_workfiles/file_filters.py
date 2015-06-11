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
Collection of filters to be used when filtering files in the file views.
"""

import sgtk
from sgtk.platform.qt import QtCore

from .user_cache import g_user_cache

class FileFilters(QtCore.QObject):
    """
    Implementation of the FileFilters class
    """
    # signal emitted whenever something in the filters is changed
    changed = QtCore.Signal()
    # signal emitted whenever the available users are changed
    available_users_changed = QtCore.Signal(object)# list of users
    # signal emitted whenever the users changed:
    users_changed = QtCore.Signal(object)# list of users
    
    def __init__(self, parent=None):
        """
        Construction

        :param parent:  The parent QObject
        """
        QtCore.QObject.__init__(self, parent)
        
        self._show_all_versions = False
        self._filter_reg_exp = QtCore.QRegExp()
        self._available_users = [g_user_cache.current_user] if g_user_cache.current_user else []
        self._users = [g_user_cache.current_user] if g_user_cache.current_user else []

    #@property
    def _get_show_all_versions(self):
        return self._show_all_versions
    #@show_all_versions.setter
    def _set_show_all_versions(self, show):
        if show != self._show_all_versions:
            self._show_all_versions = show
            self.changed.emit()
    show_all_versions=property(_get_show_all_versions, _set_show_all_versions)

    #@property filter_reg_exp
    def _get_filter_reg_exp(self):
        return self._filter_reg_exp
    #@filter_reg_exp.setter
    def _set_filter_reg_exp(self, value):
        if value != self._filter_reg_exp:
            self._filter_reg_exp = value
            self.changed.emit()
    filter_reg_exp = property(_get_filter_reg_exp, _set_filter_reg_exp)

    #@property
    def _get_available_users(self):
        return self._available_users
    #available_users.setter
    def _set_available_users(self, users):
        current_user_ids = set([u["id"] for u in self._available_users if u])
        new_user_ids = set([u["id"] for u in users if u])
        if new_user_ids != current_user_ids:
            self._available_users = [u for u in users if u]
            self.available_users_changed.emit(self._available_users)

            # also, update user ids, removing any that are no longer in
            # the list of available user ids:
            self._set_users(self._users)
    available_users = property(_get_available_users, _set_available_users)

    #@property
    def _get_users(self):
        return self._users
    #users.setter
    def _set_users(self, users):
        current_user_ids = set([u["id"] for u in self._users if u])
        available_user_ids = set([u["id"] for u in self._available_users])
        new_user_ids = set([u["id"] for u in users if u]) & available_user_ids
        if new_user_ids != current_user_ids:
            self._users = [u for u in users if u and u["id"] in new_user_ids]
            self.users_changed.emit(self._users)
            self.changed.emit()
    users = property(_get_users, _set_users)




