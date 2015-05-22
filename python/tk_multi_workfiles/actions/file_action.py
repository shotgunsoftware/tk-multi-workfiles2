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

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore
from .action import Action

class FileAction(Action):
    """
    """
    @staticmethod
    def create_folders(ctx):
        """
        Create folders for specified context
        """
        app = sgtk.platform.current_bundle()
        app.log_info("Creating folders for context %s" % ctx)

        # create folders:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            ctx_entity = ctx.task or ctx.entity or ctx.project
            app.sgtk.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), 
                                                       engine=app.engine.name)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    @staticmethod
    def restart_engine(ctx):
        """
        Set context to the new context.  This will
        clear the current scene and restart the
        current engine with the specified context
        """
        app = sgtk.platform.current_bundle()
        app.log_info("Restarting the engine...")
        
        # restart engine:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            current_engine_name = app.engine.name
            
            # stop current engine:            
            if sgtk.platform.current_engine(): 
                sgtk.platform.current_engine().destroy()
                
            # start engine with new context:
            sgtk.platform.start_engine(current_engine_name, ctx.sgtk, ctx)
        except Exception, e:
            raise TankError("Failed to change work area and start a new engine - %s" % e)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    
    def __init__(self, label, file, file_versions, environment):
        """
        """
        Action.__init__(self, label)
        self._file = file
        self._file_versions = file_versions
        self._environment = environment

    @property
    def file(self):
        return self._file

    @property
    def file_versions(self):
        return self._file_versions

    @property
    def environment(self):
        return self._environment
