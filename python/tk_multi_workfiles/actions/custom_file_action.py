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

from .file_action import FileAction

class CustomFileAction(FileAction):
    
    @staticmethod
    def _prepare_file_data_for_hook(file_versions):
        """
        """
        work_file_versions = []
        publish_versions = []
        for file in file_versions:
            if file.is_local:
                work_file = {}
                work_file["name"] = file.name
                work_file["path"] = file.path
                work_file["version"] = file.version
                work_file["modified_at"] = file.modified_at
                work_file["modified_by"] = file.modified_by
                work_file["read_only"] = not file.editable
                work_file["type"] = "work"
                work_file_versions.append(work_file)
            if file.is_published:
                publish = {}
                publish["name"] = file.name
                publish["path"] = file.publish_path
                publish["version"] = file.version
                publish["published_at"] = file.published_at
                publish["published_by"] = file.published_by
                publish["type"] = "publish"
                publish_versions.append(publish)

        return work_file_versions, publish_versions

    @staticmethod
    def get_action_details(file, file_versions, environment, workfiles_visible, publishes_visible):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # build hook-friendly data:
        work_file, publish = CustomFileAction._prepare_file_data_for_hook([file])
        hook_file = None
        if workfiles_visible:
            hook_file = work_file[0] if work_file else None
        if not hook_file and publishes_visible:
            hook_file = publish[0] if publish else None
        work_versions, publish_versions = CustomFileAction._prepare_file_data_for_hook(file_versions.values())

        # execute hook method to get actions:
        action_info = []
        try:
            action_info = app.execute_hook_method("custom_actions_hook", 
                                                  "generate_actions", 
                                                  file = hook_file,
                                                  work_versions = work_versions,
                                                  publish_versions = publish_versions,
                                                  context = environment.context)
        except:
            app.log_exception("Failed to retrieve custom actions from Hook!")
            
        return action_info
        
    
    def __init__(self, name, label, file, file_versions, environment, workfiles_visible, publishes_visible):
        """
        Construction
        """
        FileAction.__init__(self, label, file, file_versions, environment)
        self._name = name
        self._workfiles_visible = workfiles_visible
        self._publishes_visible = publishes_visible
    
    def execute(self, parent_ui):
        """
        """
        # execute hook to perform the action
        app = sgtk.platform.current_bundle()
        
        # build hook-friendly data:
        work_file, publish = CustomFileAction._prepare_file_data_for_hook([self.file])
        hook_file = None
        if self._workfiles_visible:
            hook_file = work_file[0] if work_file else None
        if not hook_file and self._publishes_visible:
            hook_file = publish[0] if publish else None
        work_versions, publish_versions = CustomFileAction._prepare_file_data_for_hook(self.file_versions.values())

        # execute hook method to execute action:
        result = False
        try:
            result = app.execute_hook_method("custom_actions_hook", 
                                              "execute_action",
                                              action = self._name, 
                                              file = hook_file,
                                              work_versions = work_versions,
                                              publish_versions = publish_versions,
                                              context = self.environment.context)
        except:
            app.log_exception("Failed to execute custom action!")

        return result

