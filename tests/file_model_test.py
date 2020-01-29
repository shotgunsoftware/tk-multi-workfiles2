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
        FileModel = self.tk_multi_workfiles.file_model.FileModel

        # Create the menu and set all available users, taken from the base class.
        self._model = FileModel(self._manager, None)
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

        self._task_concept_ctx = self._create_context(self._task_concept)
        self._task_concept_ctx = self._create_context(self._task_concept, self.francis)

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

    def test_noop(self):
        fields = self._task_concept_ctx.as_template_fields(self._maya_asset_work)
