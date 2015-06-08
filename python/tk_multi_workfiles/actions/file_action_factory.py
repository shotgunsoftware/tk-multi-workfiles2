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
"""
import sgtk

from .action import SeparatorAction

from .interactive_open_action import InteractiveOpenAction

from .open_workfile_actions import OpenWorkfileAction
from .open_workfile_actions import ContinueFromPreviousWorkFileAction
from .open_workfile_actions import CopyAndOpenFileInCurrentWorkAreaAction 

from .open_publish_actions import OpenPublishAction
from .open_publish_actions import ContinueFromPublishAction
from .open_publish_actions import CopyAndOpenPublishInCurrentWorkAreaAction

from .new_file_action import NewFileAction

from .show_in_filesystem_action import ShowWorkFileInFileSystemAction, ShowPublishInFileSystemAction
from .show_in_filesystem_action import ShowWorkAreaInFileSystemAction, ShowPublishAreaInFileSystemAction 
from .show_in_shotgun_action import ShowPublishInShotgunAction, ShowLatestPublishInShotgunAction

from .custom_file_action import CustomFileAction

from ..work_area import WorkArea

class FileActionFactory(object):
    """
    """
    
    def get_actions(self, file, file_versions, environment, workfiles_visible=True, publishes_visible=True):
        """
        """
        app = sgtk.platform.current_bundle()

        actions = []

        # determine if this file is in a different work area:
        change_work_area = (environment.context != app.context)

        # always add the interactive 'open' action.  This is the
        # default/generic open action that gets run whenever someone
        # double-clicks on a file or just hits the 'Open' button
        actions.append(InteractiveOpenAction(file, file_versions, environment, workfiles_visible, publishes_visible))

        #if workfiles_visible and file.is_local:
        if file.is_local:
            # all actions available when selection is a work file
            
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())            
            actions.append(OpenWorkfileAction(file, file_versions, environment))

            if file.editable:
                # determine if this version is the latest:
                all_versions = [v for v, f in file_versions.iteritems()]
                max_version = max(all_versions) if all_versions else 0
                if file.version != max_version:
                    actions.append(ContinueFromPreviousWorkFileAction(file, file_versions, environment))
                
            if change_work_area:
                # make sure we can actually copy the file to the current work area:
                if app.context:
                    current_env = WorkArea(app.context)
                    if current_env.work_template:
                        actions.append(CopyAndOpenFileInCurrentWorkAreaAction(file, file_versions, environment))
                
        #if publishes_visible and file.is_published:
        if file.is_published:
            # all actions available when selection is a work file:

            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            actions.append(OpenPublishAction(file, file_versions, environment))
            actions.append(ContinueFromPublishAction(file, file_versions, environment))
            
            if change_work_area:
                actions.append(CopyAndOpenPublishInCurrentWorkAreaAction(file, file_versions, environment))    
        
        if NewFileAction.can_do_new_file(environment):
            # New file action
            
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            actions.append(NewFileAction(file, file_versions, environment))
            
        # query for any custom actions:
        custom_actions = CustomFileAction.get_action_details(file, file_versions, environment, 
                                                          workfiles_visible, publishes_visible)
        if custom_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
        for action_dict in custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("caption") or name
            custom_action = CustomFileAction(name, label, file, file_versions, environment, workfiles_visible, publishes_visible)
            actions.append(custom_action)
        
        # finally add the 'show in' actions:
        show_in_actions = []
        if file.is_local:
            show_in_actions.append(ShowWorkFileInFileSystemAction(file, file_versions, environment))
        else:
            if environment.work_area_template:
                show_in_actions.append(ShowWorkAreaInFileSystemAction(file, file_versions, environment))

        if file.is_published:
            show_in_actions.append(ShowPublishInFileSystemAction(file, file_versions, environment))
            show_in_actions.append(ShowPublishInShotgunAction(file, file_versions, environment))
        else:
            if environment.publish_area_template:
                show_in_actions.append(ShowPublishAreaInFileSystemAction(file, file_versions, environment))            
            
            # see if we have any publishes:
            publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
            if publish_versions:
                show_in_actions.append(ShowLatestPublishInShotgunAction(file, file_versions, environment))
            
        if show_in_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())            
            actions.extend(show_in_actions)
            
        return actions
    
    
    
    
    
    
    
    
        