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
        self.__tk_multi_workfiles = self.import_module("tk_multi_workfiles")

        #application_has_scenes = True
        #if self.engine.name == "tk-mari":
        #    # Mari doesn't have the concept of a current scene!
        #    application_has_scenes = False

        # register commands:
        #
        
        #if application_has_scenes:
        #    # Shotgun file manager is available for all engines that have the concept of a scene file:
        #    self.engine.register_command("Shotgun File Manager...", self.show_file_manager_dlg)

        ## change work area is only available if one or more entity types have been set 
        ## in the configuration: 
        #can_change_work_area = (len(self.get_setting("sg_entity_types", [])) > 0)
        #if can_change_work_area:
        #    cmd = lambda enable_start_new=application_has_scenes: self.show_change_work_area_dlg(enable_start_new)
        #    self.engine.register_command("Change Work Area...", cmd, {"type": "context_menu"})

        ## other commands are only valid if we have at least a valid work template.  Version
        ## up the current scene is only available of the work template also has a version key
        #template_work = self.get_template("template_work")
        #self._can_save_as = template_work is not None 
        #self._can_change_version = self._can_save_as and ("version" in template_work.keys)
        #if self._can_save_as:
        #    self.engine.register_command("Shotgun Save As...", self.show_save_as_dlg)
        #if self._can_change_version:
        #    self.engine.register_command("Version up Current Scene...", self.show_change_version_dlg)
        
        # new UI's
        self.engine.register_command("File Open...", self.show_file_open_dlg)
        self.engine.register_command("File Save...", self.show_file_save_dlg)
        
        # process auto startup options - but only on certain supported platforms
        # because of the way QT inits and connects to different host applications
        # differently, in conjunction with the 'boot' process in different tools,
        # the behaviour can be very different.  
        
        # currently, we have done basic QA on nuke and maya so we limit these options to 
        # those two engines for now. 
        
        #SUPPORTED_ENGINES = ["tk-nuke", "tk-maya", "tk-3dsmax"]
        #
        #if self.engine.has_ui and not hasattr(tank, '_tk_multi_workfiles_launch_at_startup'):
        #
        #    # this is the very first time we run this app
        #    tank._tk_multi_workfiles_launch_at_startup = True
        #
        #    if self.get_setting('launch_at_startup'):
        #        # show the file manager UI
        #        if self.engine.name in SUPPORTED_ENGINES:            
        #            self.show_file_manager_dlg()
        #        else:
        #            self.log_warning("Sorry, the launch at startup option is currently not supported "
        #                             "in this engine! You can currently only use it with the following "
        #                             "engines: %s" % ", ".join(SUPPORTED_ENGINES))
        #                    
        #    elif self.get_setting('launch_change_work_area_at_startup') and can_change_work_area:
        #        # show the change work area UI
        #        if self.engine.name in SUPPORTED_ENGINES:
        #            self.show_change_work_area_dlg(False)
        #        else:
        #            self.log_warning("Sorry, the launch at startup option is currently not supported "
        #                             "in this engine! You can currently only use it with the following "
        #                             "engines: %s" % ", ".join(SUPPORTED_ENGINES))

    def destroy_app(self):
        self.log_debug("Destroying tk-multi-workfiles")
        
    def show_file_open_dlg(self):
        """
        """
        self.__tk_multi_workfiles.WorkFiles.show_file_open_dlg()

    def show_file_save_dlg(self):
        """
        """
        self.__tk_multi_workfiles.WorkFiles.show_file_save_dlg()        

    #def can_save_as(self):
    #    """
    #    Returns True if save-as is available, False otherwise.
    #    """
    #    return self._can_save_as
        
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
        self.config = sg_instance.config
        
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

    def create(self, *args, **kwargs):
        self._log_fn("SG API create start: %s %s" % (args, kwargs))
        data = self._sg.create(*args, **kwargs)
        self._log_fn("SG API create end")
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
    
