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
"""

from .file_action import FileAction, CustomFileAction
from .open_workfile_action import OpenAction, OpenWorkfileAction

class FileActionFactory(object):
    
    def __init__(self):
        """
        """
        pass
    
    def get_actions(self, file, file_versions, environment):
        """
        """
        actions = []
        
        # always add the generic 'open' action:
        actions.append(OpenAction())

        if file.is_local:
            # can open this file directly:
            # TODO: check user and version
            actions.append(OpenWorkfileAction())
        
        # and query for any custom actions:
        hook_custom_actions = []
        # TODO
        for action_dict in hook_custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("label") or name
            custom_action = CustomFileAction(name, label)
            actions.append(custom_action)
        
        return actions        
        