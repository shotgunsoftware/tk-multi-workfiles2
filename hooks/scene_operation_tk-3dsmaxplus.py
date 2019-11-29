# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


try:
    import MaxPlus
except ImportError:
    pass

try:
    import pymxs
except ImportError:
    pass

import sgtk

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the current scene
    """

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """
        if operation == "current_path":
            # return the current scene path or an empty string.
            return _session_path() or ""
        elif operation == "open":
            # open the specified scene
            _open_file(file_path)
        elif operation == "save":
            # save the current scene:
            _save_file()
        elif operation == "save_as":
            # save the scene as file_path:
            _save_file(file_path)
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            _reset_scene()
            return True


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    if sgtk.platform.current_engine().supports_max_plus
        return MaxPlus.FileManager.GetFileNameAndPath()
    elif pymxs.runtime.maxFilePath and pymxs.runtime.maxFileName:
        return os.path.join(
            pymxs.runtime.maxFilePath,
            pymxs.runtime.maxFileName
        )
    else:
        return None


def _open_file(file_path):
    if sgtk.platform.current_engine().supports_max_plus:
        MaxPlus.FileManager.Open(file_path)
    else:
        pymxs.runtime.loadMaxFile(file_path)


def _save_file(file_path):
    if sgtk.platform.current_engine().supports_max_plus:
        if file_path is None:
            MaxPlus.FileManager.Save()
        else:
            MaxPlus.FileManager.Save(file_path)
    else:
        if file_path is None:
            pymxs.runtime.saveMaxFile()
        else:
            pymxs.runtime.saveMaxFile(file_path)


def _reset_scene():
    if sgtk.platform.current_engine().supports_max_plus:
        MaxPlus.FileManager.Reset(True)
    else:
        rt.resetMaxFile(rt.Name("noprompt"))
