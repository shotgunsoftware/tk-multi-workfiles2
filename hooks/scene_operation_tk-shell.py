# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import sgtk

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
    """

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """
        # We need to see which mode of Nuke we're in. If this is Hiero or
        # Nuke Studio, then we have a separate scene operation routine to
        # use. We're checking that the "hiero_enabled" attribute exists
        # to ensure that this works properly with pre-v0.4.x versions of
        # the tk-nuke engine. If that one attribute exists, then we can be
        # confident that the "studio_enabled" attribute is also available,
        # so there's no need to check that.
        #
        # If there is ever a situation where Hiero- or Nuke Studio-specific
        # logic is required that doesn't also apply to the other, then this
        # conditional could be broken up between hiero_enabled and
        # studio_enabled cases that call through to Nuke Studio and Hiero
        # specific methods.
        # If we didn't hit the Hiero or Nuke Studio case above, we can
        # continue with the typical Nuke scene operation logic.

        engine = self.parent.engine

        engine.log_info("scene_operation.execute.%s" % operation)
        engine.log_info("    file_path: %s" % file_path)
        engine.log_info("    context: %s" % context)
        engine.log_info("    parent_action: %s" % parent_action)
        engine.log_info("    file_version: %s" % file_version)
        engine.log_info("    read_only: %s" % read_only)

        if operation == "current_path":
            return os.getcwd()
        elif operation == "reset":
            return True

