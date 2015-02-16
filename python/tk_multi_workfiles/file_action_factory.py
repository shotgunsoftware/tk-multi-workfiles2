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

from .file_action import FileAction

from .file_action import CustomFileAction
from .file_action import ShowWorkFileInFileSystemAction, ShowPublishInFileSystemAction, ShowPublishInShotgunAction

from .interactive_open_action import InteractiveOpenAction
from .open_workfile_action import OpenWorkfileAction

class FileActionFactory(object):
    
    def __init__(self):
        """
        """
        pass
    
    def get_actions(self, file, file_versions, environment):
        """
        """
        actions = []
        
        """
        Open publish:
        
        if 
        
        
        """
        
        
        """
        View latest Publish in Shotgun
        Open Publish Read-Only -> versions
        Open Work File -> versions

        Show work file in file system
        Show publish file in file system
        Show publish in Shotgun
        
        New file

    def _on_open_publish(self, publish_file, work_file):
    def _on_open_workfile(self, work_file, publish_file):
    def _on_open_previous_publish(self, file):
    def _on_open_previous_workfile(self, file):
    def _on_new_file(self):

        """
        
        # always add the interactive 'open' action.  This is the
        # default/generic open action that gets run whenever someone
        # double-clicks on a file or just hits the 'Open' button
        actions.append(InteractiveOpenAction())

        # now add explicit file operations based off the selection:
        if file.is_local:
            # can open this file directly:
            # TODO: check user and version
            actions.append(OpenWorkfileAction(not file.editable))
        
        # query for any custom actions:
        hook_custom_actions = []
        # TODO
        for action_dict in hook_custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("label") or name
            custom_action = CustomFileAction(name, label)
            actions.append(custom_action)
        
        # finally add the 'jump to' actions:
        if file.is_local:
            actions.append(ShowWorkFileInFileSystemAction())
        if file.is_published:
            actions.append(ShowPublishInFileSystemAction())
            actions.append(ShowPublishInShotgunAction())
        else:
            # see if we have any publishes:
            publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
            if publish_versions:
                actions.append(ShowPublishAreaInFileSystemAction())
                actions.append(ShowLatestPublishInShotgunAction())
            
        return actions
    
    
    
    
    
    
    
    
    
    
    
    
        