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
Implementation of the my tasks list widget consisting of a list view displaying the contents
of a Shotgun data model of my tasks, a text search and a filter control.
"""

from .my_task_item_delegate import MyTaskItemDelegate
from ..util import monitor_qobject_lifetime
from ..entity_tree.entity_tree_form import EntityTreeForm


class MyTasksForm(EntityTreeForm):
    """
    My Tasks widget class
    """

    def __init__(self, tasks_model, allow_task_creation, parent):
        """
        Construction

        :param model:   The Shotgun Model this widget should connect to
        :param parent:  The parent QWidget for this control
        """
        EntityTreeForm.__init__(
            self, tasks_model, "My Tasks", allow_task_creation, tasks_model.extra_display_fields, parent
        )

        # There is no need for the my tasks toggle.
        self._ui.my_tasks_cb.hide()

        # Sets an item delete to show a list of tiles for tasks instead of nodes in a tree.
        self._item_delegate = None
        # create the item delegate - make sure we keep a reference to the delegate otherwise
        # things may crash later on!
        self._item_delegate = MyTaskItemDelegate(tasks_model.extra_display_fields, self._ui.entity_tree)
        monitor_qobject_lifetime(self._item_delegate)
        self._ui.entity_tree.setItemDelegate(self._item_delegate)

    def shut_down(self):
        """
        Clean up as much as we can to help the gc once the widget is finished with.
        """
        signals_blocked = self.blockSignals(True)
        try:
            EntityTreeForm.shut_down(self)
            # detach and clean up the item delegate:
            self._ui.entity_tree.setItemDelegate(None)
            if self._item_delegate:
                self._item_delegate.setParent(None)
                self._item_delegate.deleteLater()
                self._item_delegate = None
        finally:
            self.blockSignals(signals_blocked)
