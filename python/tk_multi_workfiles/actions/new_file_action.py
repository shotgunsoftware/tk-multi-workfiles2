# Copyright (c) 2015 Shotgun Software Inc.
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

import os

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .file_action import FileAction
from ..scene_operation import prepare_new_scene, reset_current_scene, NEW_FILE_ACTION

class NewFileAction(FileAction):
    def __init__(self):
        """
        """
        FileAction.__init__(self, "New File")
    
    def execute(self, file, file_versions, environment, parent_ui):
        """
        Perform a new-scene operation initialized with
        the current context
        """
        if not NewFileAction.can_do_new_file(environment):
            # should never get here as the new button in the UI should
            # be disabled!
            return False
        
        # switch context
        try:
            create_folders = not (environment.context == self._app.context)
            if not create_folders:
                # see if we have all fields for the work area:
                ctx_fields = environment.context.as_template_fields(environment.work_area_template)
                if environment.work_area_template.missing_keys(ctx_fields):
                    # missing fields might be because the path cache isn't populated
                    # so lets create folders anyway to populate it!
                    create_folders = True
            
            if create_folders:
                # ensure folders exist:
                self._create_folders(environment.context)
                
            # reset the current scene:
            if not reset_current_scene(self._app, NEW_FILE_ACTION, environment.context):
                self._app.log_debug("Unable to perform New Scene operation after failing to reset scene!")
                return False
            
            # prepare the new scene:
            prepare_new_scene(self._app, NEW_FILE_ACTION, environment.context)

            if not environment.context == self._app.context:            
                # restart the engine with the new context
                self._restart_engine(environment.context)
        except Exception, e:
            QtGui.QMessageBox.information(parent_ui, "Failed to complete new file operation!", 
                                       "Failed to complete new file operation:\n\n%s!" % e)
            self._app.log_exception("Failed to complete new file operation")
            return False

        return True
        
    @staticmethod
    def can_do_new_file(env):
        """
        Do some validation to see if it's possible to
        start a new file with the selected context.
        """
        can_do_new = (env.context != None 
                      and (env.context.entity or env.context.project)
                      and env.work_area_template != None)
        if not can_do_new:
            return False
        
        # (AD) - this used to check that the context contained everything
        # required by the work area template.  However, this meant that it
        # wasn't possible to start a new file from an entity that didn't
        # exist in the path cache!  This has now been changed so that it's
        # possible to start a new file as long as a work area has been 
        # selected - it's then up to the apps in the new environment to
        # decide what to do if there isn't enough information available in
        # the context.
        
        return True  
         
