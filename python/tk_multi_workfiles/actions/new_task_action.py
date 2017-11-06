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
from sgtk.platform.qt import QtGui

from .action import Action
from ..new_task_form import NewTaskForm
from ..user_cache import g_user_cache


class NewTaskAction(Action):
    """
    This action creates a new task for a given entity.
    """

    def __init__(self, entity, step):
        """
        Constructor.

        :param entity: Entity for which a task needs to be created.
        :param step: Default pipeline step for the new task.
        """
        Action.__init__(self, "Create New Task")
        self._entity = entity
        self._step = step

    def execute(self, parent_ui):
        """
        Shows the task creation form and creates the task.

        :param parent_ui: Parent widget for the dialog.

        :returns: If True, task creation was completed, returns False otherwise.
        """
        if not self._entity:
            return False

        # show new task dialog:
        app = sgtk.platform.current_bundle()
        res, new_task_form = app.engine.show_modal("Create New Task", app, NewTaskForm, self._entity, self._step,
                                                   g_user_cache.current_user, parent_ui)

        if res != QtGui.QDialog.Accepted:
            return False

        try:
            from sgtk.util.metrics import EventMetric as EventMetric

            group = EventMetric.GROUP_TASKS
            pipeline_step=new_task_form._get_pipeline_step()
            task_name = pipeline_step.get("code","unknown") # Why not new_task_form._get_task_name() ?
            entity_type = pipeline_step.get("type", "Unknown")
            method = "Form" # since this was created from the Qt widget
            fields_used = []
            properties = sgtk.platform.current_engine()._get_metrics_properties()
            properties.update({
                "Linked Entity Type": entity_type,
                "Method": method,
                "Task Name": task_name,
                "Fields Used": fields_used
            })

            # Log usage statistics about the Shotgun Desktop executable and the desktop startup.
            EventMetric.log(group, "Created Task", properties=properties)
        except ImportError as e:
            # ignore all errors. ex: using a core that doesn't support metrics
            pass

        return True
