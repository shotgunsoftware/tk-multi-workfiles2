# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import types
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore

OPEN_FILE_ACTION, SAVE_FILE_AS_ACTION, NEW_FILE_ACTION, VERSION_UP_FILE_ACTION = range(4)

def _do_scene_operation(app, action, context, operation, path=None, version=0, read_only=False, result_types=None):
    """
    Do the specified scene operation with the specified args by executing the scene operation hook
    
    :param app:          The App bundle that is running this code
    :param action:       The parent action that this scene operation is part of
    :param context:      The context that this operation is being run for
    :param operation:    The scene operation to perform
    :param path:         If the scene operation requires a file path then this is it
    :param version:      The version of the file that should be opened (for open operation only)
    :param read_only:    True if the file should be opened read-only (for open operation only)
    :param result_types: The acceptable tuple of result types for the hook.
    :returns:            Varies depending on the hook operation
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
    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        result = app.execute_hook("hook_scene_operation", 
                                  operation=operation, 
                                  file_path=path, 
                                  context=context, 
                                  parent_action=action_str, 
                                  file_version=version, 
                                  read_only=read_only)     
    except TankError, e:
        # deliberately filter out exception that used to be thrown 
        # from the scene operation hook but has since been removed
        if not str(e).startswith("Don't know how to perform scene operation '"):
            # just re-raise the exception:
            raise
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    # validate the result if needed:
    if result_types and not isinstance(result, result_types):
        raise TankError(
            ("Unexpected type returned from 'hook_scene_operation' "
             "for operation '%s' - expected one of (%s) but returned '%s'")
            % (
                operation,
                ", ".join([rtype.__name__ for rtype in result_types]),
                type(result).__name__
            )
        )

    return result
    
def get_current_path(app, action, context):
    """
    Use hook to get the current work/scene file path
    """
    app.log_debug("Retrieving current scene path...")
    return _do_scene_operation(app, action, context, "current_path", result_types=(basestring,))
    
def reset_current_scene(app, action, context):
    """
    Use hook to clear the current scene
    """
    app.log_debug("Resetting the current scene via hook")
    return _do_scene_operation(app, action, context, "reset", result_types=(bool,))
    
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

def open_file(app, action, context, path, version, read_only):
    """
    Use hook to open the specified file.
    """
    # do open:
    app.log_debug("Opening file '%s' via hook" % path)
    return _do_scene_operation(app, action, context, "open", path, version, read_only, result_types=(bool, types.NoneType))    
    

     