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


class Workfiles2TestBase(TankTestBase):
    """
    Baseclass for all Workfiles2 unit tests.

    This sets up the fixtures, starts an engine and provides
    the following members:

    - self.engine: The test engine running
    - self.app: The test app running
    - self.tk_multi_workfiles: The tk_multi_workfiles module
    - self.jeff, self.rob and self.francis, three human user entities.

    Jeff is set as the current user.
    """

    _qapp = None

    def setUp(self):
        """
        Fixtures setup
        """
        # Make sure the project folder on disk has a unique name between each test.
        super(Workfiles2TestBase, self).setUp(
            {"project_tank_name": self.short_test_name}
        )
        sgtk.set_authenticated_user(SealedMock(login="jeff"))

        self.jeff = self.mockgun.create("HumanUser", {"name": "Jeff", "login": "jeff"})
        self.francis = self.mockgun.create(
            "HumanUser", {"name": "Francis", "login": "francis"}
        )
        self.rob = self.mockgun.create("HumanUser", {"name": "Rob", "login": "rob"})

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

        self.app = self.engine.apps["tk-multi-workfiles2"]
        self.tk_multi_workfiles = self.app.import_module("tk_multi_workfiles")

        self.bg_task_manager = (
            self.app.frameworks["tk-framework-shotgunutils"]
            .import_module("task_manager")
            .BackgroundTaskManager(parent=None, start_processing=True)
        )
        self.addCleanup(self.bg_task_manager.shut_down)

        self.maya_asset_work = self.tk.templates["maya_asset_work"]
        self.maya_asset_publish = self.tk.templates["maya_asset_publish"]

    def create_context(self, entity, user=None):
        """
        Create a context for the given entity and user.

        This method will also create the sandbox for that user.
        """
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

    @contextmanager
    def wait_for(self, predicate, assert_msg_cb, timeout=2000):
        """
        Wait for a given predicate to turn True.

        In between calls to predicates, the Qt message loop will be processed.

        :param callable predicate: Predicate to evaluate.
        :param int timeout: Timeout
        """
        # This loop will execute until the _data_changed_cb is called nb_events times.
        loop = sgtk.platform.qt.QtCore.QEventLoop()

        self._timed_out = False

        def set_timeout_flag():
            self._timed_out = True

        # Give ourselves 2 seconds to wait for the data, then abort
        sgtk.platform.qt.QtCore.QTimer.singleShot(timeout, set_timeout_flag)

        yield

        while predicate() is False and self._timed_out is False:
            loop.processEvents()

        assert predicate(), assert_msg_cb()

    def create_work_file(self, ctx, name, version):
        """
        Create a workfile for the given context, name and version.

        :returns: The path to the file.
        """
        return self._create_template_file(ctx, self.maya_asset_work, name, version)

    def create_publish_file(self, ctx, name, version):
        """
        Create a publish file for the given context, name and version.

        :returns: The path to the file.
        """
        path = self._create_template_file(ctx, self.maya_asset_publish, name, version)
        sgtk.util.register_publish(
            self.tk,
            ctx,
            path,
            name,
            version,
            thumbnail_path=os.path.expandvars(
                "$SHOTGUN_CURRENT_REPO_ROOT/icon_256.png"
            ),
        )
        return path

    def _create_template_file(self, ctx, template, name, version):
        """
        Create a file for the given context, template, name and version.

        :returns: The path to the file.
        """
        fields = ctx.as_template_fields(template)
        fields["name"] = name
        fields["version"] = version
        file_path = template.apply_fields(fields)
        # Touches the file
        with open(file_path, "wb") as fh:
            return file_path


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
