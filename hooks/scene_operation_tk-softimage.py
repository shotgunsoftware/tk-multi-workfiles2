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

import win32com
from win32com.client import Dispatch, constants
from pywintypes import com_error

Application = Dispatch("XSI.Application").Application

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

        if operation == "current_path":
            # return the current scene path

            # query the current scene 'name' and file path from the application:
            scene_filepath = Application.ActiveProject.ActiveScene.filename.value
            scene_name = Application.ActiveProject.ActiveScene.Name

            # There doesn't seem to be an easy way to determin if the current scene
            # is 'new'.  However, if the file name is "Untitled.scn" and the scene
            # name is "Scene" rather than "Untitled", then we can be reasonably sure
            # that we haven't opened a file called Untitled.scn
            if scene_name == "Scene" and os.path.basename(scene_filepath) == "Untitled.scn":
                return ""
            return scene_filepath

        elif operation == "open":
            # open the specified scene without any prompts

            # Redraw the UI
            # Certain OnEndNewScene events can result in Softimage
            # crashing if a scene is opened immediately after doing
            # a new scene.  One such event is the Solid Andle Arnold
            # renderer SITOA_OnEndNewScene event which sets some
            # viewport settings.
            #
            # Calling RedrawUI seems to force the events to complete
            # before the open and therefore avoids the crash!
            Application.Desktop.RedrawUI()

            # Application.OpenScene(path, Confirm, ApplyAuxiliaryData)
            Application.OpenScene(file_path, False, False)

        elif operation == "save":
            # save the current scene:
            Application.SaveScene()

        elif operation == "save_as":
            # save the scene as file_path:
            Application.SaveSceneAs(file_path, False)

        elif operation == "reset":
            # Reset the current scene. This is run when performing both
            # 'new file' and 'open file' operations.

            try:
                # perform the new scene:
                Application.NewScene("", True)
            except:
                return False
            else:
                return True

