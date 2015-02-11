# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""

import sgtk

class FileAction(object):
    def __init__(self, name, label):
        """
        """
        self._app = sgtk.platform.current_bundle()
        self._name = name
        self._label = label
        
    @property
    def name(self):
        return self._name
    
    @property
    def label(self):
        return self._label
    
    def execute(self, file, file_versions, environment, parent_ui):
        raise NotImplementedError()
    
class CustomFileAction(FileAction):
    def __init__(self, name, label):
        """
        """
        custom_name = "custom_%s" % name
        FileAction.__init__(self, custom_name, label)
        self._orig_name = name
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        """
        # execute hook to perform the action
        # TODO
        pass