# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
from pyfbsdk import FBApplication

import tank
from tank import Hook
from tank import TankError
from tank.platform.qt import QtGui

class SceneOperation(Hook):
    """
    Hook called to perform an operation with the
    current scene
    """

    def execute(self, operation, file_path, context, parent_action, **kwargs):
        """
        Main hook entry point

        :operation:     String
                        Scene operation to perform

        :file_path:     String
                        File path to use if the operation
                        requires it (e.g. open)

        :context:       Context
                        The context the file operation is being
                        performed in.

        :parent_action: This is the action that this scene operation is
                        being executed for.  This can be one of:
                        - open_file
                        - new_file
                        - save_file_as
                        - version_up

        :returns:       Depends on operation:
                        'current_path' - Return the current scene
                                         file path as a String
                        'reset'        - True if scene was reset to an empty
                                         state, otherwise False
                        all others     - None
        """
        lApplication = FBApplication()

        if operation == "current_path":
            # return the current scene path
            return lApplication.FBXFileName
        elif operation == "open":
            # do new scene as Maya doesn't like opening
            # the scene it currently has open!
            lApplication.FileOpen( file_path )
        elif operation == "save":
            # save the current scene:
            lApplication.FileSave( lApplication.FBXFileName )
        elif operation == "save_as":
            lApplication.FileSave( file_path )
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            ## TODO - Check if scene changes need to be saved
            ## FileNew will force a new scene without asking user.
            lApplication.FileNew()
            return True
