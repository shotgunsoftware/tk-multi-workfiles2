# Copyright (c) 2013 Shotgun Software Inc.
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

class UserCache(object):
    """
    A cache of user information retrieved from Shotgun as needed
    """    
    def __init__(self, app):
        """
        Construction
        """
        self.__app = app
        self.__user_details_by_login = {}
        self.__user_details_by_id = {}
        
        self.__sg_fields = ["id", "type", "email", "login", "name", "image"]
    
    def get_user_details_for_id(self, id):
        """
        Get the user details for the specified user entity id.
        
        :param id:  The entity id of the user whose details should be returned
        :returns:   A Shotgun entity dictionary for the user if found, otherwise {}
        """
        return self.get_user_details_for_ids([id]).get(id)
    
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
            details = self.__user_details_by_id.get(user_id)
            if details:
                user_details[id] = details
            elif details == None:
                # never looked user up before so add to list to find:
                users_to_fetch.add(user_id)
             
        if users_to_fetch:
            # get user details from shotgun:
            sg_users = []
            try:
                sg_users = self.__app.shotgun.find("HumanUser", [["id", "in"] + list(users_to_fetch)], self.__sg_fields)
            except:
                sg_users = []
                
            # add found users to look-ups:
            users_found = set()
            for sg_user in sg_users:
                user_id = sg_user.get("id")
                if user_id not in users_to_fetch:
                    continue
                self.__user_details_by_id[user_id] = sg_user
                self.__user_details_by_login[sg_user["login"]] = sg_user
                users_found.add(user_id)
                
                user_details[user_id] = sg_user
        
            # and fill in any blanks so we don't bother searching again:
            for user in users_to_fetch:
                if user_id not in users_found:
                    # store empty dictionary to differenctiate from 'None'
                    self.__user_details_by_id[user_id] = {}
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
            return self.__get_user_details_for_login(login_name)
        
        return None
    
    def __get_user_details_for_login(self, login_name):
        """
        Get the shotgun HumanUser entry for the specified login name
        
        :param login_name:  The login name of the user to find
        :returns:           A Shotgun entity dictionary for the HumanUser entity found
        """
        # first look to see if we've already found it:
        sg_user = self.__user_details_by_login.get(login_name)
        if not sg_user:
            try:
                sg_user = self.__app.shotgun.find_one("HumanUser", [["login", "is", login_name]], self.__sg_fields)
            except:
                sg_user = {}
            self.__user_details_by_login[login_name] = sg_user
            if sg_user:
                self.__user_details_by_id[sg_user["id"]] = sg_user
        return sg_user
    
    