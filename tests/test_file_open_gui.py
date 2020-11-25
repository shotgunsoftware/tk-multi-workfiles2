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
    Return the command to run to launch Workfiles2 in different state
    """
    return "file_open"


@pytest.fixture(scope="module")
def window_name():
    """
    Return the window app name
    """
    return "Shotgun: File Open"


@pytest.fixture(scope="module")
def file_dialog():
    """
    Return the window app name
    """
    return ("File Open", "Open")


def test_tabs(test_my_tasks_tab, test_assets_tab, test_shots_tab):
    """
    Assets and Shots tabs validation
    """
