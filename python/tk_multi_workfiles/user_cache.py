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
Implementation of the user cache storing Shotgun user information
"""
import os
import sys
import sgtk

from .util import Threaded

class UserCache(Threaded):
    """
    A cache of user information retrieved from Shotgun as needed
    """
    def __init__(self):
        """
        Construction
        """
        Threaded.__init__(self)
        self._app = sgtk.platform.current_bundle()
        self._current_user = sgtk.util.get_current_user(self._app.sgtk)

        self._user_details_by_login = {}
        self._user_details_by_id = {}

        self._sg_fields = ["id", "type", "email", "login", "name", "image"]

    @property
    def current_user(self):
        """
        :returns:    The Shotgun dictionary representing the current user
        """
        return self._current_user

    def get_user_details_for_id(self, user_id):
        """
        Get the user details for the specified user entity id.

        :param user_id: The entity id of the user whose details should be returned
        :returns:       A Shotgun entity dictionary for the user if found, otherwise {}
        """
        return self.get_user_details_for_ids([user_id]).get(id)

    def get_user_details_for_ids(self, ids):
        """
        Get the user details for all users represented by the list of supplied entity ids

        :param ids: The entity ids of the users whose details should be returned
        :returns:   A dictionary of id->Shotgun entity dictionary containing one entry
                    for each user requested.  An empty dictionary will be returned for users
                    that couldn't be found!
        """
        if not ids:
            # nothing to look for!
            return {}

        # first, check for cached user info for ids:
        user_details = {}
        users_to_fetch = set()
        for user_id in ids:
            details = self._get_user_for_id(user_id)
            if details:
                user_details[user_id] = details
            elif details == None:
                # never looked user up before so add to list to find:
                users_to_fetch.add(user_id)

        if users_to_fetch:
            # get user details from shotgun:
            sg_users = []
            try:
                sg_users = self._app.shotgun.find("HumanUser", [["id", "in"] + list(users_to_fetch)], self._sg_fields)
            except:
                sg_users = []

            # add found users to look-ups:
            users_found = set()
            for sg_user in sg_users:
                user_id = sg_user.get("id")
                if user_id not in users_to_fetch:
                    continue
                self._cache_user(sg_user["login"], user_id, sg_user)
                users_found.add(user_id)

                user_details[user_id] = sg_user

            # and fill in any blanks so we don't bother searching again:
            for user_id in users_to_fetch:
                if user_id not in users_found:
                    # store empty dictionary to differentiate from 'None'
                    self._cache_user(None, user_id, {})
                    user_details[user_id] = {}

        return user_details

    def get_file_last_modified_user(self, path):
        """
        Get the user details of the last person to modify the specified file.  Note, this currently
        doesn't work on Windows as Windows doesn't provide this information as standard

        :param path:    The path to find the last modified user for
        :returns:       A  Shotgun entity dictionary for the HumanUser that last modified the path
        """

        login_name = None
        if sys.platform == "win32":
            # TODO: add windows support..
            pass
        else:
            try:
                from pwd import getpwuid
                login_name = getpwuid(os.stat(path).st_uid).pw_name
            except:
                pass

        if login_name:
            sg_user = self._get_user_details_for_login(login_name)
            return sg_user

        return None

    def _get_user_details_for_login(self, login_name):
        """
        Get the shotgun HumanUser entry for the specified login name

        :param login_name:  The login name of the user to find
        :returns:           A Shotgun entity dictionary for the HumanUser entity found
        """
        # first look to see if we've already found the user:
        sg_user = self._get_user_for_login(login_name)
        if not sg_user:
            # have to do a Shotgun lookup:
            try:
                sg_user = self._app.shotgun.find_one("HumanUser", [["login", "is", login_name]], self._sg_fields)
                # handle sg_user being None
                sg_user = sg_user or {}
            except Exception, e:
                # this isn't critical so just log as debug
                self._app.log_debug("Failed to retrieve Shotgun user for login '%s': %s" % (login_name, e))

            # cache the sg user so we don't have to look for it again
            self._cache_user(login_name, sg_user.get("id"), sg_user)

        return sg_user

    @Threaded.exclusive
    def _get_user_for_id(self, user_id):
        """
        Thread-safe mechanism to get the cached user for the specified user id

        :param user_id: Id of the user to find
        :returns:       A Shotgun entity dictionary representing the user if found in the 
                        cache, otherwise None
        """
        return self._user_details_by_id.get(user_id)

    @Threaded.exclusive
    def _get_user_for_login(self, login):
        """
        Thread-safe mechanism to get the cached user for the specified user login

        :param login:   Shotgun login of the user to find
        :returns:       A Shotgun entity dictionary representing the user if found in the 
                        cache, otherwise None
        """
        return self._user_details_by_login.get(login)

    @Threaded.exclusive
    def _cache_user(self, login, user_id, details):
        """
        Thread-safe mechanism to add the specified user to the cache

        :param login:   Shotgun login of the user to add
        :param user_id: Id of the user to add
        :param details: Shotgun entity dictionary containing the details of the user to add
        """
        if login != None:
            self._user_details_by_login[login] = details
        if user_id != None:
            self._user_details_by_id[user_id] = details

# single global instance of the user cache
g_user_cache = UserCache()
    