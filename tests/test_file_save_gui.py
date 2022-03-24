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
from workfiles2_functions import _test_my_tasks_tab, _test_tab

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
    return "file_save"


@pytest.fixture(scope="module")
def window_name():
    """
    Return the window app name.
    This fixture is used by the app_dialog fixture in conftest.py
    """
    return "ShotGrid: File Save"


def test_my_tasks(app_dialog, tk_test_project):
    """
    Basic My Tasks tab UI validation to make sure all buttons, tabs and fields are available
    """
    # Validate that the right Workfiles 2 dialog mode is launched
    assert app_dialog.root.captions["File Save"].exists(), "Not the File Open dialog"

    # Validate File Save dialog buttons
    assert app_dialog.root.dropdowns[
        "File Type"
    ].exists(), "Open file type drop down menu is missing"
    assert app_dialog.root.buttons["Save"].exists(), "Save button is missing"

    # Validate File Save dialog text fields
    assert app_dialog.root.textfields[
        "Name Edit"
    ].exists(), "Name text field is missing"
    assert app_dialog.root["Version Number"].exists(), "Version text field is missing"

    # Validate File Save dialog checkboxes
    assert app_dialog.root.checkboxes[
        "Use Next Available Version Number"
    ].exists(), "Use Next Available Version Number checkbox is missing"
    assert app_dialog.root.checkboxes[
        "Use Next Available Version Number"
    ].checked, "Use Next Available Version Number checkbox should be checked by default"

    # My Tasks tab general UI validation
    _test_my_tasks_tab(app_dialog, tk_test_project)


# Parametrize decorator to run the same functions for Assets and Shots tabs.
@pytest.mark.parametrize(
    "tab_name, selection_hierarchy, entity, entity_type, step, task",
    [
        (
            "Assets",
            # Names of the tree items in the selection order
            ("Character", "AssetAutomation", "Model"),
            "Asset",
            "AssetAutomation",
            "Model",
            "Rig",
        ),
        (
            "Shots",
            # Names of the tree items in the selection order
            ("seq_001", "shot_001", "Comp"),
            "Shot",
            "shot_001",
            "Comp",
            "Light",
        ),
    ],
)
def test_tabs(
    app_dialog, tab_name, selection_hierarchy, entity, entity_type, step, task
):
    """
    Assets/Shots tabs UI validation.
    """
    _test_tab(
        app_dialog, tab_name, selection_hierarchy, entity, entity_type, step, task
    )
