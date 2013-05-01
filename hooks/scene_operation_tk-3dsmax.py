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
            mxs.saveMaxFile()
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
                raise TankError("New scene cancelled")
            
            # now reset the scene:
            mxs.resetMAXFile(mxs.pyhelper.namify("noPrompt"))
            
        else:
            raise TankError("Don't know how to perform scene operation '%s'" % operation)


