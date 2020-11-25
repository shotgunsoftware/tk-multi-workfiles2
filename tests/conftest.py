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
from tk_toolchain.authentication import get_toolkit_user

try:
    from MA.UI import topwindows
except ImportError:
    pytestmark = pytest.mark.skip()


@pytest.fixture(scope="session")
def shotgun():
    """
    Provides a connection to Shotgun.
    """
    sg = get_toolkit_user().create_sg_connection()

    return sg


@pytest.fixture(scope="session")
def sg_project(shotgun):
    """
    Generates a fresh Shotgun Project to use with the WF2 UI Automation.
    """
    # Create or update the integration_tests local storage with the current test run
    storage_name = "WF2 UI Tests"
    local_storage = shotgun.find_one(
        "LocalStorage", [["code", "is", storage_name]], ["code"]
    )
    if local_storage is None:
        local_storage = shotgun.create("LocalStorage", {"code": storage_name})

    # Always update local storage path
    local_storage["path"] = os.path.join(
        os.path.expandvars("${SHOTGUN_CURRENT_REPO_ROOT}"), "tests", "fixtures", "files"
    )
    shotgun.update(
        "LocalStorage", local_storage["id"], {"windows_path": local_storage["path"]}
    )

    # Make sure there is not already an automation project created
    filters = [["name", "is", "Toolkit WF2 UI Automation"]]
    existed_project = shotgun.find_one("Project", filters)
    if existed_project is not None:
        shotgun.delete(existed_project["type"], existed_project["id"])

    # Create a new project without template. This mean it will use the default one.
    project_data = {
        "sg_description": "Project Created by Automation",
        "name": "Toolkit WF2 UI Automation",
        "tank_name": "Toolkit WF2 UI Automation",
    }
    new_project = shotgun.create("Project", project_data)

    return new_project


@pytest.fixture(scope="session")
def sg_entities(sg_project, shotgun):
    """
    Creates Shotgun entities which will be used in different test cases.
    """
    # Create a Sequence to be used by the Shot creation
    sequence_data = {
        "project": sg_project,
        "code": "seq_001",
        "sg_status_list": "ip",
    }
    new_sequence = shotgun.create("Sequence", sequence_data)

    # Validate if Automation shot task template exists
    shot_template_filters = [["code", "is", "Automation Shot Task Template"]]
    existed_shot_template = shotgun.find_one("TaskTemplate", shot_template_filters)
    if existed_shot_template is not None:
        shotgun.delete(existed_shot_template["type"], existed_shot_template["id"])
    # Create a shot task templates
    shot_template_data = {
        "code": "Automation Shot Task Template",
        "description": "This shot task template was created by the WF2 UI automation",
        "entity_type": "Shot",
    }
    shot_task_template = shotgun.create("TaskTemplate", shot_template_data)

    # Create Comp and Light tasks
    for shot_task_name in ["Comp", "Light"]:
        # Get the Pipeline step task name
        shot_pipeline_step_filter = [["code", "is", shot_task_name]]
        shot_pipeline_step = shotgun.find_one("Step", shot_pipeline_step_filter)
        # Create task
        shot_task_data = {
            "content": shot_task_name,
            "step": shot_pipeline_step,
            "task_template": shot_task_template,
        }
        shotgun.create("Task", shot_task_data)

    # Validate if Automation asset task template exists
    asset_template_filters = [["code", "is", "Automation Asset Task Template"]]
    existed_asset_template = shotgun.find_one("TaskTemplate", asset_template_filters)
    if existed_asset_template is not None:
        shotgun.delete(existed_asset_template["type"], existed_asset_template["id"])
    # Create an asset task templates
    asset_template_data = {
        "code": "Automation Asset Task Template",
        "description": "This asset task template was created by the WF2 UI automation",
        "entity_type": "Asset",
    }
    asset_task_template = shotgun.create("TaskTemplate", asset_template_data)

    # Create Model and Rig tasks
    for asset_task_name in ["Model", "Rig"]:
        # Get the Pipeline step task name
        asset_pipeline_step_filter = [["code", "is", asset_task_name]]
        asset_pipeline_step = shotgun.find_one("Step", asset_pipeline_step_filter)
        # Create task
        asset_task_data = {
            "content": asset_task_name,
            "step": asset_pipeline_step,
            "task_template": asset_task_template,
        }
        shotgun.create("Task", asset_task_data)

    # Create a new shot
    shot_data = {
        "project": sg_project,
        "sg_sequence": new_sequence,
        "code": "shot_001",
        "description": "This shot was created by the WF2 UI automation",
        "sg_status_list": "ip",
        "task_template": shot_task_template,
    }
    shotgun.create("Shot", shot_data)

    # Create a new asset
    asset_data = {
        "project": sg_project,
        "code": "AssetAutomation",
        "description": "This asset was created by the WF2 UI automation",
        "sg_status_list": "ip",
        "sg_asset_type": "Character",
        "task_template": asset_task_template,
    }
    asset = shotgun.create("Asset", asset_data)

    # Get the publish_file_type id to be passed in the publish creation
    published_file_type_filters = [["code", "is", "Image"]]
    published_file_type = shotgun.find_one(
        "PublishedFileType", published_file_type_filters
    )

    # File to publish
    file_to_publish = os.path.join(
        os.path.expandvars("${TK_TEST_FIXTURES}"), "files", "images", "sven.png"
    )

    # Find the model task to publish to
    filters = [
        ["project", "is", sg_project],
        ["entity.Asset.code", "is", asset["code"]],
        ["step.Step.code", "is", "model"],
    ]
    fields = ["sg_status_list"]
    model_task = shotgun.find_one("Task", filters, fields)

    # Create a published file
    publish_data = {
        "project": sg_project,
        "code": "sven.png",
        "name": "sven.png",
        "description": "This file was published by the WF2 UI automation",
        "published_file_type": published_file_type,
        "path": {"local_path": file_to_publish},
        "entity": asset,
        "task": model_task,
        "version_number": 1,
    }
    shotgun.create("PublishedFile", publish_data)


# This fixture will launch tk-run-app on first usage
# and will remain valid until the test run ends.
@pytest.fixture(scope="module")
def host_application(sg_project, sg_entities, commands):
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

    # Make sure all text fields are showing up
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


@pytest.fixture(scope="module")
def test_my_tasks_tab(app_dialog, sg_project, file_dialog):
    """
    Basic UI validation to make sure all buttons, tabs and fields are available
    """
    # Make Sure the File Open dialog is showing up in the right context
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
    # Button only in Open file dialog
    if file_dialog[1] == "Open":
        assert app_dialog.root.buttons[
            "+ New File"
        ].exists(), "+ New File button is missing"
    # Button only in Open file dialog
    elif file_dialog[1] == "Save":
        assert app_dialog.root.buttons[
            "Open"
        ].exists(), "Open file type button is missing"
    assert app_dialog.root.buttons[
        "+ New Task"
    ].exists(), "+ New Task button is missing"
    # Buttons in both, Open and Save file dialog
    assert app_dialog.root.buttons["Cancel"].exists(), "Cancel button is missing"
    assert app_dialog.root.buttons[
        file_dialog[1]
    ].exists(), "Open/Save button is missing"

    # Make sure all text fields are showing up
    # text fields in both, Open and Save file dialog
    assert app_dialog.root[
        "Search All Files"
    ].exists(), "Search All Files text field is missing"
    assert app_dialog.root[
        "Search Entity"
    ].exists(), "Search My Tasks text field is missing"
    # text fields only in Save file dialog
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


@pytest.fixture(scope="module")
def test_assets_tab(app_dialog):
    """
    Asset tab UI validation.
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


@pytest.fixture(scope="module")
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
