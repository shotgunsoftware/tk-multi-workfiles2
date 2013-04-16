"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

import tank
from tank.platform.qt import QtCore, QtGui 

class AsyncWorker(QtCore.QThread):
    """
    Background worker that executes a callback
    in a separate thread when requested.
    """

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
        with QtCore.QMutexLocker(self._mutex):
            self._data = data
            self._wait_condition.wakeAll()
        
    def stop(self):
        with QtCore.QMutexLocker(self._mutex):
            self._stop_work = True
            self._wait_condition.wakeAll()
            
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
            with QtCore.QMutexLocker(self._mutex):
                if self._stop_work:
                    break
                
                if self._data is None:
                    # wait for version to be changed:
                    self._wait_condition.wait(self._mutex)
                
                if self._stop_work:
                    break
                
                data = self._data
                self._data = None
                
            # do the work:
            try:
                result = self._worker_cb(data)
                
                # emit result:        
                self.work_done.emit(data, result)
            except Exception, e:
                # TODO: throwing an exception here will kill the thread
                # which isn't what we want - however, ignoring errors
                # isn't great either!
                print "%s" % e
                pass
            
            
            
            
            