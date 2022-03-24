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
    from MA.UI import first
except ImportError:
    pytestmark = pytest.mark.skip()


def _test_my_tasks_tab(app_dialog, tk_test_project):
    """
    Basic My Tasks tab UI validation to make sure all buttons, tabs and fields are available
    """
    # Make Sure the File dialog is showing up in the right context
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
    assert app_dialog.root.tabs["All"].exists(), "All tab is missing"
    assert app_dialog.root.tabs["Working"].exists(), "Working tab is missing"
    assert app_dialog.root.tabs["Publishes"].exists(), "Publishes tab is missing"

    # Buttons in both, File Open and File Save dialogs
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    assert app_dialog.root.buttons["Cancel"].exists(), "Cancel button is missing"

    # Make sure all text fields are showing up
    # text fields in both, File Open and File Save dialogs
    assert app_dialog.root[
        "Search All Files"
    ].exists(), "Search All Files text field is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search My Tasks text field is missing"


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


def _navigate_and_validate_content(app_dialog, selection_hierarchy, task):
    """
    Navigation and content dialog validation
    """
    # Got to the model task and validate content dialog

    for num, item in enumerate(selection_hierarchy):

        app_dialog.root.outlineitems[item].waitExist(timeout=30)
        if num + 1 != len(selection_hierarchy):
            # If we are not in the last item in the hierarchy then click the item
            app_dialog.root.outlineitems[item].mouseDoubleClick()

    # Validate content dialog
    # Cells are not showing up with PySide2, it is only seeing them as text.
    assert (
        app_dialog.root.cells[selection_hierarchy[1]].exists()
        or app_dialog.root.captions[selection_hierarchy[1]].exists()
    ), "{0} is missing in content dialog".format(selection_hierarchy[1])
    assert (
        app_dialog.root.cells["{0} - {0}".format(selection_hierarchy[2])].exists()
        or app_dialog.root.captions["{0} - {0}".format(selection_hierarchy[2])].exists()
    ), "{0} task is missing in content dialog".format(selection_hierarchy[2])
    assert (
        app_dialog.root.cells["{0} - {0}".format(task)].exists()
        or app_dialog.root.captions["{0} - {0}".format(task)].exists()
    ), "{0} task is missing in content dialog".format(task)


def _search_all(app_dialog, step, task):
    # Search in the content dialog for a specific task and make sure other tasks are not showing up anymore
    # Cells are not showing up with PySide2, it is only seeing them as text.
    app_dialog.root["Search All Files"].pasteIn(task, enter=True)
    assert (
        app_dialog.root.cells["{0} - {0}".format(task)].exists()
        or app_dialog.root.captions["{0} - {0}".format(task)].exists()
    ), "{0} task should be visible in content dialog".format(task)
    assert (
        app_dialog.root.cells["{0} - {0}".format(step)].exists()
        or app_dialog.root.captions["{0} - {0}".format(step)].exists() is False
    ), "{0} task shouldn't be visible in content dialog".format(step)

    # Remove text in the search field and make sure all tasks are back
    app_dialog.root["Search All Files"].buttons.mouseClick()
    assert (
        app_dialog.root.cells["{0} - {0}".format(step)].exists()
        or app_dialog.root.captions["{0} - {0}".format(step)].exists()
    ), "{0} task should be visible in content dialog".format(step)


def _breadcrumb_validation(
    app_dialog, tab_name, selection_hierarchy, entity, entity_type, step
):
    # Select a specific task
    app_dialog.root.outlineitems[step].mouseDoubleClick()
    app_dialog.root.outlineitems[step][1].waitExist(timeout=30)
    app_dialog.root.outlineitems[step][1].mouseClick()

    # Validate content dialog
    # Cells are not showing up with PySide2, it is only seeing them as text.
    assert (
        app_dialog.root.cells["{0} - {0}".format(step)].exists()
        or app_dialog.root.captions["{0} - {0}".format(step)].exists()
    ), "Not on the right tasks"

    # Validate breadcrumb
    assert app_dialog.root.captions[
        "{0}*{1}*{2}*{3}*Step*{4}*Task*{4}".format(
            tab_name, selection_hierarchy[0], entity, entity_type, step
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


def _hierarchy_view(app_dialog, step, task):
    # Unselect all Pipeline Step filters and make sure tasks are not showing up anymore
    # Cells are not showing up with PySide2, it is only seeing them as text.
    app_dialog.root.buttons["Select None"].mouseClick()
    assert (
        app_dialog.root.outlineitems[step].exists() is False
    ), "{0} task shouldn't be visible".format(step)
    assert (
        app_dialog.root.cells["{0} - {0}".format(step)].exists()
        or app_dialog.root.captions["{0} - {0}".format(step)].exists() is False
    ), "{0} task shouldn't be visible in content dialog".format(step)

    # Select all Pipeline Step filters and make sure all tasks are showing up
    app_dialog.root.buttons["Select All"].mouseClick()
    app_dialog.root.outlineitems[step].waitExist(timeout=30)
    assert app_dialog.root.outlineitems[
        step
    ].exists(), "{0} task should be visible".format(step)

    # Search for a specific task and make sure other tasks are not showing up anymore
    app_dialog.root["Search Entity"].pasteIn(task, enter=True)
    assert app_dialog.root.outlineitems[
        task
    ].exists(), "{0} task should be visible".format(task)
    assert (
        app_dialog.root.outlineitems[step].exists() is False
    ), "{0} task shouldn't be visible".format(step)

    # Enable My Tasks Only and make sure tasks are not showing up anymore
    app_dialog.root.checkboxes["My Tasks Only"].mouseClick()
    assert (
        app_dialog.root.outlineitems[task].exists() is False
    ), "{0} task shouldn't be visible".format(task)


def _test_tab(
    app_dialog, tab_name, selection_hierarchy, entity, entity_type, step, task
):
    """
    Assets/Shots tabs UI validation.
    """
    # Select an entity tab
    app_dialog.root.tabs[tab_name].mouseClick()

    # Make sure UI dialog display all items
    activityDialog = first(app_dialog.root)
    width, height = activityDialog.size
    app_dialog.root.mouseClick(width * 0, height * 0.5)

    # Validate the expected UI is available
    _test_expected_ui_showing(app_dialog, tab_name)

    # Navigate in the hierarchy view and make sure the content dialog has the right information
    _navigate_and_validate_content(app_dialog, selection_hierarchy, task)

    # Test search all text field
    _search_all(app_dialog, step, task)

    # Breadcrumb validation
    _breadcrumb_validation(
        app_dialog, tab_name, selection_hierarchy, entity, entity_type, step
    )

    # Hierarchy view validation
    _hierarchy_view(app_dialog, step, task)
