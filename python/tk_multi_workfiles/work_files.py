# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import gc
import resource

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

def dbg_watch_memory(func):
    def wrapper(*args, **kwargs):
        #import PySide
        #print "PySide v%s" % PySide.__version__
        #print "Qt v%s" % QtCore.__version__

        # grab the pre-run info:
        num_objects_before = len(gc.get_objects())
        bytes_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0

        # run the function:
        res = func(*args, **kwargs)

        # cleanup and grab the post-run info:
        gc.collect()
        bytes_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
        num_objects_after = len(gc.get_objects())

        # and report any difference:
        bytes_diff = bytes_after - bytes_before
        obj_diff = num_objects_after - num_objects_before
        msg = ("Memory before: %0.2fMb, current: %0.2fMb, leaked: %0.2fMb (%d new Python objects)" 
               % (bytes_before, bytes_after, bytes_diff, obj_diff))
        app = sgtk.platform.current_bundle()
        app.log_debug(msg)
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

    @managed_gc
    @dbg_watch_memory
    def _show_file_open_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_open_form import FileOpenForm
            #app.engine.show_dialog("File Open", app, FileOpenForm)
            app.engine.show_modal("File Open", app, FileOpenForm)

            # run a separate event loop for a few ms whilst the main event loop processes
            # any remaining deleteLater calls for any monitored QObjects and then report
            # any qobjects that haven't been destroyed
            wait = SignalWait()
            QtCore.QTimer.singleShot(100, wait.finish)
            wait.wait()
            report_non_destroyed_qobjects()
        except:
            app.log_exception("Failed to create File Open dialog!")

    @managed_gc
    @dbg_watch_memory
    def _show_file_save_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_save_form import FileSaveForm
            app.engine.show_modal("File Save", app, FileSaveForm)

            # run a separate event loop for a few ms whilst the main event loop processes
            # any remaining deleteLater calls for any monitored QObjects and then report
            # any qobjects that haven't been destroyed
            wait = SignalWait()
            QtCore.QTimer.singleShot(100, wait.finish)
            wait.wait()
            report_non_destroyed_qobjects()
        except:
            app.log_exception("Failed to create File Save dialog!")

