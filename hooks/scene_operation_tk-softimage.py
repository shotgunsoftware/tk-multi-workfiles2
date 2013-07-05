"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os

import tank
from tank import Hook
from tank import TankError

import win32com
from win32com.client import Dispatch, constants
from pywintypes import com_error

Application = Dispatch("XSI.Application").Application


class SceneOperation(Hook):
    """
    Hook called to perform an operation with the 
    current scene
    """
    
    def execute(self, operation, file_path, **kwargs):
        """
        Main hook entry point
        
        :operation: String
                    Scene operation to perform
        
        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)
                    
        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    'reset'        - True if scene was reset to an empty 
                                     state, otherwise False
                    all others     - None
        """
        
        if operation == "current_path":
            # return the current scene path
            scene_name = Application.ActiveProject.ActiveScene.Name
            scene_filename = Application.ActiveProject.ActiveScene.filename.value
            # If the scene name is "Scene" rather than "Untitled", we can be reasonably
            # sure that we haven't opened a file called Untitled.scn
            if scene_name == "Scene" and os.path.basename(scene_filename) == "Untitled.scn":
                return ""
            return scene_filename

        elif operation == "open":
            # open the specified scene
            Application.OpenScene(file_path, 0, 0)

        elif operation == "save":
            # save the current scene:
            Application.SaveScene()

        elif operation == "save_as":
            # save the scene as file_path:
            Application.SaveSceneAs(file_path, 0)

        elif operation == "reset":
            # reset the scene to an empty state
            try:
                # use the standard Softimage mechanism to check
                # for and save the file if required:
                Application.NewScene("", 1)
            except com_error:
                # exception here means the user hit 'Cancel'
                return False
            else:
                return True
