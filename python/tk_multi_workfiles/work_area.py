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
import threading
import copy
import sgtk
from sgtk import TankError

from .user_cache import g_user_cache
from .util import Threaded

class WorkArea(object):
    """
    Class containing information about the current work area including context, templates
    and other miscelaneous work-area specific settings.
    """
    
    class _SettingsCache(Threaded):
        """
        Cache of settings per context, engine and app name.
        """
        def __init__(self):
            Threaded.__init__(self)
            self._cache = {}

        @Threaded.exclusive
        def get(self, engine_name, app_name, context):
            """
            """
            settings_by_context = self._cache.get((engine_name, app_name), [])
            for ctx, settings in settings_by_context:
                if ctx == context:
                    return settings

        @Threaded.exclusive
        def add(self, engine_name, app_name, context, settings):
            """
            """
            self._cache.setdefault((engine_name, app_name), list()).append((context, copy.deepcopy(settings)))
    
    _settings_cache = _SettingsCache() 
    
    def __init__(self, ctx=None):
        """
        Construction
        """
        # the context!
        self._context = ctx

        # context-specific templates:
        self.work_area_template = None
        self.work_template = None
        self.publish_area_template = None
        self.publish_template = None
        
        # context-specific settings:
        self.save_as_default_name = ""
        self.save_as_prefer_version_up = False
        self.version_compare_ignore_fields = []
        self.valid_file_extensions = []

        # user sandbox information:
        self._sandbox_users = {}
        self._work_template_contains_user = False
        self._publish_template_contains_user = False

        # load settings:
        self._load_settings()

    def create_copy_for_user(self, user):
        """
        Create a copy of this work area for a specific user.  

        Note, this assumes that all templates & settings are identical for all users.  If this turns out to be
        an invalid assumption then this code will need to be changed to resolve settings as well.  However,
        this is primarily used when resolving user sandboxes which are intrinsically linked to the templates, etc.
        so the whole thing will probably break if this does turn out to be the case!
        """
        user_work_area = WorkArea()
        user_work_area._context = self._context.create_copy_for_user(user) 

        # deep copy all other templates and settings
        user_work_area.work_area_template = self.work_area_template
        user_work_area.work_template = self.work_template
        user_work_area.publish_area_template = self.publish_area_template
        user_work_area.publish_template = self.publish_template
        user_work_area.save_as_default_name = self.save_as_default_name
        user_work_area.save_as_prefer_version_up = self.save_as_prefer_version_up
        user_work_area.version_compare_ignore_fields = copy.deepcopy(self.version_compare_ignore_fields)
        user_work_area.valid_file_extensions = copy.deepcopy(self.valid_file_extensions)
        user_work_area._sandbox_users = copy.deepcopy(self._sandbox_users)
        user_work_area._work_template_contains_user = self._work_template_contains_user
        user_work_area._publish_template_contains_user = self._publish_template_contains_user

        return user_work_area


    #@property
    def _get_context(self):
        return self._context
    #@context.setter
    def _set_context(self, ctx):
        """
        Set the context
        """
        self._context = ctx
        self._load_settings()
    context=property(_get_context, _set_context)

    @property
    def work_area_contains_user_sandboxes(self):
        """
        """
        return self._work_template_contains_user

    @property
    def publish_area_contains_user_sandboxes(self):
        """
        """
        return self._publish_template_contains_user
    
    @property
    def contains_user_sandboxes(self):
        """
        """
        return (self._work_template_contains_user 
                or self._publish_template_contains_user)

    @property
    def work_area_sandbox_users(self):
        """
        """
        if self._work_template_contains_user:
            return self._resolve_user_sandboxes(self.work_template)
        else:
            return []

    @property
    def publish_area_sandbox_users(self):
        """
        """
        if self._publish_template_contains_user:
            return self._resolve_user_sandboxes(self.publish_template)
        else:
            return []

    @property
    def sandbox_users(self):
        """
        """
        sandbox_users = self.work_area_sandbox_users
        user_ids = set([u["id"] for u in sandbox_users])
        for user in self.publish_area_sandbox_users:
            user_id = user["id"]
            if user_id not in user_ids:
                sandbox_users.append(user)
                user_ids.add(user_id)
        return sandbox_users

    def resolve_user_sandboxes(self):
        """
        """
        self._resolve_user_sandboxes(self.work_template)
        self._resolve_user_sandboxes(self.publish_template)

    # ------------------------------------------------------------------------------------------
    # Protected methods

    def __repr__(self):
        return ("CTX: %s\n - Work Area: %s\n - Work: %s\n - Publish Area: %s\n - Publish: %s" 
                % (self._context, 
                   self.work_area_template, self.work_template, 
                   self.publish_area_template, self.publish_template)
                )

    def _load_settings(self):
        """
        """
        # attemps to load all settings for the context:
        templates_to_find = ["template_work", "template_publish", 
                             "template_work_area", "template_publish_area"]
        settings_to_find = ["saveas_default_name", "saveas_prefer_version_up", 
                            "version_compare_ignore_fields", "file_extensions"]
        resolved_settings = {}
        try:
            if self._context:
                resolved_settings = self._get_settings_for_context(self._context, templates_to_find, settings_to_find)
        except:
            # (TODO) - propogate problems up - maybe add an is_valid() method?
            pass
        finally:
            # update the templates and settings regardless if an exception was raised.
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
            extensions = resolved_settings.get("file_extensions") or []
            extensions = [ext if ext.startswith(".") else ".%s" % ext for ext in extensions if ext]
            self.valid_file_extensions = extensions

            # test for user sandboxes:
            self._work_template_contains_user = self.work_template and bool(self._get_template_user_keys(self.work_template))
            self._publish_template_contains_user = self.publish_template and bool(self._get_template_user_keys(self.publish_template))

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
        
        # first look in the cache:
        other_settings = WorkArea._settings_cache.get(app.engine.name, app.name, context)
        if other_settings == None:
            try:
                # find settings for all instances of app in the environment picked for the given context:
                other_settings = sgtk.platform.find_app_settings(app.engine.name, app.name, app.sgtk, context)
                if not other_settings:
                    # for backwards compatibility, look for settings for the 'tk-multi-workfiles' app as well
                    other_settings = sgtk.platform.find_app_settings(app.engine.name, "tk-multi-workfiles", 
                                                                     app.sgtk, context)
            finally:
                # make sure the cache is updated:
                WorkArea._settings_cache.add(app.engine.name, app.name, context, other_settings or {})

        if len(other_settings) == 1:
            return other_settings[0].get("settings")
    
        settings_by_engine = {}
        for settings in other_settings:
            settings_by_engine.setdefault(settings.get("engine_instance"), list()).append(settings)
        
        # can't handle more than one engine!  
        if len(settings_by_engine) != 1:
            return
            
        # ok, so have a single engine but multiple apps lets try 
        # to find an app with the same instance name.

        # first, get the instance name of the current app - we
        # have to look through all engine apps to find this as
        # the app itself doesn't know
        app_instance_name = None
        for instance_name, engine_app in app.engine.apps.iteritems():
            if engine_app == app:
                app_instance_name = instance_name
                break
        if not app_instance_name:
            return
    
        # now look for settings for this specific instance in the engine settings:
        for engine_name, engine_settings in settings_by_engine.iteritems():
            for settings in engine_settings:
                if settings.get("app_instance") == app_instance_name:
                    return settings.get("settings")

    def _resolve_user_sandboxes(self, template):
        """
        """
        if not template or not self._context:
            # don't have enough information to resolve users!
            return []

        # find all 'user' keys in the template:
        user_keys = self._get_template_user_keys(template)
        if not user_keys:
            # this template doesn't contain user keys!
            return []

        users = self._sandbox_users.get(template.definition)
        if users is not None:
            # already resolved users!
            return users

        # update cache:
        self._sandbox_users[template.definition] = []

        # find shortest template that contains one of the user keys:
        # (AD) - this might need to be extended to cope with optional
        # user keys
        search_template = template
        while True:
            # get the template's parent:
            parent_template = search_template.parent
            # make sure it's still valid and has a user key in it:
            if not parent_template or not (user_keys & set(parent_template.keys)):
                break
            search_template = parent_template

        # resolve context fields for this template:
        ctx_fields = {}
        try:
            # Note, we deliberately don't perform validation here as the current user may not have created
            # any files yet and we don't want this to fail just because it can't resolve a field for the
            # user key. 
            ctx_fields = self._context.as_template_fields(search_template, validate=False)
        except TankError, e:
            # this probably means that there isn't anything in the path cache for this context
            # yet which also means no users have created folders therefore there are also no 
            # user sandboxes!
            return []

        # make sure we have enough fields to perform a valid search - we should have all non-optional
        # keys apart from user keys:
        for key_name in search_template.keys.keys():
            if (key_name not in user_keys 
                and key_name not in ctx_fields
                and not search_template.is_optional(key_name)):
                # this is bad - assume we can't perform a search!
                return []
            
        # ok, so lets search for paths that match the template:
        app = sgtk.platform.current_bundle()
        paths = app.sgtk.paths_from_template(search_template, ctx_fields, user_keys)
        
        # split out users from the list of paths:
        user_ids = set()
        for path in paths:
            # to find the user, we have to construct a context
            # from the path and then inspect the user from this
            path_ctx = app.sgtk.context_from_path(path)
            user = path_ctx.user
            if user: 
                user_ids.add(user["id"])

        # look these up in the user cache:
        users = g_user_cache.get_user_details_for_ids(user_ids).values()
        self._sandbox_users[template.definition] = users
        return users

    def _get_template_user_keys(self, template):
        """
        """
        # find all 'user' keys in the template:
        user_keys = set()
        if "HumanUser" in template.keys:
            user_keys.add("HumanUser")
        for key in template.keys.values():
            if key.shotgun_entity_type == "HumanUser":
                user_keys.add(key.name)
        return user_keys


