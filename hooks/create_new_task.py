# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Task creation hook.
"""

import sgtk

HookClass = sgtk.get_hook_baseclass()


class CreateNewTaskHook(HookClass):
    """
    Hook called to create a task for a given entity and step.
    """

    def create_task_name_validator(self):
        """
        Create a QtGui.QValidator instance that will be used by the task name field to interactively
        inform if the name is valid or not. The caller will take ownership of the validator.

        For example, this simple validator will prevent the user from entering spaces in the field.

        .. code-block:: python

            class _Validator(QtGui.QValidator):

                def validate(self, text, pos):
                    if " " in text:
                        return QtGui.QValidator.Intermediate, text.replace(" ", ""), pos - 1
                    else:
                        return QtGui.QValidator.Acceptable, text, pos

        .. note:: The calling convention for fixup and validate have been modified to make them more pythonic.
            http://pyside.readthedocs.org/en/1.2.2/sources/pyside/doc/pysideapi2.html?highlight=string#qstring

        :returns: A QtGui.QValidator derived object.
        """
        return None

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

        :returns: The created task.
        :rtype: dictionary with keys 'step', 'project', 'entity', 'content' and 'task_assignees' if
            'assigned_to' was set.

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

        return sg_result
