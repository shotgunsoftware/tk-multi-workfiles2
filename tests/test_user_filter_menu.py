# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

from tank_test.tank_test_base import TankTestBase
from tank_test.tank_test_base import setUpModule  # noqa

import sgtk


class TestUserFilterMenu(TankTestBase):
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
        super(TestUserFilterMenu, self).setUp()
        self.setup_fixtures()

        # Add these to mocked shotgun
        self.add_to_sg_mock_db([self.project])

        # run folder creation for the project
        self.tk.create_filesystem_structure(self.project["type"], self.project["id"])

        # now make a context
        context = self.tk.context_from_entity(self.project["type"], self.project["id"])

        # and start the engine
        self.engine = sgtk.platform.start_engine("tk-testengine", self.tk, context)
        # This ensures that the engine will always be destroyed.
        self.addCleanup(self.engine.destroy)

        # Ensure a QApplication instance for the tests.
        self._qapp = sgtk.platform.qt.QtGui.QApplication.instance()
        if not self._qapp:
            self._qapp = sgtk.platform.qt.QtGui.QApplication([])

        self.app = self.engine.apps["tk-multi-workfiles2"]
        self.tk_multi_workfiles = self.app.import_module("tk_multi_workfiles")

    def test_noop(self):
        pass
