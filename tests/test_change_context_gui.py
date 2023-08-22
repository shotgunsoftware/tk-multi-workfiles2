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

try:
    from MA.UI import topwindows
except ImportError:
    pytestmark = pytest.mark.skip()


@pytest.fixture(scope="module")
def commands():
    """
    Return the command to launch Workfiles2 in different mode.
    This fixture is used by the host_application fixture in conftest.py
    """
    return "change_context"


@pytest.fixture(scope="module")
def window_name():
    """
    Return the window app name.
    This fixture is used by the app_dialog fixture in conftest.py
    """
    return "ShotGrid: Change Context"


def test_ui_validation(app_dialog, tk_test_project):
    """
    Basic UI validation to make sure all buttons, tabs and fields are available
    """
    # Make Sure the Change Context dialog is showing up in the right context
    assert app_dialog.root.captions[
        "Change Context"
    ].exists(), "Not the Change Context dialog"
    assert app_dialog.root.captions[
        "*Project " + tk_test_project["name"]
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

    # Make sure all buttons are showing up
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    assert app_dialog.root.buttons["Cancel"].exists(), "Cancel button is missing"
    assert app_dialog.root.buttons["Change Context"].exists(), "Open button is missing"

    # Make sure all test fields are showing up
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search My Tasks text field is missing"
    # Create a new task and select it
    app_dialog.root.tabs["Assets"].mouseClick()
    app_dialog.root.outlineitems["Character"].waitExist(timeout=30)
    app_dialog.root.outlineitems["Character"].mouseDoubleClick()
    app_dialog.root.outlineitems["AssetAutomation"].waitExist(timeout=30)
    app_dialog.root.outlineitems["AssetAutomation"].mouseDoubleClick()
    app_dialog.root.buttons["+ New Task"].mouseClick()
    app_dialog.root.dialogs["ShotGrid: Create New Task"].waitExist(timeout=30)
    app_dialog.root.dialogs["ShotGrid: Create New Task"].textfields[
        "Task Name"
    ].pasteIn("New Texture Task")
    app_dialog.root.dialogs["ShotGrid: Create New Task"].dropdowns[
        "Pipeline Step"
    ].mouseClick()
    topwindows.listitems["Texture"].waitExist(timeout=30)
    topwindows.listitems["Texture"].mouseClick()
    app_dialog.root.dialogs["ShotGrid: Create New Task"].buttons["Create"].mouseClick()
    app_dialog.root.outlineitems["Texture"].waitExist(timeout=30)
    # Enable My Tasks Only and make sure Model task is not showing up anymore
    app_dialog.root.checkboxes["My Tasks Only"].mouseClick()
    assert app_dialog.root.outlineitems[
        "Texture"
    ].exists(), "New Texture task should be visible"

    # Go back to My Tasks and make sure New Texture Task is showing up and select it
    app_dialog.root.tabs["My Tasks"].mouseClick()
    app_dialog.root.outlineitems["New Texture Task"].waitExist(timeout=30)
    app_dialog.root.outlineitems["New Texture Task"].mouseClick()
    assert (
        app_dialog.root.outlineitems["New Texture Task"].selected
        or app_dialog.root.outlineitems["New Texture Task"].focused is True
    )
