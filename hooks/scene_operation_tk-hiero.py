"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
import hiero.core

from tank import Hook


class SceneOperation(Hook):
    """
    Hook called to perform an operation with the
    current scene
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
            # return the current script path
            project = self._get_current_project()
            curr_path = project.path().replace("/", os.path.sep)
            return curr_path

        elif operation == "open":
            # open the specified script
            hiero.core.openProject(file_path)
        
        elif operation == "save":
            # save the current script:
            project = self._get_current_project()
            project.save()
        
        elif operation == "save_as":
            project = self._get_current_project()
            project.saveAs(file_path)

        elif operation == "reset":
            # do nothing and indicate scene was reset to empty
            return True
        
        elif operation == "prepare_new":
            # add a new project to hiero
            hiero.core.newProject()
        

    def _get_current_project(self):
        """
        Returns the current project based on where in the UI the user clicked 
        """
        
        # get the menu selection from hiero engine
        selection = self.parent.engine.get_menu_selection()

        if len(selection) != 1:
            raise Exception("Please select a single Project!")
        
        if not isinstance(selection[0] , hiero.core.Bin):
            raise Exception("Please select a Hiero Project!")
            
        project = selection[0].project()
        if project is None:
            # apparently bins can be without projects (child bins I think)
            raise Exception("Please select a Hiero Project!")
         
        return project
