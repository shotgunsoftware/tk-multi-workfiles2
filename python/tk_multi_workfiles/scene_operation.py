"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

import tank
from tank import TankError

[OPEN_FILE_ACTION, SAVE_FILE_AS_ACTION, NEW_FILE_ACTION, VERSION_UP_FILE_ACTION] = range(4)

def _do_scene_operation(app, action, context, operation, path=None, result_type=None):
    """
    Do the specified scene operation with the specified args
    """
    # determine action string for action:
    action_str = ""
    if action == OPEN_FILE_ACTION:
        action_str = "open_file"
    elif action == SAVE_FILE_AS_ACTION:
        action_str = "save_file_as"
    elif action == NEW_FILE_ACTION:
        action_str = "new_file"
    elif action == VERSION_UP_FILE_ACTION:
        action_str = "version_up"
    else:
        raise TankError("Unrecognised action %s for scene operation" % action)
    
    result = None
    try:
        result = app.execute_hook("hook_scene_operation", operation=operation, file_path=path, context=context, parent_action=action_str)     
    except TankError, e:
        # deliberately filter out exception that used to be thrown 
        # from the scene operation hook but has since been removed
        if not str(e).startswith("Don't know how to perform scene operation '"):
            # just re-raise the exception:
            raise
        
    # validate the result if needed:
    if result_type and (result == None or not isinstance(result, result_type)):
        raise TankError("Unexpected type returned from 'hook_scene_operation' for operation '%s' - expected '%s' but returned '%s'" 
                        % (operation, result_type.__name__, type(result).__name__))
    
    return result
    
def get_current_path(app, action, context):
    """
    Use hook to get the current work/scene file path
    """
    app.log_debug("Retrieving current scene path...")
    return _do_scene_operation(app, action, context, "current_path", result_type=basestring)
    
def reset_current_scene(app, action, context):
    """
    Use hook to clear the current scene
    """
    app.log_debug("Resetting the current scene via hook")
    return _do_scene_operation(app, action, context, "reset", result_type=bool)
    
def prepare_new_scene(app, action, context):
    """
    Use the hook to do any preperation for
    the new scene
    """
    app.log_debug("Preparing the new scene via hook")
    return _do_scene_operation(app, action, context, "prepare_new")
    
def save_file(app, action, context, path=None):
    """
    Use hook to save the current file
    """
    if path != None:
        app.log_debug("Saving the current file as '%s' with hook" % path)
        _do_scene_operation(app, action, context, "save_as", path)  
    else:
        app.log_debug("Saving the current file with hook")
        _do_scene_operation(app, action, context, "save")

def open_file(app, action, context, path):
    """
    Use hook to open the specified file.
    """
    # do open:
    app.log_debug("Opening file '%s' via hook" % path)
    _do_scene_operation(app, action, context, "open", path)    
    

     