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

from unittest.mock import patch

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

    def setUp(
        self,
        app_instance="tk-multi-workfiles2",
        work_template="sandbox_path",
        publish_template="publish_path",
    ):
        """
        Fixtures setup
        """
        # Make sure the project folder on disk has a unique name between each test.
        super().setUp({"project_tank_name": self.short_test_name})
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

        self.app = self.engine.apps[app_instance]
        self.tk_multi_workfiles = self.app.import_module("tk_multi_workfiles")

        self.bg_task_manager = (
            self.app.frameworks["tk-framework-shotgunutils"]
            .import_module("task_manager")
            .BackgroundTaskManager(parent=None, start_processing=True)
        )
        self.work_template = self.tk.templates[work_template]
        self.publish_template = self.tk.templates[publish_template]

    def tearDown(self):
        """
        Cleanup - manually shut down and destroy objects before super().tearDown().

        This prevents segmentation faults on macOS with Python 3.13+ where
        the GIL changes and PySide6 6.8.3+ stricter signal auto-disconnection
        can access freed memory during object destruction.

        Following tk-framework-shotgunutils pattern: manually handle all
        cleanup in tearDown (NOT via addCleanup) to ensure proper order.
        """
        # Import Qt early so we can use it throughout
        from tank.platform.qt import QtCore
        import time

        # Shut down background task manager first and wait for ALL threads
        if hasattr(self, "bg_task_manager") and self.bg_task_manager is not None:
            # Call shut_down which signals threads to stop
            self.bg_task_manager.shut_down()

            # CRITICAL: Wait for the results dispatcher thread to actually finish
            # The dispatcher's shut_down() doesn't wait (to avoid deadlock in normal use)
            # but in tearDown we MUST wait or it will try to log during engine destruction
            results_dispatcher = getattr(
                self.bg_task_manager, "_results_dispatcher", None
            )
            if results_dispatcher and results_dispatcher.isRunning():
                results_dispatcher.wait(2000)  # Wait up to 2 seconds

            # Explicitly delete the task manager to break any references
            del self.bg_task_manager
            self.bg_task_manager = None

        # CRITICAL: Destroy any test-created models/widgets BEFORE destroying engine
        # This prevents segfaults on Python 3.13 with PySide6
        if hasattr(self, "_model") and self._model is not None:
            self._model.destroy()
            del self._model
            self._model = None

        # Wait for metrics dispatcher threads to finish before engine.destroy()
        if hasattr(self, "engine") and self.engine is not None:
            metrics_dispatcher = getattr(self.engine, "_metrics_dispatcher", None)
            if metrics_dispatcher and metrics_dispatcher.dispatching:
                # Stop metrics dispatcher
                metrics_dispatcher.stop()
                # Wait for worker threads to actually complete
                for worker in metrics_dispatcher.workers:
                    if worker.is_alive():
                        worker.join(timeout=2.0)

            # Destroy the engine
            self.engine.destroy()

        # CRITICAL: Aggressive Qt cleanup before pytest fixture teardown
        qapp = QtCore.QCoreApplication.instance()
        if qapp is not None:
            # Process all events multiple times
            for _ in range(10):
                QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.sendPostedEvents()

            # Explicitly process deferred delete events
            QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
            QtCore.QCoreApplication.processEvents()

            # Give threads a tiny moment to fully exit
            time.sleep(0.01)

            # Final event processing
            QtCore.QCoreApplication.processEvents()
            QtCore.QCoreApplication.sendPostedEvents()

        # Clear engine reference after all Qt processing
        if hasattr(self, "engine"):
            del self.engine
            self.engine = None

        super().tearDown()

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
    def wait_for(self, predicate, assert_msg_cb, timeout=5000):
        """
        Wait for a given predicate to turn True.

        In between calls to predicates, the Qt message loop will be processed.

        :param callable predicate: Predicate to evaluate.
        :param callable assert_msg_cb: On error, this callable will be invoked
            to generate an error message.
        :param int timeout: Timeout in milliseconds (default 5000ms) in milliseconds (default 5000ms)
        """
        loop = sgtk.platform.qt.QtCore.QEventLoop()

        # This will be used to indicate that we should stop looping because it
        # took too long for the predicate to turn true.
        self._timed_out = False

        def set_timeout_flag():
            self._timed_out = True

        yield

        # Launch the timer that will time us out.
        sgtk.platform.qt.QtCore.QTimer.singleShot(timeout, set_timeout_flag)

        # As soon as the predicate turns true, we can stop processing events.
        while predicate() is False and self._timed_out is False:
            loop.processEvents()

        # Print out an error message if the predicate is False.
        assert predicate(), assert_msg_cb()

    def create_work_file(self, ctx, name, version):
        """
        Create a workfile for the given context, name and version.

        :returns: The path to the file.
        """
        return self._create_template_file(ctx, self.work_template, name, version)

    def create_publish_file(self, ctx, name, version):
        """
        Create a publish file for the given context, name and version.

        :returns: The path to the file.
        """
        path = self._create_template_file(ctx, self.publish_template, name, version)
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
