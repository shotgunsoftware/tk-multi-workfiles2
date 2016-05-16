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
Environment and context abstraction.
"""

import copy
import sgtk
from sgtk import TankError

from .user_cache import g_user_cache
from .util import Threaded, get_template_user_keys


class WorkArea(object):
    """
    Class containing information about the current work area including context, templates
    and other miscellaneous work-area specific settings.
    """

    # Number of template settings for the app.
    NB_TEMPLATE_SETTINGS = 4

    class _SettingsCache(Threaded):
        """
        Cache of settings per context.
        """

        def __init__(self):
            """
            Constructor.
            """
            Threaded.__init__(self)
            self._cache = []

        @Threaded.exclusive
        def get(self, context):
            """
            Retrieve the cached settings for a given context.

            :param context: The context for which we desire settings.

            :returns: The settings dictionary or None
            """
            for ctx, settings in self._cache:
                if ctx == context:
                    return settings
            return None

        @Threaded.exclusive
        def add(self, context, settings):
            """
            Cache settings for a given context.

            :param context: Context for which these settings need to be cached.
            :param settings: Settings to cache.
            """
            self._cache.append((context, copy.deepcopy(settings)))

    _settings_cache = _SettingsCache()

    def __init__(self, ctx=None):
        """
        Construction

        :param ctx: Toolkit context to load the work area settings for.

        :raises TankError: Thrown if the settings couldn't be loaded from disk.
        """
        # the context!
        self._context = ctx

        # Assume we haven't found the settings for this context by default.
        self._settings_loaded = False

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

        # Keep track which engine instance the settings come from.
        self.engine_instance_name = sgtk.platform.current_bundle().engine.instance_name

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
        user_work_area._settings_loaded = self._settings_loaded

        return user_work_area

    # @property
    def _get_context(self):
        return self._context

    # @context.setter
    def _set_context(self, ctx):
        """
        Set the context
        """
        self._context = ctx
        self._load_settings()

    context = property(_get_context, _set_context)

    def are_settings_loaded(self):
        """
        Indicates if settings were loaded for a given work area.
        """
        return self._settings_loaded

    @property
    def work_area_contains_user_sandboxes(self):
        """
        :returns: True if the work files are in user sandboxes.
        """
        return self._work_template_contains_user

    @property
    def publish_area_contains_user_sandboxes(self):
        """
        :returns: True if the publishes are in user sandboxes.
        """
        return self._publish_template_contains_user

    @property
    def contains_user_sandboxes(self):
        """
        :returns: True if a sandbox is used.
        """
        return (self._work_template_contains_user or
                self._publish_template_contains_user)

    @property
    def work_area_sandbox_users(self):
        """
        :returns: List of users inside the work area sandboxes.
        """
        if self._work_template_contains_user:
            return self._resolve_user_sandboxes(self.work_template)
        else:
            return []

    @property
    def publish_area_sandbox_users(self):
        """
        :returns: List of users inside the publish area sandboxes.
        """
        if self._publish_template_contains_user:
            return self._resolve_user_sandboxes(self.publish_template)
        else:
            return []

    @property
    def sandbox_users(self):
        """
        :returns: List of users inside the all sandboxes
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
        Caches internally the list of user sandboxes.
        """
        self._resolve_user_sandboxes(self.work_template)
        self._resolve_user_sandboxes(self.publish_template)

    # ------------------------------------------------------------------------------------------
    # Protected methods

    def __repr__(self):
        """
        Formats a string with information about the work area context's and templates, e.g.::
            CTX: Anm2, Shot bunny_010_0010
             - Work Area: <Sgtk TemplatePath shot_work_area_maya: sequences/{Sequence}/{Shot}/{Step}/work/maya>
             - Work: <Sgtk TemplatePath maya_shot_work: sequences/{Sequence}/{Shot}/{Step}/work/maya/{name}.v{version}.{extension}>
             - Publish Area: <Sgtk TemplatePath shot_publish_area_maya: sequences/{Sequence}/{Shot}/{Step}/publish/maya>
             - Publish: <Sgtk TemplatePath maya_shot_publish: sequences/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.{extension}>

        :returns The formatted string.
        """
        return ("CTX: %s\n - Work Area: %s\n - Work: %s\n - Publish Area: %s\n - Publish: %s"
                % (self._context,
                   self.work_area_template, self.work_template,
                   self.publish_area_template, self.publish_template)
                )

    def _load_settings(self):
        """
        Extracts the settings from the environment file.
        """
        # attemps to load all settings for the context:
        templates_to_find = ["template_work", "template_publish",
                             "template_work_area", "template_publish_area"]
        settings_to_find = ["saveas_default_name", "saveas_prefer_version_up",
                            "version_compare_ignore_fields", "file_extensions"]
        resolved_settings = {}
        if self._context:
            resolved_settings = self._get_settings_for_context(self._context, templates_to_find, settings_to_find)

        if not resolved_settings:
            return

        self._settings_loaded = True

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
        self._work_template_contains_user = self.work_template and bool(get_template_user_keys(self.work_template))
        self._publish_template_contains_user = self.publish_template and bool(get_template_user_keys(self.publish_template))

    def get_missing_templates(self):
        """
        Asserts that all the templates are configured.

        :returns: An array of sgtk.Template objects that are not configured.
        """
        # First find all the templates that are not defined.
        missing_templates = []
        if not self.work_area_template:
            missing_templates.append("'template_work_area'")
        if not self.work_template:
            missing_templates.append("'template_work'")
        if not self.publish_area_template:
            missing_templates.append("'template_publish_area'")
        if not self.publish_template:
            missing_templates.append("'template_publish'")

        return missing_templates

    def _get_settings_for_context(self, context, templates_to_find, settings_to_find=None):
        """
        Find templates for the given context.

        :param context: Toolkit context.
        :param templates_to_find: Name of the templates to look for in the settings.
        :param settings_to_find: List of mandatory settings names.

        :returns: A dictionary of the settings. If the dictionary is empty, not settings was found.

        :raises TankError: If no workfiles
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
            if settings:
                # get templates:
                for key in templates_to_find:
                    resolved_settings[key] = app.get_template_from(settings, key)

                # get additional settings:
                for key in settings_to_find:
                    resolved_settings[key] = app.get_setting_from(settings, key)

        return resolved_settings

    def _get_raw_app_settings_for_context(self, app, context):
        """
        Find settings for the app in the specified context

        :param app: Application instance
        :param context: Context in which to look for settings.

        :returns: The workfiles 2 application settings for the given context or None.
        """
        app = sgtk.platform.current_bundle()

        if not context:
            app.log_debug("No context found.")
            return

        # first look in the cache:
        app_settings = WorkArea._settings_cache.get(context)

        if app_settings is None:
            try:
                # find settings for all instances of app in the environment picked for the given context:
                app_settings = sgtk.platform.find_app_settings(
                    app.engine.name, app.name, app.sgtk, context, app.engine.instance_name
                )
            finally:
                # Ignore any errors while looking for the settings
                WorkArea._settings_cache.add(context, app_settings or {})

        # No settings found, do nothing.
        if not app_settings:
            app.log_debug("No settings found.")
            return None

        if len(app_settings) == 1:
            return app_settings[0].get("settings")

        # There's more than one instance of that app for the engine instance, so we'll
        # need to deterministically pick one. We'll pick the one with the same
        # application instance name as the current app instance.
        for settings in app_settings:
            if settings.get("app_instance") == app.instance_name:
                return settings.get("settings")

        app.log_warning(
            "Looking for tk-multi-workfiles application settings in '%s' context"
            " yielded too many results (%s), none named '%s'." % (
                context,
                ", ".join([s.get("app_instance") for s in app_settings]),
                app.instance_name
            )
        )

        return None

    def _resolve_user_sandboxes(self, template):
        """
        Resolves user sandboxes on disk for a given template. Caches the result.

        :param template: Template for which to cache the users.

        :returns: List of users in the given sandbox.
        """
        if not template or not self._context:
            # don't have enough information to resolve users!
            return []

        # find all 'user' keys in the template:
        user_keys = get_template_user_keys(template)
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
        except TankError:
            # this probably means that there isn't anything in the path cache for this context
            # yet which also means no users have created folders therefore there are also no
            # user sandboxes!
            return []

        # make sure we have enough fields to perform a valid search - we should have all non-optional
        # keys apart from user keys:
        for key_name in search_template.keys.keys():
            if (key_name not in user_keys and
                    key_name not in ctx_fields and
                    not search_template.is_optional(key_name)):
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

