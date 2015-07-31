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

from .util import report_non_destroyed_qobjects, monitor_qobject_lifetime

class SignalWait(QtCore.QObject):
    """
    """
    def __init__(self, count=1):
        QtCore.QObject.__init__(self)
        self._count=count
        self._loop = QtCore.QEventLoop(self)
        monitor_qobject_lifetime(self._loop, "Signal wait event loop")

    def wait(self):
        if self._count > 0:
            self._loop.exec_()

    def finish(self):
        self._count -= 1
        if self._count == 0:
            self._loop.exit()

class TimedGc(QtCore.QObject):
    """
    """
    def __init__(self, parent=None):
        """
        """
        QtCore.QObject.__init__(self, parent)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._do_gc_collect)
        self._gc_enabled = False

    def start(self):
        """
        """
        self._gc_enabled = gc.isenabled()
        if self._gc_enabled:
            gc.disable()
            self._timer.start(10000)

    def stop(self):
        """
        """
        self._timer.stop()
        if self._gc_enabled:
            # re-enable garbage collection:
            gc.enable()
        # and do one last collect
        gc.collect()

    def _do_gc_collect(self):
        """
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
        # create a SignalWait instance now and connect it up to the application.  This is to
        # ensure that when we later call it using wait.wait() it doesn't hang forever if the
        # application event loop has finished!
        wait = SignalWait()
        q_app = QtGui.QApplication.instance()
        if q_app and isinstance(q_app, QtGui.QApplication):
            # note, in Nuke 6.3/PySide 1.0.9 QtGui.QApplication.instance() rather unhelpfully returns
            # a QtCore.QCoreApplication instance!
            if q_app.quitOnLastWindowClosed():
                # we don't want to wait if the event loop has finished cause we'll be waiting forever!
                q_app.lastWindowClosed.connect(wait.finish)

        # grab the pre-run memory info:
        num_objects_before = len(gc.get_objects())
        bytes_before = 0
        if sys.platform == "Darwin":
            import resource
            bytes_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0

        # run the function:
        res = func(*args, **kwargs)

        # wait for any QObjects to be cleaned up in the main event loop:
        QtCore.QTimer.singleShot(100, wait.finish)
        wait.wait()
        wait = None
        
        # report any non-destroyed QObjects:
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
    """
    @staticmethod
    def show_file_open_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_save_dlg()

    @dbg_info
    @managed_gc
    def _show_file_open_dlg(self):
        """
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
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_save_form import FileSaveForm
            app.engine.show_modal("File Save", app, FileSaveForm)
        except:
            app.log_exception("Failed to create File Save dialog!")

