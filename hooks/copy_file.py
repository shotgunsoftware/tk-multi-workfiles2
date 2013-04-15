"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""

import tank
from tank import Hook
import shutil
import os

class CopyFile(Hook):
    """
    Hook called when a file needs to be copied
    """
    
    def execute(self, source_path, target_path, **kwargs):
        """
        Main hook entry point
        
        :source_path:   String
                        Source file path to copy
                        
        :target_path:   String
                        Target file path to copy to
        """
        
        # create the folder if it doesn't exist
        dirname = os.path.dirname(target_path)
        if not os.path.isdir(dirname):            
            old_umask = os.umask(0)
            os.makedirs(dirname, 0777)
            os.umask(old_umask)            

        shutil.copy(source_path, target_path)