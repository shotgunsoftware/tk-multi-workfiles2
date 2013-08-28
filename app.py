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
Multi Publish

"""

import os
import tank
from tank import TankError

class MultiWorkFiles(tank.platform.Application):

    def init_app(self):
        """
        Called as the application is being initialized
        """
        
        tk_multi_workfiles = self.import_module("tk_multi_workfiles")

        # register commands:
        self._work_files_handler = tk_multi_workfiles.WorkFiles(self)
        self.engine.register_command("Shotgun File Manager...", self._work_files_handler.show_dlg)
        self.engine.register_command("Change Work Area...", self.change_work_area, {"type": "context_menu"})

        # other commands are only valid if we have valid work and publish templates:
        if self.get_template("template_work") and self.get_template("template_publish"):
            cmd = lambda app=self: tk_multi_workfiles.SaveAs.show_save_as_dlg(app)
            self.engine.register_command("Shotgun Save As...", cmd)
            
            cmd = lambda app=self: tk_multi_workfiles.Versioning.show_change_version_dlg(app)
            self.engine.register_command("Version up Current Scene...", cmd)
        
        # only launch the dialog once at startup - use the tank object 
        # to store this flag
        if self.get_setting('launch_change_work_area_at_startup'):
            if not hasattr(tank, '_tk_multi_workfiles_change_work_area_shown'):
                # this is the very first time we run this app
                tank._tk_multi_workfiles_change_work_area_shown = True
                # show the UI at startup - but only if the engine supports a UI
                if self.engine.has_ui:
                    self.change_work_area(False)

    def destroy_app(self):
        self.log_debug("Destroying tk-multi-workfiles")
        self._work_files_handler = None
        
    def change_work_area(self, ask_about_new=True):
        self._work_files_handler.change_work_area(ask_about_new)
        
    @property
    def shotgun(self):
        """
        Subclassing of the shotgun property on the app base class. 
        This is a temporary arrangement to be able to time some of the shotgun calls. 
        """
        # get the real shotgun from the application base class
        app_shotgun = tank.platform.Application.shotgun.fget(self)
        # return a wrapper back which produces debug logging
        return DebugWrapperShotgun(app_shotgun, self.log_debug)
        
        
class DebugWrapperShotgun(object):
    
    def __init__(self, sg_instance, log_fn):
        self._sg = sg_instance
        self._log_fn = log_fn
        
    def find(self, *args, **kwargs):
        self._log_fn("SG API find start: %s %s" % (args, kwargs))
        data = self._sg.find(*args, **kwargs)
        self._log_fn("SG API find end")
        return data

    def find_one(self, *args, **kwargs):
        self._log_fn("SG API find_one start: %s %s" % (args, kwargs))
        data = self._sg.find_one(*args, **kwargs)
        self._log_fn("SG API find_one end")
        return data

    def update(self, *args, **kwargs):
        self._log_fn("SG API update start: %s %s" % (args, kwargs))
        data = self._sg.update(*args, **kwargs)
        self._log_fn("SG API update end")
        return data

    def insert(self, *args, **kwargs):
        self._log_fn("SG API insert start: %s %s" % (args, kwargs))
        data = self._sg.insert(*args, **kwargs)
        self._log_fn("SG API insert end")
        return data
    