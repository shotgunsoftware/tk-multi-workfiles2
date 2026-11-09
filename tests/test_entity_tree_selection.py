# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Unit tests for the selection of an Entity shown in several places of a tree.
"""

from typing import TYPE_CHECKING, List, Optional
from unittest.mock import Mock

from deferred_model_test_utils import BackgroundTaskManagerDrainMixin
from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa

if TYPE_CHECKING:
    from sgtk.platform.qt import QtGui


class TestEntityTreeSelection(BackgroundTaskManagerDrainMixin, Workfiles2TestBase):
    """
    Test which item is selected for an Entity which is shown several times.
    """

    def setUp(self) -> None:
        super().setUp()

        from sgtk.platform.qt import QtCore, QtGui

        self.QtCore = QtCore
        self.QtGui = QtGui
        self.entity_tree_form = self.tk_multi_workfiles.entity_tree.entity_tree_form
        self.first_visible_item = self.entity_tree_form.first_visible_item
        self.create_regex = self.tk_multi_workfiles.util.create_case_insensitive_regex

        self.shots = [
            self.mockgun.create("Shot", {"code": code, "project": self.project})
            for code in ("A", "B")
        ]
        step = self.mockgun.create("Step", {"code": "Anim"})
        self.task = {
            "type": "Task",
            "id": 1,
            "content": "task1",
            "step": {"type": "Step", "id": step["id"], "name": "Anim"},
        }

        # The base class destroys the model in tearDown.
        self._model = self.tk_multi_workfiles.entity_models.deferred_model.ShotgunDeferredEntityModel(
            "Shot",
            [["project", "is", self.project]],
            ["code"],
            [],
            deferred_query={
                "entity_type": "Task",
                "link_field": "entity.Asset.shots",
                "filters": [],
                "hierarchy": ["step"],
            },
            parent=None,
            bg_task_manager=self.bg_task_manager,
        )
        self._model.load_and_refresh()
        with self.wait_for(
            lambda: all(
                self._model.item_from_entity("Shot", shot["id"]) for shot in self.shots
            ),
            lambda: "The Shots were not loaded.",
        ):
            pass
        # Show the same Task under both Shots.
        for shot in self.shots:
            self._model._add_deferred_item_hierarchy(
                self._model.item_from_entity("Shot", shot["id"]),
                ["step"],
                "content",
                self.task,
            )

        self.proxy = self.tk_multi_workfiles.entity_tree.entity_tree_proxy_model.EntityTreeProxyModel(
            None, []
        )
        self.proxy.setSourceModel(self._model)

    def tearDown(self) -> None:
        self.proxy.setSourceModel(None)
        super().tearDown()

    @staticmethod
    def _path_of(item: Optional["QtGui.QStandardItem"]) -> List[str]:
        """
        Return the text of the items from the root of the model down to the item.
        """
        path = []
        while item is not None:
            path.append(item.text())
            item = item.parent()
        return list(reversed(path))

    def _task_items(self) -> List["QtGui.QStandardItem"]:
        return self._model.items_from_entity("Task", self.task["id"])

    def test_selects_first_visible_location(self) -> None:
        """
        A location hidden by the search is ignored.
        """
        # Only show the branch of the Shot "B".
        self.proxy.setFilterRegExp(self.create_regex("B"))
        item = self.first_visible_item(self.proxy, self._task_items())
        self.assertEqual(self._path_of(item), ["B", "Anim", "task1"])

    def test_selects_first_location_when_all_are_visible(self) -> None:
        item = self.first_visible_item(self.proxy, self._task_items())
        self.assertEqual(self._path_of(item), ["A", "Anim", "task1"])

    def test_follows_proxy_sort_order(self) -> None:
        """
        The first location is the first one shown, not the first one in the model.
        """
        self.proxy.sort(0, self.QtCore.Qt.DescendingOrder)
        item = self.first_visible_item(self.proxy, self._task_items())
        self.assertEqual(self._path_of(item), ["B", "Anim", "task1"])

    def test_returns_none_when_nothing_is_visible(self) -> None:
        self.proxy.setFilterRegExp(self.create_regex("not in the tree"))
        self.assertIsNone(self.first_visible_item(self.proxy, self._task_items()))

    def test_returns_none_without_items(self) -> None:
        self.assertIsNone(self.first_visible_item(self.proxy, []))
        self.assertIsNone(self.first_visible_item(self._model, []))

    def test_returns_first_item_without_proxy_model(self) -> None:
        items = self._task_items()
        self.assertIs(self.first_visible_item(self._model, items), items[0])

    def _update_selection(
        self, view_model: "QtGui.QAbstractItemModel", entity: dict
    ) -> Mock:
        """
        Run EntityTreeForm._update_selection on a stand-in form and return the
        mock of the tree view showing the given model.
        """
        form = Mock()
        form._entity_to_select = entity
        form._current_item_ref = None
        form._ui.entity_tree.model.return_value = view_model
        form._get_selected_item.return_value = None
        self.entity_tree_form.EntityTreeForm._update_selection(form, None)
        return form._ui.entity_tree

    def test_update_selection_selects_visible_location(self) -> None:
        """
        The selection goes to the visible location of the Entity.
        """
        self.proxy.setFilterRegExp(self.create_regex("B"))
        tree = self._update_selection(self.proxy, self.task)
        index = tree.selectionModel().setCurrentIndex.call_args[0][0]
        item = self._model.itemFromIndex(self.proxy.mapToSource(index))
        self.assertEqual(self._path_of(item), ["B", "Anim", "task1"])

    def test_update_selection_selects_nothing_when_hidden(self) -> None:
        self.proxy.setFilterRegExp(self.create_regex("not in the tree"))
        tree = self._update_selection(self.proxy, self.task)
        tree.selectionModel().setCurrentIndex.assert_not_called()

    def test_falls_back_to_item_from_entity(self) -> None:
        """
        Models without items_from_entity are queried as before.
        """

        class LegacyModel(self.QtGui.QStandardItemModel):
            def __init__(self, item: "QtGui.QStandardItem") -> None:
                super().__init__()
                self.invisibleRootItem().appendRow(item)
                self.item = item
                self.requests = []

            def item_from_entity(
                self, entity_type: str, entity_id: int
            ) -> "QtGui.QStandardItem":
                self.requests.append((entity_type, entity_id))
                return self.item

        legacy_model = LegacyModel(self.QtGui.QStandardItem("task1"))
        self.assertFalse(hasattr(legacy_model, "items_from_entity"))
        tree = self._update_selection(legacy_model, self.task)
        self.assertEqual(legacy_model.requests, [("Task", self.task["id"])])
        index = tree.selectionModel().setCurrentIndex.call_args[0][0]
        self.assertEqual(index, legacy_model.item.index())
