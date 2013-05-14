"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

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
        self.engine.register_command("Tank File Manager...", self._work_files_handler.show_dlg)

        # other commands are only valid if we have valid work and publish templates:
        if self.get_template("template_work") and self.get_template("template_publish"):
            cmd = lambda app=self: tk_multi_workfiles.SaveAs.show_save_as_dlg(app)
            self.engine.register_command("Tank Save As...", cmd)
            
            cmd = lambda app=self: tk_multi_workfiles.Versioning.show_change_version_dlg(app)
            self.engine.register_command("Version up Current Scene...", cmd)
        
    def destroy_app(self):
        self.log_debug("Destroying tk-multi-workfiles")
        self._work_files_handler = None