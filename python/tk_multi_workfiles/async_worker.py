# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank.platform.qt import QtCore, QtGui 

class AsyncWorker(QtCore.QThread):
    """
    Background worker that executes a callback
    in a separate thread when requested.
    """

    # Indicates that this worker class has been fixed to stop 
    # gc of QThread from resulting in a crash.  This happens 
    # when the mutex object had been gc'd but the thread is 
    # still trying to acces it - the fix is to wait for the 
    # thread to terminate before returning from 'stop()'
    _SGTK_IMPLEMENTS_QTHREAD_CRASH_FIX_=True

    # signal emitted when some work has been done.
    # arguments are (data, result)
    work_done = QtCore.Signal(object, object)

    def __init__(self, worker_cb, parent=None):
        """
        Construction
        """
        QtCore.QThread.__init__(self, parent)

        self._worker_cb = worker_cb

        self._mutex = QtCore.QMutex()
        self._wait_condition = QtCore.QWaitCondition()

        self._data = None
        self._stop_work = False

    def do(self, data):
        """
        Call to do some work using the data provided
        """
        try:
            self._mutex.lock()
            self._data = data
            self._wait_condition.wakeAll()
        finally:
            self._mutex.unlock()
        
    def stop(self, wait_for_completion=True):
        try:
            self._mutex.lock()
            self._stop_work = True
            self._wait_condition.wakeAll()
        finally:
            self._mutex.unlock()
            
        # wait for completion..
        if wait_for_completion:
            self.wait()
            
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, type, value, traceback):
        self.stop()
            
    def run(self):
        """
        Internal function called when start() is called
        """        
        while True:
            
            data = None
            try:
                self._mutex.lock()
                if self._stop_work:
                    break
                
                if self._data is None:
                    # wait for version to be changed:
                    self._wait_condition.wait(self._mutex)
                
                if self._stop_work:
                    break
                
                data = self._data
                self._data = None
            finally:
                self._mutex.unlock()
                
            # do the work:
            try:
                result = self._worker_cb(data)
                
                # emit result:        
                self.work_done.emit(data, result)
            except Exception, e:
                # TODO: throwing an exception here will kill the thread
                # which isn't what we want - however, ignoring errors
                # isn't great either!
                print "Unhandled exception in worker thread: %s" % e
                pass
