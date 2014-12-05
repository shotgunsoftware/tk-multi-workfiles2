
import sgtk
from sgtk import TankError

def get_templates_for_context(app, context, keys):
    """
    Find templates for the given context.
    """
    settings = _get_app_settings_for_context(app, context)
    if not settings:
        raise TankError("Failed to find Work Files settings for context '%s'.\n\nPlease ensure that"
                        " the Work Files app is installed for the environment that will be used for"
                        " this context" % context)
    
    templates = {}
    for key in keys:
        template = app.get_template_from(settings, key)
        templates[key] = template
        
    return templates
        
    
def _get_app_settings_for_context(app, context):
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