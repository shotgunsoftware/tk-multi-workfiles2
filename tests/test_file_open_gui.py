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
import sgtk

try:
    from MA.UI import topwindows
except ImportError:
    pytestmark = pytest.mark.skip()


# This fixture will launch tk-run-app on first usage
# and will remain valid until the test run ends.
@pytest.fixture(scope="module")
def host_application(sg_project, sg_entities):
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
            sg_project["type"],
            "--context-entity-id",
            str(sg_project["id"]),
            "--commands",
            "file_open",
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
def app_dialog(host_application):
    """
    Retrieve the application dialog and return the AppDialogAppWrapper.
    """
    before = time.time()
    while before + 30 > time.time():
        if sgtk.util.is_windows():
            app_dialog = AppDialogAppWrapper(topwindows)
        else:
            app_dialog = AppDialogAppWrapper(topwindows["python"])

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
        self.root = parent["Shotgun: File Open"].get()

    def exists(self):
        """
        ``True`` if the widget was found, ``False`` otherwise.
        """
        return self.root.exists()

    def close(self):
        self.root.buttons["Close"].get().mouseClick()


def test_ui_validation(app_dialog, sg_project):
    """
    Basic UI validation to make sure all buttons, tabs and fields are available
    """
    # Make Sure the File Open dialog is showing up in the right context
    assert app_dialog.root.captions["File Open"].exists(), "Not the File Open dialog"
    assert app_dialog.root.captions[
        "*Project " + sg_project["name"]
    ].exists(), "Not the right context"

    # Make sure the breadcrumb UI is fine.
    assert app_dialog.root.buttons[
        "nav_home_btn"
    ].exists(), "Nav home button is missing"
    assert app_dialog.root.buttons[
        "nav_prev_btn"
    ].exists(), "Nav previous button is missing"
    assert app_dialog.root.buttons[
        "nav_next_btn"
    ].exists(), "Nav next button is missing"
    assert app_dialog.root.captions["My Tasks"].exists(), "Not the right breadcrumb"

    # Make sure the all tabs are showing up.
    assert app_dialog.root.tabs["My Tasks"].exists(), "My Tasks tab is missing"
    assert app_dialog.root.tabs["Assets"].exists(), "Assets tab is missing"
    assert app_dialog.root.tabs["Shots"].exists(), "Shots tab is missing"
    assert app_dialog.root.tabs["All"].exists(), "All tab is missing"
    assert app_dialog.root.tabs["Working"].exists(), "Working tab is missing"
    assert app_dialog.root.tabs["Publishes"].exists(), "Publishes tab is missing"

    # Make sure all buttons are showing up
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    assert app_dialog.root.buttons[
        "+ New File"
    ].exists(), "+ New File button is missing"
    assert app_dialog.root.buttons["Cancel"].exists(), "Cancel button is missing"
    assert app_dialog.root.buttons["Open"].exists(), "Open button is missing"

    # Make sure all test fields are showing up
    assert app_dialog.root[
        "Search All Files"
    ].exists(), "Search All Files text field is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search My Tasks text field is missing"

    # Make sure all checkboxes are showing up
    assert app_dialog.root.checkboxes[
        "All Versions"
    ].exists(), "All Versions checkbox is missing"


def test_assets_tab(app_dialog):
    """
    Asset tab validation
    """
    # Select the Assets tab
    app_dialog.root.tabs["Assets"].mouseClick()

    # Make sure all expected UI is showing up
    assert app_dialog.root.captions[
        "Filter by Pipeline Step"
    ].exists(), "Pipeline Step filters are missing"
    assert app_dialog.root.buttons[
        "Select All"
    ].exists(), "Pipeline Step filters Select All button is missing"
    assert app_dialog.root.buttons[
        "Select None"
    ].exists(), "Pipeline Step filters Select None button is missing"
    assert app_dialog.root.checkboxes[
        "My Tasks Only"
    ].exists(), "My Tasks Only checkbox is missing"
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search Assets text field is missing"

    # Got to the model task and validate breadcrumb
    app_dialog.root.outlineitems["Character"].waitExist(timeout=30)
    app_dialog.root.outlineitems["Character"].mouseDoubleClick()
    app_dialog.root.outlineitems["AssetAutomation"].waitExist(timeout=30)
    app_dialog.root.outlineitems["AssetAutomation"].mouseDoubleClick()
    app_dialog.root.outlineitems["Model"].waitExist(timeout=30)

    # Validate content dialog
    assert app_dialog.root.cells[
        "AssetAutomation"
    ].exists(), "AssetAutomation is missing in content dialog"
    assert app_dialog.root.cells[
        "Model - Model"
    ].exists(), "Model task is missing in content dialog"
    assert app_dialog.root.cells[
        "Rig - Rig"
    ].exists(), "Rig task is missing in content dialog"

    # Search in the content dialog for Rig and make sure Model is not showing up anymore
    app_dialog.root["Search All Files"].typeIn("Rig" "{ENTER}")
    assert app_dialog.root.cells[
        "Rig - Rig"
    ].exists(), "Rig task should be visible in content dialog"
    assert (
        app_dialog.root.cells["Model - Model"].exists() is False
    ), "Model task shouldn't be visible in content dialog"

    # Remove text in the search field and make sure Modal task is back
    app_dialog.root["Search All Files"].buttons.mouseClick()
    assert app_dialog.root.cells[
        "Model - Model"
    ].exists(), "Model task should be visible in content dialog"

    # Select Model task
    app_dialog.root.outlineitems["Model"].mouseDoubleClick()
    app_dialog.root.outlineitems["Model"][1].waitExist(timeout=30)
    app_dialog.root.outlineitems["Model"][1].mouseClick()

    # Validate content dialog
    assert app_dialog.root.cells["Model - Model"].exists(), "Not on the right tasks"

    # Validate breadcrumb
    assert app_dialog.root.captions[
        "Assets * Character * Asset AssetAutomation * Step Model * Task Model"
    ].exists(), "Breadcrumb not on the right task"

    # Click on the back navigation button until back to the Assets context
    for _i in range(0, 4):
        # Click on the back navigation button
        app_dialog.root.buttons["nav_prev_btn"].mouseClick()

    # Validate Breadcrumb widget is only showing the project context
    assert app_dialog.root.captions[
        "Assets"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Enable My Tasks Only and make sure Model task is not showing up anymore
    app_dialog.root.checkboxes["My Tasks Only"].mouseClick()
    assert (
        app_dialog.root.outlineitems["Model"].exists() is False
    ), "Model task shouldn't be visible"


def test_shots_tab(app_dialog):
    """
    Shot tab validation
    """
    # Select the Shots tab
    app_dialog.root.tabs["Shots"].mouseClick()

    # Make sure all expected UI is showing up
    assert app_dialog.root.captions[
        "Filter by Pipeline Step"
    ].exists(), "Pipeline Step filters are missing"
    assert app_dialog.root.buttons[
        "Select All"
    ].exists(), "Pipeline Step filters Select All button is missing"
    assert app_dialog.root.buttons[
        "Select None"
    ].exists(), "Pipeline Step filters Select None button is missing"
    assert app_dialog.root.checkboxes[
        "My Tasks Only"
    ].exists(), "My Tasks Only checkbox is missing"
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search Shots text field is missing"

    # Got to the model task and validate breadcrumb
    app_dialog.root.outlineitems["seq_001"].waitExist(timeout=30)
    app_dialog.root.outlineitems["seq_001"].mouseDoubleClick()
    app_dialog.root.outlineitems["shot_001"].waitExist(timeout=30)
    app_dialog.root.outlineitems["shot_001"].mouseDoubleClick()
    app_dialog.root.outlineitems["Comp"].waitExist(timeout=30)

    # Validate content dialog
    assert app_dialog.root.cells[
        "shot_001"
    ].exists(), "shot_001 is missing in content dialog"
    assert app_dialog.root.cells[
        "Comp - Comp"
    ].exists(), "Comp task is missing in content dialog"
    assert app_dialog.root.cells[
        "Light - Light"
    ].exists(), "Light task is missing in content dialog"
    app_dialog.root.outlineitems["Comp"].mouseDoubleClick()
    app_dialog.root.outlineitems["Comp"][1].waitExist(timeout=30)
    app_dialog.root.outlineitems["Comp"][1].mouseClick()

    # Validate content dialog
    assert app_dialog.root.cells["Comp - Comp"].exists(), "Not on the right tasks"

    # Validate breadcrumb
    assert app_dialog.root.captions[
        "Shots * Sequence seq_001 * Shot shot_001 * Step Comp * Task Comp"
    ].exists(), "Breadcrumb not on the right task"

    # Click on the back navigation button until back to the Assets context
    for _i in range(0, 4):
        # Click on the back navigation button
        app_dialog.root.buttons["nav_prev_btn"].mouseClick()

    # Validate Breadcrumb widget is only showing the project context
    assert app_dialog.root.captions[
        "Shots"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Unselect all Pipeline Step filters and make sure Comp task is no more showing up
    app_dialog.root.buttons["Select None"].mouseClick()
    assert (
        app_dialog.root.outlineitems["Comp"].exists() is False
    ), "Comp task shouldn't be visible"
    assert (
        app_dialog.root.cells["Comp - Comp"].exists() is False
    ), "Comp task shouldn't be visible in content dialog"

    # Select all Pipeline Step filters and make sure Comp task is showing up
    app_dialog.root.buttons["Select All"].mouseClick()
    app_dialog.root.outlineitems["Comp"].waitExist(timeout=30)
    assert app_dialog.root.outlineitems["Comp"].exists(), "Comp task should be visible"

    # Search for Anm and make sure Comp is not showing up anymore
    app_dialog.root["Search Entity"].typeIn("Light" "{ENTER}")
    assert app_dialog.root.outlineitems[
        "Light"
    ].exists(), "Light task should be visible"
    assert (
        app_dialog.root.outlineitems["Comp"].exists() is False
    ), "Comp task shouldn't be visible"
