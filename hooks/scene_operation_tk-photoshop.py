"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
import photoshop

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
            # return the current script path
            doc = photoshop.app.activeDocument

            if doc is None:
                path = ""
            elif doc.fullName is None:
                path = ""
            else:
                path = doc.fullName.nativePath
            
            return path

        elif operation == "open":
            # open the specified script
            f = photoshop.RemoteObject('flash.filesystem::File', file_path)
            photoshop.app.load(f)            
        
        elif operation == "save":
            # save the current script:
            doc = photoshop.app.activeDocument

            if doc:
                photoshop.app.activeDocument.save()
        
        elif operation == "save_as":
            doc = photoshop.app.activeDocument
            if doc:            
                new_file_name = photoshop.RemoteObject('flash.filesystem::File', file_path)
                # no options and do not save as a copy
                # http://cssdk.host.adobe.com/sdk/1.5/docs/WebHelp/references/csawlib/com/adobe/photoshop/Document.html#saveAs()
                doc.saveAs(new_file_name, None, False)

        elif operation == "reset":
            # do nothing and indicate scene was reset to empty
            return True
        
        elif operation == "prepare_new":
            # file->new
            photoshop.app.documents.add()
        

