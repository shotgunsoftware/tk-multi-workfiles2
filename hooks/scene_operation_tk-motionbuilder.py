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
        
        fb_app = FBApplication()

        if operation == "current_path":
            # return the current scene path
            return fb_app.FBXFileName
        elif operation == "open":
            # do new scene as Maya doesn't like opening
            # the scene it currently has open!
            fb_app.FileOpen( file_path )
        elif operation == "save":
            # save the current scene:
            # Note - have to pass the current scene name to
            # avoid showing the save-as dialog
            fb_app.FileSave(fb_app.FBXFileName)
        elif operation == "save_as":
            fb_app.FileSave( file_path )
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            
            while True:
                # Note, there doesn't appear to be any way to query if
                # there are unsaved changes through the MotionBuilder
                # Python API.  Therefore we just assume there are and
                # prompt the user anyway!            
                res = QtGui.QMessageBox.question(None,
                                     "Save your scene?",
                                     "Your scene has unsaved changes. Save before proceeding?",
                                     QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
                
                if res == QtGui.QMessageBox.Cancel:
                    # stop now!
                    return False
                elif res == QtGui.QMessageBox.No:
                    break
                else:
                    # save the file first
                    # Note - have to pass the current scene name to
                    # avoid showing the save-as dialog
                    if fb_app.FileSave(fb_app.FBXFileName):
                        break
                
            # perform file-new
            fb_app.FileNew()
            return True
