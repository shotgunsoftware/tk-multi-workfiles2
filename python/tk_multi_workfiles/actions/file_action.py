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
    def __init__(self, label):
        """
        """
        self._app = sgtk.platform.current_bundle()
        self._label = label
        
    @property
    def label(self):
        return self._label
    
    def execute(self, file, file_versions, environment, parent_ui):
        raise NotImplementedError()

    def _create_folders(self, ctx):
        """
        Create folders for specified context
        """
        self._app.log_debug("Creating folders for context %s" % ctx)
        
        # create folders:
        ctx_entity = ctx.task or ctx.entity or ctx.project
        self._app.sgtk.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), 
                                                   engine=self._app.engine.name)

    def _restart_engine(self, ctx):
        """
        Set context to the new context.  This will
        clear the current scene and restart the
        current engine with the specified context
        """
        self._app.log_debug("Restarting the engine...")
        
        # restart engine:        
        try:
            current_engine_name = self._app.engine.name
            
            # stop current engine:            
            if sgtk.platform.current_engine(): 
                sgtk.platform.current_engine().destroy()
                
            # start engine with new context:
            sgtk.platform.start_engine(current_engine_name, ctx.sgtk, ctx)
        except Exception, e:
            raise TankError("Failed to change work area and start a new engine - %s" % e)

class SeparatorFileAction(FileAction):
    def __init__(self):
        FileAction.__init__(self, "---")
        
    def execute(self, file, file_versions, environment, parent_ui):
        # do nothing!
        pass
