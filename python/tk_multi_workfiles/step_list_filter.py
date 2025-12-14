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

settings_fw = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

# Settings name to save the Step filter list
_STEP_FILTERS_USER_SETTING = "step_filters"


def load_step_filters():
    """
    Load saved step filters.

    If the step filters were not saved yet, None is returned.

    :returns: None or a list of Shotgun Step dictionaries.
    """
    manager = settings_fw.UserSettings(sgtk.platform.current_bundle())
    step_filters = manager.retrieve(_STEP_FILTERS_USER_SETTING)
    return step_filters


def get_saved_step_filter():
    """
    Build a Shotgun query filter from saved Step filters.

    :returns: A Shotgun filter which can be directly added to a Shotgun query.
    """
    return get_filter_from_filter_list(load_step_filters())


def get_filter_from_filter_list(step_list):
    """
    Build a Shotgun query filter from a list of Steps.

    :returns: A Shotgun filter which can be directly added to a Shotgun query.
    """
    if step_list is None:
        # No Steps saved yet, allow all Steps.
        return []
    if not step_list:
        # All steps off, ask for a non-existing step
        return ["step.Step.id", "is", -1]
    # General case, build the filter from the Step list.
    step_filter = ["step.Step.id", "in", [x["id"] for x in step_list]]
    return step_filter


def get_steps_for_entity_type(entity_type):
    """
    Return cached Shotgun Step dictionaries for a given Entity type.

    The list is sourced from the StepCache, which respects the
    'project_visible_pipeline_steps' app setting and the current project context.

    :param str entity_type: A Shotgun Entity type (e.g. 'Asset', 'Shot').
    :returns: List of Step dictionaries with at least 'id', 'code',
              'entity_type' and optionally 'color'.
    """
    StepCache.ensure_loaded()
    return list(StepCache.get_step_map().get(entity_type, []))


class StepCache(object):
    """
    Cache Shotgun Pipeline Steps per entity type.
    """

    _step_map = None

    @classmethod
    def ensure_loaded(cls):
        """
        Populate the cache for the current context/settings.
        Computes a step map on accordingly.
        """
        bundle = sgtk.platform.current_bundle()
        all_steps = bundle.shotgun.find(
            "Step",
            [],
            ["code", "entity_type", "color"],
            order=[{"field_name": "code", "direction": "asc"}],
        )
        project = bundle.context.project
        if project and bundle.get_setting("project_visible_pipeline_steps", False):
            step_map = cls._build_project_visible_steps(
                all_steps, project["id"], sgtk.platform.current_engine().shotgun
            )
        else:
            step_map = defaultdict(list)
            for step in all_steps:
                step_map[step.get("entity_type")].append(step)
        cls._step_map = step_map

    @classmethod
    def get_step_map(cls):
        """
        Return the cached mapping: entity_type -> list of step dicts.
        """
        if cls._step_map is None:
            cls.ensure_loaded()
        return cls._step_map

    @classmethod
    def _build_project_visible_steps(cls, all_steps, project_id, engine_shotgun_api):
        """
        Build entity_type -> visible steps mapping for a project.
        """
        # Build lookup: entity_type -> { code -> step }
        steps_by_entity_and_code = defaultdict(dict)
        for step in all_steps:
            if step.get("code"):
                steps_by_entity_and_code[step.get("entity_type")][
                    step.get("code")
                ] = step
        step_map = defaultdict(list)
        for entity_type, step_lookup_by_code in steps_by_entity_and_code.items():
            schema_fields = engine_shotgun_api.schema_field_read(
                entity_type,
                project_entity={"type": "Project", "id": project_id},
            )
            visible_step_codes = []
            for field_name, field_schema in schema_fields.items():
                step_name = field_schema.get("name", {}).get("value")
                is_visible = field_schema.get("visible", {}).get("value")
                if (
                    field_name.startswith("step_")
                    and is_visible
                    and step_name
                    and step_name != "ALL TASKS"
                ):
                    visible_step_codes.append(step_name)
            if not visible_step_codes:
                continue
            visible_steps = [
                step_lookup_by_code[step_code]
                for step_code in visible_step_codes
                if step_code in step_lookup_by_code
            ]
            if not visible_steps:
                continue
            visible_steps.sort(key=lambda x: x.get("code") or "")
            step_map[entity_type].extend(visible_steps)
        return step_map


class StepListWidget(QtCore.QObject):
    """
    A list widget of Shotgun Pipeline steps per entity type.
    """

    step_filter_changed = QtCore.Signal(object)  # List of PTR step dictionaries

    def __init__(self, list_widget):
        """
        Instantiate a StepListWidget, collect all Pipeline steps from Shotgun if
        they are not already cached.

        :param list_widget: A :class:`QtGui.QListWidget` instance. It is assumed
                            it has a direct QWidget parent which can be shown or
                            hidden when showing steps for a given Entity type is
                            needed or not needed.
        """
        super().__init__()
        self._list_widget = list_widget
        StepCache.ensure_loaded()
        self._step_list = StepCache.get_step_map()
        self._step_widgets = defaultdict(list)
        saved_filters = load_step_filters()
        # Keep track of filters being changed to only save them if they were
        # changed.
        self._step_filters_changed = False
        if saved_filters is None:
            # Settings were never saved before. Select all exsiting steps by
            # default.
            self._current_filter_step_ids = set()
            for step_list in self._step_list.values():
                self._current_filter_step_ids.update([x["id"] for x in step_list])
        else:
            self._current_filter_step_ids = set([x["id"] for x in load_step_filters()])

    def select_all_steps(self, value=True):
        """
        Turn on or off all steps for filtering.

        Only active step widgets are affected, the updated selection is retrieved
        and emitted.

        :param bool value: Whether to turn on or off the steps.
        """
        for item_row in range(0, self._list_widget.count()):
            # Only toggle widgets currently active
            if not self._list_widget.isRowHidden(item_row):
                item = self._list_widget.item(item_row)
                # Retrieve the Step dictionary which was stored in user data.
                item_step = item.data(QtCore.Qt.UserRole)
                if value:
                    self._current_filter_step_ids.add(item_step["id"])
                else:
                    self._current_filter_step_ids.discard(item_step["id"])
                self._list_widget.itemWidget(item).setChecked(value)
        self._step_filters_changed = True
        self._retrieve_and_emit_selection()

    def unselect_all_steps(self):
        """
        Turn off all steps for filtering.
        """
        self.select_all_steps(False)

    def set_widgets_for_entity_type(self, entity_type):
        """
        Refresh the Step widgets being displayed for the given Entity type.

        If the Entity type is not supported or is None, the whole Step UI is hidden.

        :param str entity_type: A Shotgun Entity type or None.
        """
        if entity_type == "Task":
            # Show all steps
            for linked_entity_type in self._step_list:
                self._ensure_widgets_for_entity_type(linked_entity_type)
            for item_row in range(0, self._list_widget.count()):
                self._list_widget.setRowHidden(item_row, False)
            self._list_widget.parent().setVisible(True)
        elif entity_type is None or entity_type not in self._step_list:
            # Hide all steps by hiding the parent widget.
            self._list_widget.parent().setVisible(False)
        else:
            # Only show Steps for the given Entity type.
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
            self._list_widget.parent().setVisible(True)

    def save_step_filters_if_changed(self):
        """
        Save the current Step filters in user settings if they were changed.
        """
        if self._step_filters_changed:
            self.save_step_filters()

    def save_step_filters(self):
        """
        Save the current Step filters in user settings.
        """
        manager = settings_fw.UserSettings(sgtk.platform.current_bundle())
        current_selection = self._retrieve_selection()
        manager.store(_STEP_FILTERS_USER_SETTING, current_selection)

    def _retrieve_selection(self):
        """
        Retrieve the current Step filter selection.

        :returns: A potentially empty list of Shotgun Step entity dictionaries.
        """
        return [
            {"type": "Step", "id": step_id} for step_id in self._current_filter_step_ids
        ]

    def _retrieve_and_emit_selection(self):
        """
        Retrieve the whole selection and emit it.
        """
        self.step_filter_changed.emit(self._retrieve_selection())

    def _ensure_widgets_for_entity_type(self, entity_type):
        """
        Ensure widgets for Steps for the given Entity type are build.

        :param str entity_type: A Shotgun Entity type.
        """
        widgets = self._step_widgets[entity_type]
        if widgets:
            return widgets
        # Not already built, let's do it now
        for step in self._step_list[entity_type]:
            widget = QtGui.QCheckBox(step["code"])
            if step["color"]:
                pixmap = QtGui.QPixmap(100, 100)
                # Get the Step color and add a bit of transparency to the
                # color otherwise it is too bright.
                color = [int(x) for x in step["color"].split(",")] + [200]
                pixmap.fill(QtGui.QColor(*color))
                widget.setIcon(pixmap)
            # Turn it on if it was in the step saved filters
            # We do this before the toggled signal is connected to not emit
            # un-wanted signals.
            if step["id"] in self._current_filter_step_ids:
                widget.setChecked(True)
            widget.toggled.connect(
                lambda value, step_id=step["id"]: self._on_step_filter_toggled(
                    step_id, checked=value
                )
            )
            item = QtGui.QListWidgetItem("", self._list_widget)
            item.setData(QtCore.Qt.UserRole, step)
            self._list_widget.setItemWidget(item, widget)
            self._step_widgets[entity_type].append(widget)
        return self._step_widgets[entity_type]

    def _on_step_filter_toggled(self, step_id, checked=None):
        """
        Triggered when one of the Step item is toggled on/off.

        :param int step_id: The Step id which was changed.
        :param bool checked: Whether the Step is on or off.
        """
        self._step_filters_changed = True
        if checked:
            self._current_filter_step_ids.add(step_id)
        else:
            self._current_filter_step_ids.discard(step_id)
        self._retrieve_and_emit_selection()
