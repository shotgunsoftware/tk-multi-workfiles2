# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from collections import defaultdict

import sgtk
from sgtk.platform.qt import QtCore, QtGui

logger = sgtk.platform.get_logger(__name__)


class StepListWidget(QtCore.QObject):
    """
    A list of Shotgun Pipeline steps per entity type.
    """
    _step_list = None
    step_filter_changed = QtCore.Signal(list) # List of SG step dictionaries

    def __init__(self, list_widget):
        """
        Instantiate a StepListWidget, collect all Pipeline steps from Shotgun if
        they are not already cached.

        :param list_widget: A :class:`QtGui.QListWidget` instance. It is assumed
                            it has a direct QWidget parent which can be shown or
                            hidden when showing steps for a given Entity type is
                            needed or not needed.
        """
        super(StepListWidget, self).__init__()
        self._list_widget = list_widget
        self._cache_step_list()
        self._step_widgets = defaultdict(list)

    @classmethod
    def _cache_step_list(cls):
        """
        Retrieve all Steps from Shotgun and cache them, if they were not already
        cached. Do nothing if they were already cached.
        """
        if cls._step_list is None:
            shotgun = sgtk.platform.current_bundle().shotgun
            sg_steps = shotgun.find(
                "Step",
                [],
                ["code", "entity_type", "color"],
                order=[{"field_name": "code", "direction": "asc"}]
            )
            # Build a dictionary for indexing by the entity_type
            cls._step_list = defaultdict(list)
            for sg_step in sg_steps:
                cls._step_list[sg_step["entity_type"]].append(sg_step)

    def set_widgets_for_entity_type(self, entity_type):
        """
        Refresh the Step widgets being displayed for the given Entity type.

        If the Entity type is not supported or is None, the whole Step UI is hidden.
        The current selection for the given Entity type is emitted, an empty list
        is emitted for un-supported Entity types.

        :param str entity_type: A Shotgun Entity type or None.
        """
        logger.info("Switching to %s" % entity_type)
        if entity_type == "Task":
            # Show all steps
            for linked_entity_type in self._step_list:
                self._ensure_widgets_for_entity_type(linked_entity_type)
            for item_row in range(0, self._list_widget.count()):
                self._list_widget.setRowHidden(item_row, False)
            self._list_widget.parent().setVisible(True)
        elif entity_type is None or entity_type not in self._step_list:
            self._list_widget.parent().setVisible(False)
            #self.step_filter_changed.emit([])
        else:
            self._ensure_widgets_for_entity_type(entity_type)
            selection = []
            for item_row in range(0, self._list_widget.count()):
                item = self._list_widget.item(item_row)
                item_step = item.data(QtCore.Qt.UserRole)
                if entity_type != item_step["entity_type"]:
                    self._list_widget.setRowHidden(item_row, True)
                else:
                    self._list_widget.setRowHidden(item_row, False)
                if self._list_widget.itemWidget(item).isChecked():
                    selection.append(item_step)
            #self.step_filter_changed.emit(selection)
            self._list_widget.parent().setVisible(True)

    def _retrieve_selection(self, value):
        """
        Retrieve the whole selection and emit it.

        Typically triggered when one of the Step item is toggled on/off.
        """
        selection = []
        for item_row in range(0, self._list_widget.count()):
            item = self._list_widget.item(item_row)
            item_step = item.data(QtCore.Qt.UserRole)
            if self._list_widget.itemWidget(item).isChecked():
                selection.append(item_step)
        self.step_filter_changed.emit(selection)

    def _ensure_widgets_for_entity_type(self, entity_type):
        widgets = self._step_widgets[entity_type]
        if widgets:
            return widgets
        # Not already built, let's do it now
        for step in self._step_list[entity_type]:
            widget = QtGui.QCheckBox(step["code"])
            pixmap = QtGui.QPixmap(100, 100)
            # Get the Step color and add a bit of transparency to the
            # color otherwise it is too bright.
            color = [int(x) for x in step["color"].split(",")] + [200]
            pixmap.fill(QtGui.QColor(*color))
            widget.setIcon(pixmap)
            widget.toggled.connect(self._retrieve_selection)
            item = QtGui.QListWidgetItem("", self._list_widget)
            item.setData(QtCore.Qt.UserRole, step)
            self._list_widget.setItemWidget(item, widget)
            self._step_widgets[entity_type].append(widget)
        return self._step_widgets[entity_type]