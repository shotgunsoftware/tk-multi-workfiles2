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
Hook that defines and executes custom actions that can operate on a file (and it's versions).
"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class CustomActions(HookBaseClass):
    """
    Implementation of the CustomActions class
    """

    def generate_actions(self, file, work_versions, publish_versions, context, **kwargs):
        """
        Generate a list of actions that should be made available via the right-click context menu on a work file or
        publish in the main file view.

        Each action returned should be a dictionary containing the name (should be unique) and the UI caption to use
        in the menu.

        :param file:                Information about the currently selected file.  This is a dictionary containing
                                    the following fields:

                                    - name          - The Toolkit name for the file (e.g. the value for the name
                                                      template key)
                                    - path          - The path of the file
                                    - version       - The version of the file
                                    - type          - The type of the file - this can be either 'work' for work files
                                                      or 'publish' for publishes.

                                    Additionally, for work files (type is 'work'), the dictionary will also contain:

                                    - modified_at   - The date/time the file was last modified on disk
                                    - modified_by   - A Shotgun user dictionary representing the last person to modify
                                                      the file.
                                    - read_only     - True if the work file is deemed read-only.  This can be
                                                      customised by overriding the filter_work_files hook

                                    For publishes (type is 'publish'), the dictionary will also contain:
                                    - published_at  - The date/time the file was published
                                    - published_by  - A Shotgun user dictionary representing the user that published
                                                      this file
        :param work_versions:       A list of all the work file versions that exist for this file.  Each entry in
                                    the list is a dictionary with the same form as that for the 'file' parameter
        :param publish_versions:    A list of all the publish versions that exist for this file.  Each entry in
                                    the list is a dictionary with the same form as that for the 'file' parameter
        :param context:             The context/work area this file and all it's versions exist in.
        :returns:                   A list of custom actions that are available for this file.  Each action in the
                                    list should be a dictionary containing:

                                    - name      - A unique name to identify the action by.  This will be passed back to
                                                  'execute_action' to identify the action to be executed
                                    - caption   - The caption to use in the UI (e.g. on the Menu) for the action
        """
        # default implementation returns an empty list!
        # return [{"name":"do_something", "caption":"Do Something"}]
        return []

    def execute_action(self, action, file, work_versions, publish_versions, context, **kwargs):
        """
        Execute the specified action on the specified file/file versions.

        :param action:              The name of the action to execute.  This will be the name of one of the actions
                                    returned by the 'generate_actions' method.
        :param file:                Information about the currently selected file.  This is a dictionary containing
                                    the following fields:

                                    - name          - The Toolkit name for the file (e.g. the value for the name
                                                      template key)
                                    - path          - The path of the file
                                    - version       - The version of the file
                                    - type          - The type of the file - this can be either 'work' for work files
                                                      or 'publish' for publishes.

                                    Additionally, for work files (type is 'work'), the dictionary will also contain:

                                    - modified_at   - The date/time the file was last modified on disk
                                    - modified_by   - A Shotgun user dictionary representing the last person to modify
                                                      the file.
                                    - read_only     - True if the work file is deemed read-only.  This can be
                                                      customised by overriding the filter_work_files hook

                                    For publishes (type is 'publish'), the dictionary will also contain:
                                    - published_at  - The date/time the file was published
                                    - published_by  - A Shotgun user dictionary representing the user that published
                                                      this file
        :param work_versions:       A list of all the work file versions that exist for this file.  Each entry in
                                    the list is a dictionary with the same form as that for the 'file' parameter
        :param publish_versions:    A list of all the publish versions that exist for this file.  Each entry in
                                    the list is a dictionary with the same form as that for the 'file' parameter
        :param context:             The context/work area this file and all it's versions exist in.
        :returns:                   True if the action should close the main UI, otherwise False to keep it open.
        """
        # default implementation does nothing!
        return False
