# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import pprint
from contextlib import contextmanager

from tank_test.tank_test_base import TankTestBase
from tank_test.tank_test_base import setUpModule  # noqa

import sgtk
from tank_test.tank_test_base import SealedMock

from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa


class TestFileModel(Workfiles2TestBase):
    """
    Baseclass for all Workfiles2 unit tests.

    This sets up the fixtures, starts an engine and provides
    the following members:

    - self.engine: The test engine running
    - self.app: The test app running
    - self.tk_multi_workfiles: The tk_multi_workfiles module

    """

    def setUp(self):
        """
        Fixtures setup
        """
        super(TestFileModel, self).setUp()

        self._manager = (
            self.app.frameworks["tk-framework-shotgunutils"]
            .import_module("task_manager")
            .BackgroundTaskManager(parent=None, start_processing=True)
        )
        self.addCleanup(self._manager.shut_down)

        # This is specific to this test, everything above should be refactored
        # into a Workfiles2TestBase class.
        self.FileModel = self.tk_multi_workfiles.file_model.FileModel

        # Create the menu and set all available users, taken from the base class.
        self._model = self.FileModel(self._manager, None)
        self.addCleanup(self._model.destroy)

        # Create an asset with a concept task.
        self._bunny = self.mockgun.create(
            "Asset",
            {"code": "Bunny", "sg_asset_type": "Character", "project": self.project},
        )
        self._concept = self.mockgun.create(
            "Step", {"code": "Concept", "short_name": "concept"}
        )
        self._rig = self.mockgun.create("Step", {"code": "Rig", "short_name": "rig"})
        self._task_concept = self.mockgun.create(
            "Task",
            {
                "content": "Bunny Concept",
                "project": self.project,
                "step": self._concept,
                "entity": self._bunny,
            },
        )

        self._task_concept = self.mockgun.create(
            "Task",
            {
                "content": "Bunny Concept",
                "project": self.project,
                "step": self._concept,
                "entity": self._bunny,
            },
        )
        self._task_rig = self.mockgun.create(
            "Task",
            {
                "content": "Bunny Concept",
                "project": self.project,
                "step": self._concept,
                "entity": self._bunny,
            },
        )

        # Create a context with that task for both users.
        self._concept_ctx_jeff = self.create_context(self._task_concept)
        self._rig_ctx_jeff = self.create_context(self._task_rig)
        self._concept_ctx_francis = self.create_context(
            self._task_concept, self.francis
        )

    def test_default_match_user_files(self):
        """
        Ensure the model will match only files from a user by default.
        """
        # Create scene files for each user
        self.create_work_file(self._concept_ctx_jeff, "scene", 1)
        self.create_work_file(self._concept_ctx_francis, "scene", 1)

        # Wait for the group to appear and be ready.
        with self._wait_for_groups(1):
            self._model.set_entity_searches(
                [self.FileModel.SearchDetails("Concept files", self._task_concept)]
            )

        # Make sure we have only found a single file in the context.
        self._assert_model_contains([(self._concept_ctx_jeff, "scene", 1)])

        # Create a new file and refresh
        self.create_work_file(self._concept_ctx_jeff, "scene", 2)
        with self._wait_for_groups(1):
            self._model.async_refresh()

        # We should now see a second file.
        self._assert_model_contains(
            [(self._concept_ctx_jeff, "scene", 1), (self._concept_ctx_jeff, "scene", 2)]
        )

    def test_matches_specified_users(self):

        self.create_work_file(self._concept_ctx_jeff, "scene", 1)
        self.create_work_file(self._concept_ctx_francis, "scene", 1)

        with self._wait_for_groups(2):
            # The model always searches for the current user, so wait for
            # two groups even if the user menu requested one.
            self._model.set_users([self.francis])
            self._model.set_entity_searches(
                [self.FileModel.SearchDetails("Concept files", self._task_concept)]
            )

        self._assert_model_contains(
            [
                (self._concept_ctx_jeff, "scene", 1),
                (self._concept_ctx_francis, "scene", 1),
            ]
        )

    def _get_model_contents(self):
        contents = []
        for group_idx in range(self._model.rowCount()):
            group_item = self._model.item(group_idx)
            for file_idx in range(group_item.rowCount()):
                file_item = group_item.child(file_idx)
                contents.append(
                    group_item.key
                    + (file_item.file_item.name, file_item.file_item.version)
                )
        return contents

    def _assert_model_contains(self, expected):
        contents = self._get_model_contents()

        expected = [
            (
                ("Task", match[0].task["id"]),
                ("HumanUser", match[0].user["id"]),
                match[1],
                match[2],
            )
            for match in expected
        ]

        assert sorted(contents) == sorted(expected)

    @contextmanager
    def _wait_for_groups(self, nb_groups_expected):
        def search_is_over():
            if self._model.rowCount() == nb_groups_expected:
                for i in range(nb_groups_expected):
                    if (
                        self._model.item(i).data(self.FileModel.SEARCH_STATUS_ROLE)
                        != self.FileModel.SEARCH_COMPLETED
                    ):
                        return False
                return True
            else:
                return False

        with self.wait_for(search_is_over, self._get_model_contents):
            yield

    def _get_dbg_str(self):
        "Timed out. Model Content:\n" + pprint.pformat(self._get_model_contents())
