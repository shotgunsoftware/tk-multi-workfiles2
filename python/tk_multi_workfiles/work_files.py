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
from sgtk.platform.qt import QtCore, QtGui 
from sgtk import TankError

from .util import report_non_destroyed_qobjects

class TimedGc(QtCore.QObject):
    """
    Helper class that disables cyclic garbage collection and runs it periodically
    on the main thread through use of a QTimer.  This is used to avoid Qt objects being
    gc'd from non-main threads which was causing instability older PySide/Python
    versions (Python 2.6 in Nuke 6 being one example).
    """
    def __init__(self, parent=None):
        """
        Construction

        :param parent:  The parent QObject for this instance
        """
        QtCore.QObject.__init__(self, parent)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._do_gc_collect)
        self._gc_enabled = False

    def start(self):
        """
        Disable the gc and start the timer
        """
        self._gc_enabled = gc.isenabled()
        if self._gc_enabled:
            gc.disable()
            self._timer.start(10000)

    def stop(self):
        """
        Stop the timer and re-enable the gc
        """
        self._timer.stop()
        if self._gc_enabled:
            # re-enable garbage collection:
            gc.enable()
        # and do one last collect
        gc.collect()

    def _do_gc_collect(self):
        """
        Slot triggered by the timer's timeout signal to perform
        a gc collect at the timed interval.
        """
        gc.collect()

def managed_gc(func):
    """
    Decorator function to disable cyclic garbage collection whilst the wrapped function is run.  
    Whilst it is running, gc.collect() is instead run on a timer - this ensure that it always 
    runs in the main thread to avoid gc issues with PySide/Qt objects being deleted from another, 
    non-main thread.
    """
    def wrapper(*args, **kwargs):
        timed_gc = TimedGc()
        timed_gc.start()
        try:
            return func(*args, **kwargs)
        finally:
            timed_gc.stop()
            timed_gc.deleteLater()
    return wrapper

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
            bytes_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0

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
            bytes_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
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
    @staticmethod
    def show_file_open_dlg():
        """
        Show the file open dialog
        """
        handler = WorkFiles()
        handler._show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        Show the file save dialog
        """
        handler = WorkFiles()
        handler._show_file_save_dlg()

    @dbg_info
    @managed_gc
    def _show_file_open_dlg(self):
        """
        Show the file open dialog
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_open_form import FileOpenForm
            #app.engine.show_dialog("File Open", app, FileOpenForm)
            app.engine.show_modal("File Open", app, FileOpenForm)
        except:
            app.log_exception("Failed to create File Open dialog!")

    @dbg_info
    @managed_gc
    def _show_file_save_dlg(self):
        """
        Show the file save dialog
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_save_form import FileSaveForm
            app.engine.show_modal("File Save", app, FileSaveForm)
        except:
            app.log_exception("Failed to create File Save dialog!")

