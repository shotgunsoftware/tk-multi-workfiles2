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
Unit tests for the ShotgunDeferredEntityModel class.
"""

from typing import TYPE_CHECKING, List, Optional

from deferred_model_test_utils import BackgroundTaskManagerDrainMixin
from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa

if TYPE_CHECKING:
    from sgtk.platform.qt import QtGui


class FakeDeferredItem:
    """
    Stand in for an item of a deferred ShotgunEntityModel.
    """

    def __init__(self, sg_data: dict) -> None:
        self._sg_data = sg_data

    def get_sg_data(self) -> dict:
        """
        Return the Shotgun data of the item.
        """
        return self._sg_data


class FakeDeferredModel:
    """
    Stand in for the ShotgunEntityModel holding the results of a deferred query.
    """

    def __init__(self, sg_entities: List[dict]) -> None:
        self._sg_entities = {x["id"]: x for x in sg_entities}

    @property
    def entity_ids(self) -> List[int]:
        """
        Return the ids of the entities held by the model.
        """
        return list(self._sg_entities.keys())

    def get_entity_type(self) -> str:
        """
        Return the type of the entities held by the model.
        """
        return "Task"

    def clear(self) -> None:
        """
        Do nothing, there is no data to clear.
        """

    def destroy(self) -> None:
        """
        Do nothing, there is nothing to release.
        """

    def item_from_entity(self, entity_type: str, entity_id: int) -> FakeDeferredItem:
        """
        Return an item holding the data of the entity with the given id.
        """
        return FakeDeferredItem(self._sg_entities[entity_id])


class TestDeferredModel(BackgroundTaskManagerDrainMixin, Workfiles2TestBase):
    """
    Test the uids and the entity index of the ShotgunDeferredEntityModel.
    """

    def setUp(self) -> None:
        super().setUp()

        self.shot_a = self.mockgun.create(
            "Shot", {"code": "A", "project": self.project}
        )
        self.shot_b = self.mockgun.create(
            "Shot", {"code": "B", "project": self.project}
        )
        self.step_anim = self.mockgun.create("Step", {"code": "Anim"})
        self.step_light = self.mockgun.create("Step", {"code": "Light"})
        self.asset_1 = {"type": "Asset", "id": 1, "name": "Asset1"}

        self.task_1 = self._task(1, "task1", self.step_anim, "ip")
        self.task_2 = self._task(2, "task2", self.step_anim, "ip")
        self.task_3 = self._task(3, "task3", self.step_light, "ip")

        self._create_model()

    def _task(
        self,
        task_id: int,
        content: str,
        step: dict,
        status: str,
        entity: Optional[dict] = None,
    ) -> dict:
        """
        Build a Task dictionary as it would be returned by a deferred query.
        """
        return {
            "type": "Task",
            "id": task_id,
            "content": content,
            "step": {"type": "Step", "id": step["id"], "name": step["code"]},
            "sg_status_list": status,
            "entity": entity,
        }

    def _create_model(self, hierarchy: Optional[list] = None) -> None:
        """
        Create a model loading the Shots of the project, with deferred Tasks.
        """
        model = self.tk_multi_workfiles.entity_models.deferred_model.ShotgunDeferredEntityModel(
            "Shot",
            [["project", "is", self.project]],
            ["code"],
            [],
            deferred_query={
                "entity_type": "Task",
                "link_field": "entity.Asset.shots",
                "filters": [],
                "hierarchy": hierarchy or ["step"],
            },
            parent=None,
            bg_task_manager=self.bg_task_manager,
        )
        # The base class destroys the model in tearDown.
        self._model = model
        model.load_and_refresh()
        with self.wait_for(
            lambda: all(
                model.item_from_entity("Shot", shot["id"])
                for shot in (self.shot_a, self.shot_b)
            ),
            lambda: "The Shots were not loaded.",
        ):
            pass

    def _leaf(self, shot: dict) -> "QtGui.QStandardItem":
        return self._model.item_from_entity("Shot", shot["id"])

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

    def _all_task_paths(self) -> list:
        """
        Return the sorted paths of all the Task nodes in the model.
        """
        paths = []
        for shot in (self.shot_a, self.shot_b):
            stack = [self._leaf(shot)]
            while stack:
                item = stack.pop()
                sg_data = item.get_sg_data()
                if item.parent() is not None and sg_data and sg_data["type"] == "Task":
                    if not item.rowCount():
                        paths.append(self._path_of(item))
                for row in range(item.rowCount()):
                    stack.append(item.child(row))
        return sorted(paths)

    def test_task_appears_under_every_parent(self) -> None:
        """
        The same Task is shown under each Shot it is linked to.
        """
        for shot in (self.shot_a, self.shot_b):
            self._model._add_deferred_item_hierarchy(
                self._leaf(shot), ["step"], "content", self.task_1
            )
        items = self._model.items_from_entity("Task", self.task_1["id"])
        self.assertEqual(
            [self._path_of(item) for item in items],
            [["A", "Anim", "task1"], ["B", "Anim", "task1"]],
        )
        self.assertIs(self._model.item_from_entity("Task", self.task_1["id"]), items[0])

    def test_shot_asset_task_tree(self) -> None:
        """
        A Shot / Asset / Step / Task tree is built under each Shot.
        """
        task = self._task(4, "task4", self.step_anim, "ip", entity=self.asset_1)
        for shot in (self.shot_a, self.shot_b):
            self._model._add_deferred_item_hierarchy(
                self._leaf(shot), ["entity", "step"], "content", task
            )
        items = self._model.items_from_entity("Task", task["id"])
        self.assertEqual(
            [self._path_of(item) for item in items],
            [
                ["A", "Asset1", "Anim", "task4"],
                ["B", "Asset1", "Anim", "task4"],
            ],
        )

    def test_multi_field_hierarchy_splits_by_each_level(self) -> None:
        """
        Nodes of the same name under different parents are not merged.
        """
        task_light = self._task(5, "task5", self.step_light, "ip")
        for task in (self.task_1, task_light):
            self._model._add_deferred_item_hierarchy(
                self._leaf(self.shot_a), ["step", "sg_status_list"], "content", task
            )
        self.assertEqual(
            self._all_task_paths(),
            [["A", "Anim", "ip", "task1"], ["A", "Light", "ip", "task5"]],
        )

    def test_one_to_many_tree_is_unchanged(self) -> None:
        """
        Tasks linked to a single parent are shown once, as before.
        """
        for task in (self.task_1, self.task_2):
            self._model._add_deferred_item_hierarchy(
                self._leaf(self.shot_a), ["step"], "content", task
            )
        self.assertEqual(
            self._all_task_paths(),
            [["A", "Anim", "task1"], ["A", "Anim", "task2"]],
        )
        items = self._model.items_from_entity("Task", self.task_1["id"])
        self.assertEqual(len(items), 1)
        self.assertIs(self._model.item_from_entity("Task", self.task_1["id"]), items[0])

    def test_all_nodes_are_cached_under_the_parent(self) -> None:
        """
        The deferred cache keeps every node directly under the parent uid.
        """
        parent_uid = self._leaf(self.shot_a).data(self._model._SG_ITEM_UNIQUE_ID)
        uids = self._model._add_deferred_item_hierarchy(
            self._leaf(self.shot_a), ["step", "sg_status_list"], "content", self.task_1
        )
        self.assertEqual(
            sorted(uids),
            sorted(
                [
                    "%s/Step_%d" % (parent_uid, self.step_anim["id"]),
                    "%s/Step_%d/ip" % (parent_uid, self.step_anim["id"]),
                    "%s/Step_%d/ip/Task_1" % (parent_uid, self.step_anim["id"]),
                ]
            ),
        )
        self.assertEqual(
            sorted(self._model._deferred_cache.get_child_uids(parent_uid)),
            sorted(uids),
        )

    def test_item_from_entity_returns_none_when_not_loaded(self) -> None:
        """
        Nothing is returned for a deferred Entity which is not in the model.
        """
        self.assertIsNone(self._model.item_from_entity("Task", 999))
        self.assertEqual(self._model.items_from_entity("Task", 999), [])

    def test_items_from_entity_for_primary_entity_type(self) -> None:
        """
        Primary entities are still found, with the base class implementation.
        """
        items = self._model.items_from_entity("Shot", self.shot_a["id"])
        self.assertEqual([self._path_of(item) for item in items], [["A"]])
        self.assertEqual(self._model.items_from_entity("Shot", 999), [])

    def test_refresh_moves_task_when_step_changes(self) -> None:
        """
        The node of a Task is moved when the Step of the Task changes.
        """
        parent = self._leaf(self.shot_a)
        task = self._task(1, "task1", self.step_anim, "ip")
        self._model._deferred_models[self.shot_a["id"]] = FakeDeferredModel([task])
        self._model._on_deferred_data_refreshed(self.shot_a, True)
        self.assertEqual(
            [
                self._path_of(item)
                for item in self._model.items_from_entity("Task", task["id"])
            ],
            [["A", "Anim", "task1"]],
        )
        old_uids = list(self._model._deferred_uids_by_entity[("Task", task["id"])])

        task = self._task(1, "task1", self.step_light, "ip")
        self._model._deferred_models[self.shot_a["id"]] = FakeDeferredModel([task])
        self._model._on_deferred_data_refreshed(self.shot_a, True)

        self.assertEqual(
            [
                self._path_of(item)
                for item in self._model.items_from_entity("Task", task["id"])
            ],
            [["A", "Light", "task1"]],
        )
        new_uids = self._model._deferred_uids_by_entity[("Task", task["id"])]
        self.assertEqual(len(new_uids), 1)
        self.assertNotIn(new_uids[0], old_uids)
        self.assertIsNotNone(self._model._get_item_by_unique_id(new_uids[0]))
        # The old Step node is gone.
        self.assertEqual(parent.rowCount(), 1)
        self.assertEqual(parent.child(0).text(), "Light")

    def test_clear_empties_entity_index(self) -> None:
        """
        Clearing the model forgets about the deferred entities.
        """
        self._model._add_deferred_item_hierarchy(
            self._leaf(self.shot_a), ["step"], "content", self.task_1
        )
        self._model.clear()
        self.assertEqual(self._model._deferred_uids_by_entity, {})
        self.assertIsNone(self._model.item_from_entity("Task", self.task_1["id"]))

    def test_refresh_of_one_parent_keeps_other_locations(self) -> None:
        """
        Refreshing a parent only drops the Tasks of that parent.
        """
        for shot in (self.shot_a, self.shot_b):
            self._model._deferred_models[shot["id"]] = FakeDeferredModel([self.task_1])
            self._model._on_deferred_data_refreshed(shot, True)
        self._model._deferred_models[self.shot_a["id"]] = FakeDeferredModel([])
        self._model._on_deferred_data_refreshed(self.shot_a, True)
        items = self._model.items_from_entity("Task", self.task_1["id"])
        self.assertEqual([self._path_of(i) for i in items], [["B", "Anim", "task1"]])
        self.assertEqual(len(self._model._deferred_uids_by_entity[("Task", 1)]), 1)
        self.assertEqual(self._leaf(self.shot_a).child(0).text(), "No Tasks found")
