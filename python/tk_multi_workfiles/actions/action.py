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
Menu actions.
"""

import sgtk


class ActionBase(object):
    """
    Base class for Actions.
    """
    def __init__(self, label):
        """
        Constructor.

        :param label: Name of the action.
        """
        self._app = sgtk.platform.current_bundle()
        self._label = label

    @property
    def label(self):
        """
        :returns: The name of the action.
        """
        return self._label


class Action(ActionBase):
    """
    Base class for leaf actions, ie, actions that when selected execute a piece of logic. This logic
    is implemented in the execute method.
    """

    def execute(self, parent_ui):
        """
        Called when the user executes a given action. The default implementation raises a NotImplementedError.

        :raises NotImplementedError: Thrown if a derived class doesn't implement this method and the client invokes it.
        """
        raise NotImplementedError("Implementation of _execute() method missing for action '%s'" % self.label)


class ActionGroup(ActionBase):
    """
    Group of actions.
    """

    def __init__(self, label, actions):
        """
        Constructor.

        :param label: Name of the group of actions.
        :param actions: List of ActionBase actions.
        """
        ActionBase.__init__(self, label)
        self.__actions = actions[:]

    @property
    def actions(self):
        """
        :returns: List of ActionBase actions.
        """
        return self.__actions


class SeparatorAction(ActionBase):
    """
    Not an actual action but a hint to the UI that a separation should be shown.
    """
    def __init__(self):
        """
        Constructor.
        """
        ActionBase.__init__(self, "---")
