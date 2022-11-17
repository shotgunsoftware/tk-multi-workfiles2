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
from tank_vendor import six
from sgtk.platform.qt import QtGui, QtCore

from .framework_qtwidgets import MessageBox

(
    OPEN_FILE_ACTION,
    SAVE_FILE_AS_ACTION,
    NEW_FILE_ACTION,
    VERSION_UP_FILE_ACTION,
    CHECK_REFERENCES_ACTION,
) = range(5)


def _do_scene_operation(
    app,
    action,
    context,
    operation,
    path=None,
    version=0,
    read_only=False,
    result_types=None,
):
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
    elif action == CHECK_REFERENCES_ACTION:
        action_str = "check_references"
    else:
        raise TankError("Unrecognised action %s for scene operation" % action)

    result = None
    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        result = app.execute_hook(
            "hook_scene_operation",
            operation=operation,
            file_path=path,
            context=context,
            parent_action=action_str,
            file_version=version,
            read_only=read_only,
        )
    except TankError as e:
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
            (
                "Unexpected type returned from 'hook_scene_operation' "
                "for operation '%s' - expected one of (%s) but returned '%s'"
            )
            % (
                operation,
                ", ".join([rtype.__name__ for rtype in result_types]),
                type(result).__name__,
            )
        )

    return result


def get_current_path(app, action, context):
    """
    Use hook to get the current work/scene file path
    """
    app.log_debug("Retrieving current scene path...")
    return _do_scene_operation(
        app, action, context, "current_path", result_types=(six.string_types,)
    )


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
    return _do_scene_operation(
        app,
        action,
        context,
        "open",
        path,
        version,
        read_only,
        result_types=(bool, type(None)),
    )


def check_references(app, action, context, parent_ui):
    """
    Use hook to check that all references in the current file exist.

    If the hook did not check for references (returned None), then a default operation to
    check for references will be performed using the Scene Breakdown2 API (if it is
    available via the engine apps).

    :return: The list of references that are not up to date with the latest version. None is
        returned if the references could not be checked.
    :rtype: list | None
    """

    app.log_debug("Checking references in the current file with hook")

    # First check if there is a custom hook to check references
    result = _do_scene_operation(
        app,
        action,
        context,
        "check_references",
        result_types=(list, bool, type(None)),
    )

    # Return the result, if the custom hook returned a value of type list, otherwise
    # assume that the default reference check should be performed.
    if isinstance(result, list):
        return result

    # Set the cursor to waiting while references are being checked
    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

    try:
        # No result returned, get the breakdown app to perform the default operation to check
        # references
        breakdown2_app = app.engine.apps.get("tk-multi-breakdown2")
        if not breakdown2_app:
            return None

        # Use the breakdown manager to get the file references, then check if any are out of date
        manager = breakdown2_app.create_breakdown_manager()
        file_items = manager.scan_scene()
        result = []
        for file_item in file_items:
            manager.get_latest_published_file(file_item)
            if (
                not file_item.highest_version_number
                or file_item.sg_data["version_number"]
                < file_item.highest_version_number
            ):
                result.append(file_item)

        if result:
            # Out of date references were found, prompt the user how to handle them
            msg_box = MessageBox()
            msg_box.setWindowTitle("Reference Check")
            msg_box.set_text("Found out of date references in current scene.")
            msg_box.set_detailed_text(
                "\n".join(
                    [
                        (fi.sg_data.get("name") if fi.sg_data else fi.path) or fi.path
                        for fi in result
                    ]
                )
            )
            msg_box.set_always_show_details(True)
            open_button = msg_box.add_button(
                "Open in Breakdown", MessageBox.ACCEPT_ROLE
            )
            ignore_button = msg_box.add_button("Ignore", MessageBox.REJECT_ROLE)
            update_all_button = msg_box.add_button("Update All", MessageBox.APPLY_ROLE)
            msg_box.set_default_button(update_all_button)

            # Restore the cursor temporarily while user interacts with the dialog
            QtGui.QApplication.restoreOverrideCursor()
            try:
                msg_box.exec_()
            finally:
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            if msg_box.button_clicked == update_all_button:
                # Update all references to the latest version
                for file_item in result:
                    manager.update_to_latest_version(file_item)
            elif msg_box.button_clicked == open_button:
                # Open the breakdown app to see the out of date references in more details, where
                # the user can manually fix any, if desired
                breakdown2_app.show_dialog()
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    return result
