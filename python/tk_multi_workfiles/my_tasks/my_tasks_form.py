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

from ..util import monitor_qobject_lifetime
from ..entity_tree.entity_tree_form import EntityTreeForm
from ..framework_qtwidgets import ViewItemDelegate

from sgtk.platform.qt import QtCore, QtGui


class MyTasksForm(EntityTreeForm):
    """
    My Tasks widget class
    """

    # emitted when an entity is double clicked
    task_double_clicked = QtCore.Signal(object)

    def __init__(self, tasks_model, allow_task_creation, parent):
        """
        Construction

        :param model:   The Shotgun Model this widget should connect to
        :param parent:  The parent QWidget for this control
        """
        EntityTreeForm.__init__(
            self,
            tasks_model,
            "My Tasks",
            allow_task_creation,
            tasks_model.extra_display_fields,
            parent,
        )

        # There is no need for the my tasks toggle.
        self._ui.my_tasks_cb.hide()

        # Task status filter
        self._ui.task_status_combo.show()

        # Sets an item delete to show a list of tiles for tasks instead of nodes in a tree.
        # Make sure we keep a reference to the delegate otherwise things may crash later on
        self._item_delegate = self._create_delegate(tasks_model, self._ui.entity_tree)

        monitor_qobject_lifetime(self._item_delegate)
        self._ui.entity_tree.setItemDelegate(self._item_delegate)

        self._ui.entity_tree.doubleClicked.connect(self._on_double_clicked)

        self._sort_button_setup()

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

    def _on_double_clicked(self, idx):
        """
        Emits the entity that was double clicked.
        """
        entity_details = self._get_entity_details(idx)
        self.task_double_clicked.emit(entity_details)

    def _create_delegate(self, model, view):
        """Create the delegate for the tree view."""

        delegate = ViewItemDelegate(view)

        delegate.thumbnail_role = model.VIEW_ITEM_THUMBNAIL_ROLE
        delegate.header_role = model.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = model.VIEW_ITEM_SUBTITLE_ROLE
        delegate.text_role = model.VIEW_ITEM_TEXT_ROLE
        delegate.icon_role = model.VIEW_ITEM_ICON_ROLE
        delegate.expand_role = model.VIEW_ITEM_EXPAND_ROLE
        delegate.width_role = model.VIEW_ITEM_WIDTH_ROLE
        delegate.height_role = model.VIEW_ITEM_HEIGHT_ROLE
        delegate.loading_role = model.VIEW_ITEM_LOADING_ROLE
        delegate.separator_role = model.VIEW_ITEM_SEPARATOR_ROLE

        delegate.text_rect_valign = ViewItemDelegate.CENTER
        delegate.override_item_tooltip = True
        delegate.thumbnail_padding = 6

        delegate.item_height = 64
        delegate.thumbnail_padding = ViewItemDelegate.Padding(7, 0, 7, 7)
        delegate.thumbnail_uniform = True

        view.setMouseTracking(True)
        view.setRootIsDecorated(False)

        return delegate

    def _sort_button_setup(self):
        self.sort_menu_button = QtGui.QPushButton()
        self.sort_menu_button.setText("Sort")
        self.sort_menu_button.setObjectName("sort_menu_button")
        self.sort_menu_button.setStyleSheet("border :None")
        self._ui.horizontalLayout.addWidget(self.sort_menu_button)
