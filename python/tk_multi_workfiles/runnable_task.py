# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""
import traceback
import time
import threading

import sgtk
from sgtk.platform.qt import QtCore

class RunnableTask(QtCore.QRunnable, QtCore.QObject):
    """
    """
    completed = QtCore.Signal(object, object)
    failed = QtCore.Signal(object, object)
    skipped = QtCore.Signal(object)

    _next_task_id = 0
    def __init__(self, func, upstream_tasks=None, **kwargs):
        """
        """
        QtCore.QRunnable.__init__(self)
        QtCore.QObject.__init__(self)
        
        self._func = func
        self._input_kwargs = kwargs
                
        self._upstream_tasks = []
        upstream_tasks = upstream_tasks or []
        for task in upstream_tasks:
            self.add_upstream_task(task)
                
        task_id = RunnableTask._next_task_id
        RunnableTask._next_task_id = RunnableTask._next_task_id + 1
        self._id = task_id
        
        self._mutex = QtCore.QMutex()
        self._is_runnable = True
        self._is_queued = False 
        
    def __repr__(self):
        return "%s -> %s" % (self._id, self._upstream_tasks)
        
    @property
    def id(self):
        return self._id

    # @property
    def _get_is_runnable(self):
        self._mutex.lock()
        try:
            return self._is_runnable
        finally:
            self._mutex.unlock()
    # @is_runnable.setter
    def _set_is_runnable(self, value):
        self._mutex.lock()
        try:
            self._is_runnable = value
        finally:
            self._mutex.unlock()
    is_runnable=property(_get_is_runnable, _set_is_runnable)  
        
    def start(self):
        """
        """
        if self._upstream_tasks:
            for task in self._upstream_tasks:
                task.start()
        else:
            should_start = False
            self._mutex.lock()
            try:
                if not self._is_queued:
                    should_start = True
                    self._is_queued = True
            finally:
                self._mutex.unlock()
                
            if should_start:
                #print "Starting task [%s] %s" % (self.id, self._func.__name__)
                QtCore.QThreadPool.globalInstance().start(self)
    
    def stop(self):
        """
        """
        for task in self._upstream_tasks:
            task.stop()
        # just use a flag to indicate that this task shouldn't be run!
        self.is_runnable = False
        
    def autoDelete(self):
        """
        """
        # always let Python manage the lifetime of these objects!
        return False        
        
    def add_upstream_task(self, task):
        """
        """
        if task not in self._upstream_tasks:
            self._upstream_tasks.append(task)
            task.completed.connect(self._on_upstream_task_completed)
            task.failed.connect(self._on_upstream_task_failed)
            task.skipped.connect(self._on_upstream_task_skipped)
        
    def _on_upstream_task_completed(self, task, result):
        """
        """
        if task not in self._upstream_tasks:
            return

        #print "[%s] %s completed, res: %s" % (task.id, task._func.__name__, result)

        # disconnect from this task:
        self._upstream_tasks.remove(task)
        
        # append result to input args for this task:
        self._input_kwargs = dict(self._input_kwargs.items() + result.items())
        
        # if we have no more upstream tasks left then we can add this task to be processed:
        if not self._upstream_tasks:
            # ok, so now we're ready to start this task!
            self.start()
        
    def _on_upstream_task_failed(self, task, msg):
        """
        """
        if task not in self._upstream_tasks:
            return

        #print "[%s] %s failed" % (task.id, task._func.__name__)

        # clear out upstream tasks:
        self._upstream_tasks = []
        
        # if any upstream task failed then this task has also failed!
        self.failed.emit(self, msg)

    def _on_upstream_task_skipped(self, task):
        """
        """
        if task not in self._upstream_tasks:
            return

        #print "[%s] %s skipped" % (task.id, task._func.__name__)

        # clear out upstream tasks:
        self._upstream_tasks = []
        
        # if any upstream task was skipped then this task will also be skipped!
        self.skipped.emit(self)

    def run(self):
        """
        """
        if not self.is_runnable:
            # just skip this task
            self.skipped.emit(self)
            return
        
        try:
            # run the function with the provided args
            st = time.time()
            result = self._func(**self._input_kwargs) or {}
            end = time.time()
            app = sgtk.platform.current_bundle()
            if app:
                app.log_debug("[%0.2f] Task [%s] %s took %0.2fs" % (time.time(), self.id, self._func.__name__, end-st))
            
            if not isinstance(result, dict):
                # unsupported result type!
                raise TankError("Non-dictionary result type '%s' returned from function '%s'!" 
                                % (type(result), self._func.__name__))
                
            self.completed.emit(self, result)
        except Exception, e:
            tb = traceback.format_exc()
            self.failed.emit(self, "%s, %s" % (str(e), tb))