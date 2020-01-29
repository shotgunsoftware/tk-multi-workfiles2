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
from contextlib import contextmanager

from mock import patch
from tank_test.tank_test_base import TankTestBase
from tank_test.tank_test_base import setUpModule  # noqa

import sgtk
from tank_test.tank_test_base import SealedMock

from workfiles2_test_base import Workfiles2TestBase


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

        self._bunny = self.mockgun.create(
            "Asset",
            {"code": "Bunny", "sg_asset_type": "Character", "project": self.project},
        )
        self._squirrel = self.mockgun.create(
            "Asset",
            {"code": "Squirrel", "sg_asset_type": "Character", "project": self.project},
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

        self._task_concept_ctx_jeff = self._create_context(self._task_concept)
        self._task_concept_ctx_francis = self._create_context(
            self._task_concept, self.francis
        )

        self._maya_asset_work = self.tk.templates["maya_asset_work"]
        self._maya_asset_publish = self.tk.templates["maya_asset_publish"]

    def _create_context(self, entity, user=None):
        context = self.tk.context_from_entity(entity["type"], entity["id"])
        if user:
            context = context.create_copy_for_user(user)

        # FIXME: This is really dirty. We're hacking into tk-core itself
        # to fool it into creating a folder for another user.
        with patch("tank.util.login.get_current_user", return_value=context.user):
            self.tk.create_filesystem_structure(
                entity["type"], entity["id"], engine="tk-testengine"
            )

        return context

    def _create_work_file(self, ctx, name, version):
        return self._create_template_file(ctx, self._maya_asset_work, name, version)

    def _create_publish_file(self, ctx, name, version):
        return self._create_template_file(ctx, self._maya_asset_publish, name, version)

    def _create_template_file(self, ctx, template, name, version):
        fields = ctx.as_template_fields(template)
        fields["name"] = name
        fields["version"] = version
        file_path = template.apply_fields(fields)
        # Touches the file
        with open(file_path, "wb") as fh:
            return file_path

    def test_noop(self):
        # Create scene files for each user
        self._create_work_file(self._task_concept_ctx_jeff, "scene", 1)
        self._create_work_file(self._task_concept_ctx_jeff, "scene", 2)
        self._create_work_file(self._task_concept_ctx_jeff, "scene", 3)
        self._create_work_file(self._task_concept_ctx_francis, "scene", 1)
        self._create_work_file(self._task_concept_ctx_francis, "scene", 2)
        self._create_work_file(self._task_concept_ctx_francis, "scene", 3)

        def jeff_files_are_found():
            if self._model.item(0) is not None:
                # print("not none", self._model.item(0).rowCount())
                return self._model.item(0).rowCount() == 3
            else:
                return False

        with self._wait_for_data_changes(jeff_files_are_found):
            self._model.set_entity_searches(
                [
                    self.FileModel.SearchDetails(
                        self._task_concept["content"], self._task_concept
                    )
                ]
            )

        import pdb

        pdb.set_trace()

    @contextmanager
    def _wait_for_data_changes(self, predicate):
        # This loop will execute until the _data_changed_cb is called nb_events times.
        loop = sgtk.platform.qt.QtCore.QEventLoop()

        self._timed_out = False

        def set_timeout_flag():
            self._timed_out = True

        # Give ourselves 2 seconds to wait for the data, then abort
        sgtk.platform.qt.QtCore.QTimer.singleShot(2000, set_timeout_flag)

        yield

        while predicate() is False and self._timed_out is False:
            loop.processEvents()

        assert predicate(), "Waiting for data timed out."


def tearDownModule():
    # FIXME: Ensures the event loop is properly flushed. The finalization
    # of the background task manager isn't really clean and threads
    # it owned finish eventually some time after the manager
    # itself was destroyed. These threads will emit events
    # as they are ending, which means there needs to be some
    # sort of message loop that consumes them so the threads
    # can then end properly.
    import time

    time_since_last_event = time.time()
    loop = sgtk.platform.qt.QtCore.QEventLoop()
    # If it's been more than one second since we got an event
    # we can quit.
    while time_since_last_event + 1 > time.time():
        if loop.processEvents():
            time_single_last_event = time.time()
