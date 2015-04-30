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

class EnvironmentDetails(object):
    def __init__(self, ctx=None):
        """
        """
        self.context = ctx
        
        # context-specific templates
        self.work_area_template = None
        self.work_template = None
        self.publish_area_template = None
        self.publish_template = None
        
        # context-specific settings
        self.save_as_default_name = ""
        self.save_as_prefer_version_up = False
        self.version_compare_ignore_fields = []
        self.valid_file_extensions = []
        
        self._update_settings()
        
    @property
    def context(self):
        return self._context
    
    @context.setter
    def context(self, ctx):
        self._context = ctx
        self._update_settings()
        
    def __repr__(self):
        return ("CTX: %s\n - Work Area: %s\n - Work: %s\n - Publish Area: %s\n - Publish: %s" 
                % (self.context, 
                   self.work_area_template, self.work_template, 
                   self.publish_area_template, self.publish_template)
                )
        
    def _update_settings(self):
        """
        """
        templates_to_find = ["template_work", "template_publish", 
                             "template_work_area", "template_publish_area"]
        settings_to_find = ["saveas_default_name", "saveas_prefer_version_up", 
                            "version_compare_ignore_fields", "file_extensions"]
        resolved_settings = {}
        try:
            resolved_settings = self._get_settings_for_context(self._context, templates_to_find, settings_to_find)
        except:
            # (TODO) - propogate problems up - maybe add an is_valid() method?
            pass
        finally:
            # update the templates and settings regarless if an exception was raised.
            #
            
            # update templates:
            self.work_area_template = resolved_settings.get("template_work_area")
            self.work_template = resolved_settings.get("template_work")
            self.publish_area_template = resolved_settings.get("template_publish_area")
            self.publish_template = resolved_settings.get("template_publish")
            
            # update other settings:        
            self.save_as_default_name = resolved_settings.get("saveas_default_name", "")
            self.save_as_prefer_version_up = resolved_settings.get("saveas_prefer_version_up", False)
            self.version_compare_ignore_fields = resolved_settings.get("version_compare_ignore_fields", [])
            extensions = resolved_settings.get("file_extensions", [])
            extensions = [ext if ext.startswith(".") else ".%s" % ext for ext in extensions if ext]
            self.valid_file_extensions = extensions
        
        
    def _get_settings_for_context(self, context, templates_to_find, settings_to_find=None):
        """
        Find templates for the given context.
        """
        if not context:
            return {}
        
        app = sgtk.platform.current_bundle()
        settings_to_find = settings_to_find or []
        
        resolved_settings = {}
        if app.context == context:
            # no need to look for settings as we already have them in the
            # current environment!
    
            # get templates:        
            for key in templates_to_find:
                resolved_settings[key] = app.get_template(key)
                
            # get additional settings:
            for key in settings_to_find:
                resolved_settings[key] = app.get_setting(key)
                
        else:        
            # need to look for settings in a different context/environment
            settings = self._get_raw_app_settings_for_context(app, context)
            if not settings:
                raise TankError("Failed to find Work Files settings for context '%s'.\n\nPlease ensure that"
                                " the Work Files app is installed for the environment that will be used for"
                                " this context" % context)
            
            # get templates:
            resolved_settings = {}
            for key in templates_to_find:
                resolved_settings[key] = app.get_template_from(settings, key)
                
            # get additional settings:
            for key in settings_to_find:
                resolved_settings[key] = app.get_setting_from(settings, key)
            
        return resolved_settings
            
    def _get_raw_app_settings_for_context(self, app, context):
        """
        Find settings for the app in the specified context
        """
        if not context:
            return
        
        # find settings for all instances of app in 
        # the environment picked for the given context:
        other_settings = sgtk.platform.find_app_settings(app.engine.name, app.name, app.sgtk, context)
        
        if len(other_settings) == 1:
            return other_settings[0].get("settings")
    
        settings_by_engine = {}
        for settings in other_settings:
            settings_by_engine.setdefault(settings.get("engine_instance"), list()).append(settings)
        
        # can't handle more than one engine!  
        if len(settings_by_engine) != 1:
            return
            
        # ok, so have a single engine but multiple apps
        # lets try to find an app with the same instance
        # name:
        app_instance_name = None
        for instance_name, engine_app in app.engine.apps.iteritems():
            if engine_app == app:
                app_instance_name = instance_name
                break
        if not app_instance_name:
            return
    
        for engine_name, engine_settings in settings_by_engine.iteritems():
            for settings in engine_settings:
                if settings.get("app_instance") == app_instance_name:
                    return settings.get("settings")