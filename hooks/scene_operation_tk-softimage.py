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
            
            # If the Solid Angle Arnold renderer is installed, Softimage will 
            # crash if their OnEndNewScene event is not muted and this operation
            # is followed by an open operation!  
            # To avoid this problem, lets find and Mute the event whilst we do the new.
            arnold_event = None
            if parent_action != "new_file": 
                event_info = Application.EventInfos
                for event in event_info:
                    if event.Type == "OnEndNewScene" and event.Name == "SITOA_OnEndNewScene" and not event.Mute:
                        arnold_event = event
                        break
            
            try:
                if arnold_event:
                    # Mute the arnold event
                    self.parent.log_debug("Muting %s event..." % arnold_event.Name)
                    arnold_event.Mute = True
                    
                # perform the new scene:
                Application.NewScene("", True)
            except:
                return False
            else:
                return True
            finally:
                if arnold_event:
                    self.parent.log_debug("Unmuting %s event..." % arnold_event.Name)
                    arnold_event.Mute = False
            
