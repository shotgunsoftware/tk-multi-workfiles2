# Copyright (c) 2020 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pytest
import subprocess
import time
import os
import sys

try:
    from MA.UI import topwindows
except ImportError:
    pytestmark = pytest.mark.skip()


# This fixture will launch tk-run-app on first usage
# and will remain valid until the test run ends.
@pytest.fixture(scope="module")
def host_application(tk_test_project, tk_test_entities, commands):
    """
    Launch the host application for the Toolkit application.

    TODO: This can probably be refactored, as it is not
     likely to change between apps, except for the context.
     One way to pass in a context would be to have the repo being
     tested to define a fixture named context and this fixture
     would consume it.
    """
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "tk_toolchain.cmd_line_tools.tk_run_app",
            # Allows the test for this application to be invoked from
            # another repository, namely the tk-framework-widget repo,
            # by specifying that the repo detection should start
            # at the specified location.
            "--location",
            os.path.dirname(__file__),
            "--context-entity-type",
            tk_test_project["type"],
            "--context-entity-id",
            str(tk_test_project["id"]),
            "--commands",
            commands,
            "--config",
            "tests/fixtures/configWF2ui",
        ]
    )
    try:
        yield
    finally:
        # We're done. Grab all the output from the process
        # and print it so that is there was an error
        # we'll know about it.
        stdout, stderr = process.communicate()
        sys.stdout.write(stdout or "")
        sys.stderr.write(stderr or "")
        process.poll()
        # If returncode is not set, then the process
        # was hung and we need to kill it
        if process.returncode is None:
            process.kill()
        else:
            assert process.returncode == 0


@pytest.fixture(scope="module")
def app_dialog(host_application, window_name):
    """
    Retrieve the application dialog and return the AppDialogAppWrapper.
    """
    # We're importing sgtk here inside this method as the conftest module will be initialised before sgtk can be found in sys.path.
    import sgtk

    before = time.time()
    while before + 30 > time.time():
        if sgtk.util.is_windows():
            app_dialog = AppDialogAppWrapper(topwindows[window_name].get())
        else:
            app_dialog = AppDialogAppWrapper(topwindows["python"][window_name].get())

        if app_dialog.exists():
            yield app_dialog
            app_dialog.close()
            return
    else:
        raise RuntimeError("Timeout waiting for the app dialog to launch.")


class AppDialogAppWrapper(object):
    """
    Wrapper around the app dialog.
    """

    def __init__(self, parent):
        """
        :param root:
        """
        self.root = parent

    def exists(self):
        """
        ``True`` if the widget was found, ``False`` otherwise.
        """
        return self.root.exists()

    def close(self):
        self.root.buttons["Close"].get().mouseClick()
