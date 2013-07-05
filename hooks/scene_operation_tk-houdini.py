"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
import hou

import tank
from tank import Hook
from tank import TankError


class SceneOperation(Hook):
    """
    Hook called to perform an operation with the current scene
    """
    def execute(self, operation, file_path, context, **kwargs):
        """
        Main hook entry point

        :operation: String
                    Scene operation to perform

        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)

        :context:   Context
                    The context the file operation is being
                    performed in.

        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    'reset'        - True if scene was reset to an empty
                                     state, otherwise False
                    all others     - None
        """
        if operation == "current_path":
            return str(hou.hipFile.name())
        elif operation == "open":
            # give houdini forward slashes
            file_path = file_path.replace(os.path.sep, '/')
            hou.hipFile.load(file_path)
        elif operation == "save":
            hou.hipFile.save()
        elif operation == "save_as":
            # give houdini forward slashes
            file_path = file_path.replace(os.path.sep, '/')
            hou.hipFile.save(str(file_path))
        elif operation == "reset":
            hou.hipFile.clear()
            return True
