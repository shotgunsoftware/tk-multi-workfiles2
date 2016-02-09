# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import gc

import sgtk
from sgtk.platform.qt import QtCore

from .util import report_non_destroyed_qobjects


def dbg_info(func):
    """
    Decorator function used to track memory and other useful debug information around the file-open
    and file-save modal dialog calls.  If debug is enabled, this will print out a list of monitored
    QObject's that aren't destroyed correctly together with some Python memory/object stats.

    Note that the list of QObjects is misleading if the QApplication is set to close when the last
    window is closed and the dialog is the last window.
    """
    def wrapper(*args, **kwargs):
        """
        """
        # grab the pre-run memory info:
        num_objects_before = len(gc.get_objects())
        bytes_before = 0
        if sys.platform == "Darwin":
            import resource
            bytes_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0

        # run the function:
        res = func(*args, **kwargs)

        # report any non-destroyed QObjects:
        # Note, this will usually run before the main objects have been destroyed by the
        # event loop so it's important to cross-check the output with subsequent lines.
        report_non_destroyed_qobjects()

        # cleanup and grab the post-run memory info:
        gc.collect()
        bytes_after = 0
        if sys.platform == "Darwin":
            bytes_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
        num_objects_after = len(gc.get_objects())

        # and report any difference in memory usage:
        bytes_diff = bytes_after - bytes_before
        obj_diff = num_objects_after - num_objects_before
        msg = ("Memory before: %0.2fMb, current: %0.2fMb, leaked: %0.2fMb (%d new Python objects)"
               % (bytes_before, bytes_after, bytes_diff, obj_diff))
        app = sgtk.platform.current_bundle()
        app.log_debug(msg)

        # return the result:
        return res
    return wrapper


class WorkFiles(object):
    """
    Main entry point for all commands in the app.
    """

    def __init__(self):
        """
        Constructor.
        """
        app = sgtk.platform.current_bundle()
        app.log_debug("Synchronizing remote path cache...")
        app.sgtk.synchronize_filesystem_structure()
        app.log_debug("Path cache up to date!")

        # If the user wants to debug the dialog, show it modally and wrap it
        # with memory leak-detection code.
        if app.use_debug_dialog:
            self._dialog_launcher = dbg_info(app.engine.show_modal)
        else:
            self._dialog_launcher = app.engine.show_dialog

    @staticmethod
    def show_file_open_dlg():
        """
        Show the file open dialog
        """
        handler = WorkFiles()
        from .file_open_form import FileOpenForm
        handler._show_file_dlg("File Open", FileOpenForm)

    @staticmethod
    def show_file_save_dlg():
        """
        Show the file save dialog
        """
        handler = WorkFiles()
        from .file_save_form import FileSaveForm
        handler._show_file_dlg("File Save", FileSaveForm)

    def _show_file_dlg(self, dlg_name, form):
        """
        Shows the file dialog modally or not depending on the current DCC and settings.

        :param dlg_name: Title of the dialog.
        :param form: Factory for the dialog class.
        """
        app = sgtk.platform.current_bundle()
        try:
            self._dialog_launcher(dlg_name, app, form)
        except:
            app.log_exception("Failed to create %s dialog!" % dlg_name)
