# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk


class CreateNewTaskHook(sgtk.get_hook_baseclass()):
    """
    Hook called to create a task for a given entity and step.
    """
    def create_new_task(self, name, pipeline_step, entity, assigned_to=None):
        """
        Create a new task with the specified information.

        :param name: Name of the task to be created.

        :param pipeline_step: Pipeline step associated with the task.
        :type pipeline_step: dictionary with keys 'Type' and 'id'

        :param entity: Entity associated with this task.
        :type entity: dictionary with keys 'Type' and 'id'

        :param assigned_to: User assigned to the task. Can be None.
        :type assigned_to: dictionary with keys 'Type' and 'id'

        :raises sgtk.TankError: On error, during validation or creation, this method
            raises a TankError.
        """
        app = self.parent

        # construct the data for the new Task entity:
        data = {
            "step": pipeline_step,
            "project": app.context.project,
            "entity": entity,
            "content": name
        }
        if assigned_to:
            data["task_assignees"] = [assigned_to]

        # create the task:
        sg_result = app.shotgun.create("Task", data)
        if not sg_result:
            raise sgtk.TankError("Failed to create new task - reason unknown!")

        # try to set it to IP - not all studios use IP so be careful!
        try:
            app.shotgun.update("Task", sg_result["id"], {"sg_status_list": "ip"})
        except:
            pass
