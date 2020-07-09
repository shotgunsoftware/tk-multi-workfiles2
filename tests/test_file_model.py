# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pprint
from contextlib import contextmanager

from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa

import pytest
import sgtk
import sys
import os

IS_PUBLISH = "publish"
IS_WORKFILE = "workfile"


class TestFileModelBase(Workfiles2TestBase):
    """
    Baseclass for all Workfiles2 unit tests.

    This sets up the fixtures, starts an engine and provides
    the following members:

    - self.engine: The test engine running
    - self.app: The test app running
    - self.tk_multi_workfiles: The tk_multi_workfiles module

    """

    def setUp(self, app_instance, work_template, publish_template):
        """
        Fixtures setup
        """
        super(TestFileModelBase, self).setUp(
            app_instance, work_template, publish_template
        )

        # This is specific to this test, everything above should be refactored
        # into a Workfiles2TestBase class.
        self.FileModel = self.tk_multi_workfiles.file_model.FileModel

        # Create the menu and set all available users, taken from the base class.
        self._model = self.FileModel(self.bg_task_manager, None)
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

        self._task_concept_2 = self.mockgun.create(
            "Task",
            {
                "content": "Bunny Concept 2",
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
                "step": self._rig,
                "entity": self._bunny,
            },
        )

        # Create a context with that task for both users.
        self._concept_ctx_jeff = self.create_context(self._task_concept)
        self._concept_2_ctx_jeff = self.create_context(self._task_concept_2)
        self._rig_ctx_jeff = self.create_context(self._task_rig)
        self._concept_ctx_francis = self.create_context(
            self._task_concept, self.francis
        )

    def _get_model_contents(self):
        """
        Dump a list of items found in the file model.

        The list contains a series of tuple containing
        ((HumanUser, id), (Task, id), file name, file version, workfile|publish)
        """
        contents = []
        for group_idx in range(self._model.rowCount()):
            group_item = self._model.item(group_idx)
            for file_idx in range(group_item.rowCount()):
                file_item = group_item.child(file_idx).file_item
                assert file_item.is_local or file_item.is_published
                if file_item.is_local:
                    contents.append(
                        group_item.key
                        + (file_item.name, file_item.version, IS_WORKFILE)
                    )
                if file_item.is_published:
                    contents.append(
                        group_item.key + (file_item.name, file_item.version, IS_PUBLISH)
                    )
        return contents

    def _assert_model_contains(self, expected):
        """
        Ensure the model contains the specified list of files.

        The list of files is expected to follow this structure
        (ctx, file name, version)
        """
        contents = self._get_model_contents()

        # Reformat the contents into something that is sortable.
        expected = [
            (
                ("Task", match[0].task["id"]),
                ("HumanUser", match[0].user["id"]),
                match[1],
                match[2],
                match[3],
            )
            for match in expected
        ]

        assert sorted(contents) == sorted(expected)

    @contextmanager
    def _wait_for_groups(self, nb_groups_expected):
        """
        Wait for the expected number of groups to show up.

        The method will timeout if it takes too long.
        """

        def search_is_over():
            """
            Ensures the expected number of groups was found
            and that each has completed.
            """
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

        def on_error_cb():
            return "Timed out. Model Content:\n" + pprint.pformat(
                self._get_model_contents()
            )

        with self.wait_for(search_is_over, on_error_cb):
            yield


class TestFileModelWithSandboxes(TestFileModelBase):
    """
    Test FileModel with user sandboxes.
    """

    def setUp(self):
        super(TestFileModelWithSandboxes, self).setUp(
            "tk-multi-workfiles2", "sandbox_path", "publish_path"
        )

    @pytest.mark.skipif(
        sys.version_info.major == 2 and sgtk.util.is_windows() and "CI" in os.environ,
        reason="This test is flaky on Windows, Python 2.7.",
    )
    def test_default_match_user_files(self):
        """
        Ensure the model will match only files from a user by default.
        """

        # Create scene files for each user
        self.create_work_file(self._concept_ctx_jeff, "scene", 1)
        self.create_work_file(self._concept_ctx_francis, "scene", 1)

        # Wait for the group to appear and be ready.
        with self._wait_for_groups(2):
            self._model.set_entity_searches(
                [
                    self.FileModel.SearchDetails("Concept files", self._task_concept),
                    self.FileModel.SearchDetails("Rig files", self._task_rig),
                ]
            )

        # Make sure we have only found a single file in the context.
        self._assert_model_contains([(self._concept_ctx_jeff, "scene", 1, IS_WORKFILE)])

        # Create a new file and refresh
        self.create_work_file(self._concept_ctx_jeff, "scene", 2)
        with self._wait_for_groups(2):
            self._model.async_refresh()

        # We should now see a second file.
        self._assert_model_contains(
            [
                (self._concept_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 2, IS_WORKFILE),
            ]
        )

    @pytest.mark.skipif(
        sys.version_info.major == 2 and sgtk.util.is_windows() and "CI" in os.environ,
        reason="This test is flaky on Windows, Python 2.7.",
    )
    def test_matches_specified_users(self):
        """
        Match files for a list of users.
        """
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
                (self._concept_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_ctx_francis, "scene", 1, IS_WORKFILE),
            ]
        )

    @pytest.mark.skipif(
        sys.version_info.major == 2 and sgtk.util.is_windows() and "CI" in os.environ,
        reason="This test is flaky on Windows, Python 2.7.",
    )
    def test_matches_publishes(self):
        """
        Match publishes as well as workfiles.
        """
        self.create_work_file(self._concept_ctx_jeff, "scene", 1)
        self.create_work_file(self._concept_ctx_jeff, "scene", 2)
        self.create_work_file(self._concept_ctx_jeff, "scene", 3)
        self.create_publish_file(self._concept_ctx_jeff, "scene", 1)
        self.create_publish_file(self._concept_ctx_jeff, "scene", 2)

        with self._wait_for_groups(1):
            self._model.set_entity_searches(
                [self.FileModel.SearchDetails("Concept files", self._task_concept)]
            )

        # Make sure we have only found a single file in the context.
        self._assert_model_contains(
            [
                (self._concept_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 1, IS_PUBLISH),
                (self._concept_ctx_jeff, "scene", 2, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 2, IS_PUBLISH),
                (self._concept_ctx_jeff, "scene", 3, IS_WORKFILE),
            ]
        )

    @pytest.mark.skipif(
        sys.version_info.major == 2 and sgtk.util.is_windows() and "CI" in os.environ,
        reason="This test is flaky on Windows, Python 2.7.",
    )
    def test_multi_task_match_same_workfiles_but_different_publishes(self):
        """
        Ensure a task context resolves the files for all tasks on a given
        step, but that publishes are resolved per-task
        """
        self.create_work_file(self._concept_ctx_jeff, "scene", 1)
        self.create_work_file(self._concept_ctx_jeff, "scene", 2)
        self.create_publish_file(self._concept_ctx_jeff, "scene", 1)
        self.create_publish_file(self._concept_2_ctx_jeff, "scene", 2)

        # Wait for the groups to appear and be ready.
        with self._wait_for_groups(2):
            self._model.set_entity_searches(
                [
                    self.FileModel.SearchDetails("Concept", self._task_concept),
                    self.FileModel.SearchDetails("Concept 2", self._task_concept_2),
                ]
            )

        self._assert_model_contains(
            [
                (self._concept_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 2, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 1, IS_PUBLISH),
                (self._concept_2_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_2_ctx_jeff, "scene", 2, IS_WORKFILE),
                (self._concept_2_ctx_jeff, "scene", 2, IS_PUBLISH),
            ]
        )


class TestFileModelWithTaskFolder(TestFileModelBase):
    """
    Test FileModel using task folders.
    """

    def setUp(self):
        super(self.__class__, self).setUp(
            "tk-multi-workfiles2-with-tasks", "task_path", "publish_path"
        )

    @pytest.mark.skipif(
        sys.version_info.major == 2 and sgtk.util.is_windows() and "CI" in os.environ,
        reason="This test is flaky on Windows, Python 2.7.",
    )
    def test_task_sandboxing_isolates_workfiles_from_same_step(self):
        """
        Ensure that using a task folder will associate a workfile with that
        task even if another task with the same step is used.
        """
        print(self.create_work_file(self._concept_ctx_jeff, "scene", 1))
        print(self.create_publish_file(self._concept_ctx_jeff, "scene", 1))

        print(self.create_work_file(self._concept_2_ctx_jeff, "scene", 2))
        print(self.create_publish_file(self._concept_2_ctx_jeff, "scene", 2))

        # Wait for the groups to appear and be ready.
        with self._wait_for_groups(2):
            self._model.set_entity_searches(
                [
                    self.FileModel.SearchDetails("Concept", self._task_concept),
                    self.FileModel.SearchDetails("Concept 2", self._task_concept_2),
                ]
            )

        self._assert_model_contains(
            [
                (self._concept_ctx_jeff, "scene", 1, IS_WORKFILE),
                (self._concept_ctx_jeff, "scene", 1, IS_PUBLISH),
                (self._concept_2_ctx_jeff, "scene", 2, IS_WORKFILE),
                (self._concept_2_ctx_jeff, "scene", 2, IS_PUBLISH),
            ]
        )
