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

from sgtk.platform.qt import QtCore, QtGui
from .my_task_item_delegate import MyTaskItemDelegate
from ..util import monitor_qobject_lifetime
from ..entity_tree.entity_tree_form import EntityTreeForm
from .my_tasks_proxy_model import MyTasksProxyModel

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

        sort_data = tasks_model.sort_data
        self.chosen_sort_option = 0

        if sort_data:

            self.sort_model = MyTasksProxyModel(self)
            self.sort_model.filter_by_fields = []
            self.sort_model.setDynamicSortFilter(True)
            self.sort_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
            # we set the sort order, but we may actually perform a different sort order
            # in the proxy model on a per field basis
            self.sort_model.sort(0, QtCore.Qt.AscendingOrder)

            # default to the first sort option.
            sort_option = sort_data[0]
            self._set_sort_option(sort_option)

            sort_options_menu = QtGui.QMenu(self._ui.sort_tbn)
            self._ui.sort_tbn.setMenu(sort_options_menu)
            self._sort_menu_lambdas = []
            for sort_option in sort_data:

                sort_callable = lambda data=sort_option : self._set_sort_option(data)
                self._sort_menu_lambdas.append(sort_callable)

                action = QtGui.QAction(sort_option['name'], sort_options_menu)
                action.triggered.connect(sort_callable)
                sort_options_menu.addAction(action)

            monitor_qobject_lifetime(self.sort_model, "My Tasks Sort model")
            self.sort_model.setSourceModel(tasks_model)
            self._ui.entity_tree.setModel(self.sort_model)

            self._ui.sort_tbn.show()

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

    def _set_sort_option(self, sort_option):
        sort_fields = sort_option['sort_fields']
        self.sort_model.primary_sort_field = sort_fields[0]

        if len(sort_fields) > 1:
            self.sort_model.sort_by_fields = sort_fields[1:]
        else:
            self.sort_model.sort_by_fields = []

        self._ui.sort_tbn.setText("Sort By: %s" % (sort_option["name"]))
        self.sort_model.invalidate()