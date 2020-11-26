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
    Return the command to run to launch Workfiles2 in different state
    """
    return "file_save"


@pytest.fixture(scope="module")
def window_name():
    """
    Return the window app name
    """
    return "Shotgun: File Save"


@pytest.fixture(scope="module")
def file_dialog():
    """
    Return the file dialog name
    """
    return ("File Save", "Save")


def test_my_tasks(app_dialog, sg_project, file_dialog):
    """
    Basic My Tasks tab UI validation to make sure all buttons, tabs and fields are available
    """
    _test_my_tasks_tab(app_dialog, sg_project, file_dialog)


# Parametrize decorator to run the same functions for Assets and Shots tabs.
@pytest.mark.parametrize(
    "tab_name, selection_hierarchy, entities",
    [
        (
            "Assets",
            ("Character", "AssetAutomation", "Model"),
            ("Asset", "AssetAutomation", "Model", "Rig"),
        ),
        (
            "Shots",
            ("seq_001", "shot_001", "Comp"),
            ("Shot", "shot_001", "Comp", "Light"),
        ),
    ],
)
def test_tabs(app_dialog, tab_name, selection_hierarchy, entities):
    """
    Assets/Shots tabs UI validation.
    """
    _test_tab(app_dialog, tab_name, selection_hierarchy, entities)
