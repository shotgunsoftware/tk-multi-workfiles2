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

from .file_action import SeparatorFileAction

from .interactive_open_action import InteractiveOpenAction
from .open_workfile_action import OpenWorkfileAction

from .show_in_filesystem_action import ShowWorkFileInFileSystemAction, ShowPublishInFileSystemAction
from .show_in_filesystem_action import ShowWorkAreaInFileSystemAction, ShowPublishAreaInFileSystemAction 
from .show_in_shotgun_action import ShowPublishInShotgunAction, ShowLatestPublishInShotgunAction

from .custom_file_action import CustomFileAction

class FileActionFactory(object):
    
    def __init__(self):
        """
        """
        pass
    
    def get_actions(self, file, file_versions, environment):
        """
        """
        actions = []
        
        # always add the interactive 'open' action.  This is the
        # default/generic open action that gets run whenever someone
        # double-clicks on a file or just hits the 'Open' button
        actions.append(InteractiveOpenAction())

        # ------------------------------------------------------------------
        actions.append(SeparatorFileAction())

        # now add explicit file operations based off the selection:
        if file.is_local:
            # can open this file directly:
            # TODO: check user and version
            actions.append(OpenWorkfileAction(not file.editable))
        if file.is_published:
            # 'Continue working from' action
            #actions.append(OpenPublishAction())
            # 'Open read-only' action
            #actions.append(OpenPublishAction())
            pass
        
        # ------------------------------------------------------------------
        actions.append(SeparatorFileAction())
        
        # query for any custom actions:
        hook_custom_actions = []
        # TODO
        for action_dict in hook_custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("label") or name
            custom_action = CustomFileAction(name, label)
            actions.append(custom_action)
        
        # ------------------------------------------------------------------
        actions.append(SeparatorFileAction())
        
        # finally add the 'jump to' actions:
        if file.is_local:
            actions.append(ShowWorkFileInFileSystemAction())
        else:
            if environment.work_area_template:
                actions.append(ShowWorkAreaInFileSystemAction())
            
        if file.is_published:
            actions.append(ShowPublishInFileSystemAction())
            actions.append(ShowPublishInShotgunAction())
        else:
            if environment.publish_area_template:
                actions.append(ShowPublishAreaInFileSystemAction())            
            
            # see if we have any publishes:
            publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
            if publish_versions:
                actions.append(ShowLatestPublishInShotgunAction())
            
        return actions
    
    
    
    
    
    
    
    
    
    
    
    
        