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

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore

from .action import Action
from ..new_task_form import NewTaskForm
from ..user_cache import g_user_cache

class NewTaskAction(Action):
    """
    """

    def __init__(self, entity, step):
        """
        """
        Action.__init__(self, "Create New Task")
        self._entity = entity
        self._step = step

    def execute(self, parent_ui):
        """
        """
        if not self._entity:
            return False

        # show new task dialog:
        app = sgtk.platform.current_bundle()
        res, new_task_form = app.engine.show_modal("Create New Task", app, NewTaskForm, self._entity, self._step, 
                                                   g_user_cache.current_user)
        if res != QtGui.QDialog.Accepted:
            return False
        
        # get details from new_task_form:
        entity = new_task_form.entity
        assigned_to = new_task_form.assigned_to
        pipeline_step = new_task_form.pipeline_step
        task_name = new_task_form.task_name
    
        # create the task:    
        try:
            self._create_new_task(task_name, pipeline_step, entity, assigned_to)
            return True
        except TankError, e:
            QtGui.QMessageBox.warning(parent_ui,
                                  "Failed to create new task!",
                                  ("Failed to create a new task '%s' for pipeline step '%s' on entity '%s %s':\n\n%s" 
                                   % (task_name, pipeline_step.get("code"), entity["type"], entity["code"], e)))
    
    
    def _create_new_task(self, name, pipeline_step, entity, assigned_to=None):
        """
        Create a new task with the specified information
        :return: Returns the newly created task
        """
        app = sgtk.platform.current_bundle()
        
        # construct the data for the new Task entity:
        data = {
                "step":pipeline_step,
                "project":app.context.project,
                "entity":entity,
                "content":name
        }
        if assigned_to:
            data["task_assignees"] = [assigned_to]
        
        # create the task:
        sg_result = app.shotgun.create("Task", data)
        if not sg_result:
            raise TankError("Failed to create new task - reason unknown!") 
        
        # try to set it to IP - not all studios use IP so be careful!
        try:
            app.shotgun.update("Task", sg_result["id"], {"sg_status_list": "ip"})
        except:
            pass
        
        return sg_result
    