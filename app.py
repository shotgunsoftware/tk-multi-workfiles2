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
        
        cmd_name = self.get_setting("display_name")
        self.engine.register_command("%s..." % cmd_name, self._work_files_handler.show_dlg)
        
        cmd_name = "Tank Save As"
        cmd = lambda app=self: tk_multi_workfiles.SaveAs.show_save_as_dlg(app)
        self.engine.register_command("%s..." % cmd_name, cmd)
        
        cmd_name = "Version Up Open Scene"
        cmd = lambda app=self: tk_multi_workfiles.Versioning.show_change_version_dlg(app)
        self.engine.register_command("%s..." % cmd_name, cmd)
        
        # only launch the dialog once at startup
        # use tank object to store this flag
        if not hasattr(tank, '_tk_multi_workfiles_shown'):
            # very first time we run this app
            tank._tk_multi_workfiles_shown = True
            # show the UI at startup - but only if the engine supports a UI
            if self.get_setting('launch_at_startup') and self.engine.has_ui:
                self._work_files_handler.show_dlg()
        
    def destroy_app(self):
        self.log_debug("Destroying tk-multi-workfiles")
        self._work_files_handler = None