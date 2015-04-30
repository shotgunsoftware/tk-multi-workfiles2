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

from .file_action import SeparatorFileAction

from .interactive_open_action import InteractiveOpenAction
from .open_workfile_action import OpenWorkfileAction

# to be moved to seperate files
from .open_workfile_action import ContinueFromPreviousWorkFileAction, CopyAndOpenFileInCurrentWorkAreaAction 
from .open_workfile_action import OpenPublishAction, ContinueFromPublishAction, CopyAndOpenPublishInCurrentWorkAreaAction

from .new_file_action import NewFileAction

from .show_in_filesystem_action import ShowWorkFileInFileSystemAction, ShowPublishInFileSystemAction
from .show_in_filesystem_action import ShowWorkAreaInFileSystemAction, ShowPublishAreaInFileSystemAction 
from .show_in_shotgun_action import ShowPublishInShotgunAction, ShowLatestPublishInShotgunAction

from .custom_file_action import CustomFileAction

class FileActionFactory(object):
    
    def __init__(self):
        """
        """
        pass
    
    def get_actions(self, file, file_versions, environment, workfiles_visible=True, publishes_visible=True):
        """
        [Interactive Open]

        then:

        if is latest work file:
            
            if editable:
            - Open
            else:
            - Open (read-only)
            
            If work area is not current:
            - Open in current work area
            (Does this need to do another check? - I think so, yes)
            
        if it's a previous version of work file:
            if editable:
            - Open vX
            else:
            - Open vX (read-only)

            if editable:
            - Continue Working From (As vX)
            
            if work area is not current:
            - Open in current work area
            
        if is publish:
        
            - Open from the Publish area
            - Continue working from (as vX)
            
            if work area is not current:
            - Open Publish in current work area
            
        If can do new file:
            - New File
        
        [Custom Actions]
        [Show-in Actions]
        
        """
        app = sgtk.platform.current_bundle()
        
        actions = []
        
        local_versions = [v for v, f in file_versions.iteritems() if f.is_local]
        publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
        max_local_version = max(local_versions) if local_versions else None
        max_publish_version = max(publish_versions) if publish_versions else None
        max_version = max(max_local_version, max_publish_version)        
        
        is_latest = (file.version == max_version)
        read_only = not file.editable
        change_work_area = (environment.context != app.context) 
        
        # always add the interactive 'open' action.  This is the
        # default/generic open action that gets run whenever someone
        # double-clicks on a file or just hits the 'Open' button
        actions.append(InteractiveOpenAction(workfiles_visible, publishes_visible))

        #if workfiles_visible and file.is_local:
        if file.is_local:
            # all actions available when selection is a work file
            
            # ------------------------------------------------------------------
            actions.append(SeparatorFileAction())            
            actions.append(OpenWorkfileAction(is_latest, file.version, read_only))
            
            if not is_latest and not read_only:
                # assumes all versions are read_only
                actions.append(ContinueFromPreviousWorkFileAction(max_version+1))
                
            if change_work_area:
                actions.append(CopyAndOpenFileInCurrentWorkAreaAction())
                
        #if publishes_visible and file.is_published:
        if file.is_published:
            # all actions available when selection is a work file:

            # ------------------------------------------------------------------
            actions.append(SeparatorFileAction())
            actions.append(OpenPublishAction(is_latest, file.version))
            actions.append(ContinueFromPublishAction(max_version+1))
            
            if change_work_area:
                actions.append(CopyAndOpenPublishInCurrentWorkAreaAction())    
        
        if NewFileAction.can_do_new_file(environment):
            # New file action
            
            # ------------------------------------------------------------------
            actions.append(SeparatorFileAction())
            actions.append(NewFileAction())
            
        # query for any custom actions:
        custom_actions = CustomFileAction.get_action_details(file, file_versions, environment, 
                                                          workfiles_visible, publishes_visible)
        if custom_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorFileAction())
        for action_dict in custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("caption") or name
            custom_action = CustomFileAction(name, label, workfiles_visible, publishes_visible)
            actions.append(custom_action)
        
        # finally add the 'show in' actions:
        show_in_actions = []
        if file.is_local:
            show_in_actions.append(ShowWorkFileInFileSystemAction())
        else:
            if environment.work_area_template:
                show_in_actions.append(ShowWorkAreaInFileSystemAction())

        if file.is_published:
            show_in_actions.append(ShowPublishInFileSystemAction())
            show_in_actions.append(ShowPublishInShotgunAction())
        else:
            if environment.publish_area_template:
                show_in_actions.append(ShowPublishAreaInFileSystemAction())            
            
            # see if we have any publishes:
            if publish_versions:
                show_in_actions.append(ShowLatestPublishInShotgunAction())
            
        if show_in_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorFileAction())            
            actions.extend(show_in_actions)
            
        return actions
    
    
    
    
    
    
    
    
        