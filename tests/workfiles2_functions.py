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


def _test_my_tasks_tab(app_dialog, sg_project, file_dialog):
    """
    Basic My Tasks tab UI validation to make sure all buttons, tabs and fields are available
    """
    # Make Sure the File dialog is showing up in the right context
    assert app_dialog.root.captions[
        file_dialog[0]
    ].exists(), "Not the right File dialog"
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
    # Button only in File Open dialog
    if file_dialog[1] == "Open":
        assert app_dialog.root.buttons[
            "+ New File"
        ].exists(), "+ New File button is missing"
    # Button only in File Save dialog
    elif file_dialog[1] == "Save":
        assert app_dialog.root.buttons[
            "Open"
        ].exists(), "Open file type button is missing"
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    # Buttons in both, File Open and File Save dialogs
    assert app_dialog.root.buttons["Cancel"].exists(), "Cancel button is missing"
    assert app_dialog.root.buttons[
        file_dialog[1]
    ].exists(), "Open/Save button is missing"

    # Make sure all text fields are showing up
    # text fields in both, File Open and File Save dialogs
    assert app_dialog.root[
        "Search All Files"
    ].exists(), "Search All Files text field is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search My Tasks text field is missing"
    # text fields only in File Save dialog
    if file_dialog[1] == "Save":
        assert app_dialog.root.textfields[
            "Name Edit"
        ].exists(), "Name text field is missing"
        assert app_dialog.root.textfields[
            "Version Number"
        ].exists(), "Version text field is missing"

    # Make sure all checkboxes are showing up
    if file_dialog[1] == "Open":
        assert app_dialog.root.checkboxes[
            "All Versions"
        ].exists(), "All Versions checkbox is missing"
    elif file_dialog[1] == "Save":
        assert app_dialog.root.checkboxes[
            "Use Next Available Version Number"
        ].exists(), "Use Next Available Version Number checkbox is missing"
        assert app_dialog.root.checkboxes[
            "Use Next Available Version Number"
        ].checked, (
            "Use Next Available Version Number checkbox should be checked by default"
        )


def _test_expected_ui_showing(app_dialog, tab_name):
    """
    Basic tabs UI validation to make sure all buttons, tabs and fields are available
    """
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
    ].exists(), "Search {0} text field is missing".format(tab_name)


def _navigate_and_validate_breadcrumb(app_dialog, selection_hierarchy, entities):
    """
    Navigation and breadcrumb validation
    """
    # Got to the model task and validate breadcrumb

    for num, item in enumerate(selection_hierarchy):

        app_dialog.root.outlineitems[item].waitExist(timeout=30)
        if num + 1 != len(selection_hierarchy):
            # If we are not in the last item in the hierarchy then click the item
            app_dialog.root.outlineitems[item].mouseDoubleClick()

    # Validate content dialog
    assert app_dialog.root.cells[
        selection_hierarchy[1]
    ].exists(), "{0} is missing in content dialog".format(selection_hierarchy[1])
    assert app_dialog.root.cells[
        "{0} - {0}".format(selection_hierarchy[2])
    ].exists(), "{0} task is missing in content dialog".format(selection_hierarchy[2])
    assert app_dialog.root.cells[
        "{0} - {0}".format(entities[3])
    ].exists(), "{0} task is missing in content dialog".format(entities[3])


def _test_tab(app_dialog, tab_name, selection_hierarchy, entities):
    """
    Assets/Shots tabs UI validation.
    """
    # Select an entity tab
    app_dialog.root.tabs[tab_name].mouseClick()

    _test_expected_ui_showing(app_dialog, tab_name)

    _navigate_and_validate_breadcrumb(app_dialog, selection_hierarchy, entities)

    # Search in the content dialog for a specific task and make sure other tasks are not showing up anymore
    app_dialog.root["Search All Files"].pasteIn(entities[3], enter=True)
    assert app_dialog.root.cells[
        "{0} - {0}".format(entities[3])
    ].exists(), "{0} task should be visible in content dialog".format(entities[3])
    assert (
        app_dialog.root.cells["{0} - {0}".format(entities[2])].exists() is False
    ), "{0} task shouldn't be visible in content dialog".format(entities[2])

    # Remove text in the search field and make sure all tasks are back
    app_dialog.root["Search All Files"].buttons.mouseClick()
    assert app_dialog.root.cells[
        "{0} - {0}".format(entities[2])
    ].exists(), "{0} task should be visible in content dialog".format(entities[2])

    # Select a specific task
    app_dialog.root.outlineitems[entities[2]].mouseDoubleClick()
    app_dialog.root.outlineitems[entities[2]][1].waitExist(timeout=30)
    app_dialog.root.outlineitems[entities[2]][1].mouseClick()

    # Validate content dialog
    assert app_dialog.root.cells[
        "{0} - {0}".format(entities[2])
    ].exists(), "Not on the right tasks"

    # Validate breadcrumb
    assert app_dialog.root.captions[
        "{0}*{1}*{2}*{3}*Step*{4}*Task*{4}".format(
            tab_name, selection_hierarchy[0], entities[0], entities[1], entities[2]
        )
    ].exists(), "Breadcrumb not on the right task"

    # Click on the back navigation button until back to the entity context
    for _i in range(0, 4):
        # Click on the back navigation button
        app_dialog.root.buttons["nav_prev_btn"].mouseClick()

    # Validate Breadcrumb widget is only showing the entity context
    assert app_dialog.root.captions[
        tab_name
    ].exists(), "Breadcrumb widget is not set correctly"

    # Unselect all Pipeline Step filters and make sure tasks are not showing up anymore
    app_dialog.root.buttons["Select None"].mouseClick()
    assert (
        app_dialog.root.outlineitems[entities[2]].exists() is False
    ), "{0} task shouldn't be visible".format(entities[2])
    assert (
        app_dialog.root.cells["{0} - {0}".format(entities[2])].exists() is False
    ), "{0} task shouldn't be visible in content dialog".format(entities[2])

    # Select all Pipeline Step filters and make sure all tasks are showing up
    app_dialog.root.buttons["Select All"].mouseClick()
    app_dialog.root.outlineitems[entities[2]].waitExist(timeout=30)
    assert app_dialog.root.outlineitems[
        entities[2]
    ].exists(), "{0} task should be visible".format(entities[2])

    # Search for a specific task and make sure other tasks are not showing up anymore
    app_dialog.root["Search Entity"].pasteIn(entities[3], enter=True)
    assert app_dialog.root.outlineitems[
        entities[3]
    ].exists(), "{0} task should be visible".format(entities[3])
    assert (
        app_dialog.root.outlineitems[entities[2]].exists() is False
    ), "{0} task shouldn't be visible".format(entities[2])

    # Enable My Tasks Only and make sure tasks are not showing up anymore
    app_dialog.root.checkboxes["My Tasks Only"].mouseClick()
    assert (
        app_dialog.root.outlineitems[entities[3]].exists() is False
    ), "{0} task shouldn't be visible".format(entities[3])
