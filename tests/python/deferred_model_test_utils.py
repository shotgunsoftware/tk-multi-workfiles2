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
Helpers shared by the tests using a deferred entity model.
"""

import time


class BackgroundTaskManagerDrainMixin:
    """
    Mixin for test cases whose models load data with ``self.bg_task_manager``.

    Add it before :class:`Workfiles2TestBase` in the bases of the test case.
    """

    # Maximum time to wait for the results dispatcher to finish, in seconds.
    _DISPATCHER_TIMEOUT = 5

    def tearDown(self) -> None:
        """
        Shut down the background task manager before the base class releases it.

        The results dispatcher of the manager can be blocked waiting for the
        main thread to process an event, and the base class releases the
        manager without processing events, which makes Qt abort with
        "Destroyed while thread is still running". So shut the manager down
        and process events until the dispatcher has finished.
        """
        from sgtk.platform.qt import QtCore

        try:
            self.bg_task_manager.shut_down()
            dispatcher = self.bg_task_manager._results_dispatcher
            deadline = time.time() + self._DISPATCHER_TIMEOUT
            while dispatcher.isRunning():
                if time.time() >= deadline:
                    self.fail(
                        "The results dispatcher of the background task manager "
                        "did not finish within %d seconds." % self._DISPATCHER_TIMEOUT
                    )
                QtCore.QCoreApplication.processEvents()
                dispatcher.wait(10)
        finally:
            super().tearDown()
