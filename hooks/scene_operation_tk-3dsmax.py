"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
from Py3dsMax import mxs

import tank
from tank import Hook
from tank import TankError

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
            if not mxs.maxFileName:
                return ""
            return os.path.join(mxs.maxFilePath, mxs.maxFileName)
        elif operation == "open":
            # open the specified scene
            mxs.loadMaxFile(file_path)
        elif operation == "save":
            # save the current scene:
            file_path = os.path.join(mxs.maxFilePath, mxs.maxFileName)
            mxs.saveMaxFile(file_path)
        elif operation == "save_as":
            # save the scene as file_path:
            mxs.saveMaxFile(file_path)
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            # use the standard Max mechanism to check
            # for and save the file if required:
            if not mxs.checkForSave():
                return False
            
            # now reset the scene:
            mxs.resetMAXFile(mxs.pyhelper.namify("noPrompt"))
            
            return True


