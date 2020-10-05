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
from tk_toolchain.authentication import get_toolkit_user

try:
    from MA.UI import topwindows
except ImportError:
    pytestmark = pytest.mark.skip()


@pytest.fixture(scope="session")
def context():
    # Tasks in Toolkit File Open UI Automation project which we're going to use
    # in different test cases.
    # Get credentials from TK_TOOLCHAIN
    sg = get_toolkit_user().create_sg_connection()

    # Create or update the integration_tests local storage with the current test run
    storage_name = "File Open UI Tests"
    local_storage = sg.find_one(
        "LocalStorage", [["code", "is", storage_name]], ["code"]
    )
    if local_storage is None:
        local_storage = sg.create("LocalStorage", {"code": storage_name})

    # Always update local storage path
    local_storage["path"] = os.path.expandvars("${SHOTGUN_CURRENT_REPO_ROOT}")
    sg.update(
        "LocalStorage", local_storage["id"], {"windows_path": local_storage["path"]}
    )

    # Make sure there is not already an automation project created
    filters = [["name", "is", "Toolkit File Open UI Automation"]]
    existed_project = sg.find_one("Project", filters)
    if existed_project is not None:
        sg.delete(existed_project["type"], existed_project["id"])

    # Create a new project without template. This mean it will use the default one.
    project_data = {
        "sg_description": "Project Created by Automation",
        "name": "Toolkit File Open UI Automation",
    }
    new_project = sg.create("Project", project_data)

    # Create a Sequence to be used by the Shot creation
    sequence_data = {
        "project": new_project,
        "code": "seq_001",
        "sg_status_list": "ip",
    }
    new_sequence = sg.create("Sequence", sequence_data)

    # Validate if Automation shot task template exists
    shot_template_filters = [["code", "is", "Automation Shot Task Template"]]
    existed_shot_template = sg.find_one("TaskTemplate", shot_template_filters)
    if existed_shot_template is not None:
        sg.delete(existed_shot_template["type"], existed_shot_template["id"])
    # Create a shot task templates
    shot_template_data = {
        "code": "Automation Shot Task Template",
        "description": "This shot task template was created by the File Open UI automation",
        "entity_type": "Shot",
    }
    shot_task_template = sg.create("TaskTemplate", shot_template_data)
    # Get the Comp Pipeline step ID
    comp_pipeline_step_filter = [["code", "is", "Comp"]]
    comp_pipeline_step = sg.find_one("Step", comp_pipeline_step_filter)
    # Create Comp task
    comp_task_data = {
        "content": "Comp",
        "step": comp_pipeline_step,
        "task_template": shot_task_template,
    }
    sg.create("Task", comp_task_data)
    # Get the Light Pipeline step ID
    light_pipeline_step_filter = [["code", "is", "Light"]]
    light_pipeline_step = sg.find_one("Step", light_pipeline_step_filter)
    # Create Light task
    light_task_data = {
        "content": "Light",
        "step": light_pipeline_step,
        "task_template": shot_task_template,
    }
    sg.create("Task", light_task_data)
    # Validate if Automation asset task template exists
    asset_template_filters = [["code", "is", "Automation Asset Task Template"]]
    existed_asset_template = sg.find_one("TaskTemplate", asset_template_filters)
    if existed_asset_template is not None:
        sg.delete(existed_asset_template["type"], existed_asset_template["id"])
    # Create an asset task templates
    asset_template_data = {
        "code": "Automation Asset Task Template",
        "description": "This asset task template was created by the File Open UI automation",
        "entity_type": "Asset",
    }
    asset_task_template = sg.create("TaskTemplate", asset_template_data)
    # Get the Model Pipeline step ID
    model_pipeline_step_filter = [["code", "is", "Model"]]
    model_pipeline_step = sg.find_one("Step", model_pipeline_step_filter)
    # Create Model task
    model_task_data = {
        "content": "Model",
        "step": model_pipeline_step,
        "task_template": asset_task_template,
    }
    sg.create("Task", model_task_data)
    # Get the Rig Pipeline step ID
    rig_pipeline_step_filter = [["code", "is", "Rig"]]
    rig_pipeline_step = sg.find_one("Step", rig_pipeline_step_filter)
    # Create Rig task
    rig_task_data = {
        "content": "Rig",
        "step": rig_pipeline_step,
        "task_template": asset_task_template,
    }
    sg.create("Task", rig_task_data)

    # Create a new shot
    shot_data = {
        "project": new_project,
        "sg_sequence": new_sequence,
        "code": "shot_001",
        "description": "This shot was created by the File Open UI automation",
        "sg_status_list": "ip",
        "task_template": shot_task_template,
    }
    sg.create("Shot", shot_data)

    # Create a new asset
    asset_data = {
        "project": new_project,
        "code": "AssetAutomation",
        "description": "This asset was created by the File Open UI automation",
        "sg_status_list": "ip",
        "sg_asset_type": "Character",
        "task_template": asset_task_template,
    }
    asset = sg.create("Asset", asset_data)

    # Get the publish_file_type id to be passed in the publish creation
    published_file_type_filters = [["code", "is", "Image"]]
    published_file_type = sg.find_one("PublishedFileType", published_file_type_filters)

    # File to publish
    file_to_publish = os.path.join(
        os.path.expandvars("${TK_TEST_FIXTURES}"), "files", "images", "sven.png"
    )

    # Create a published file
    publish_data = {
        "project": new_project,
        "code": "sven.png",
        "name": "sven.png",
        "description": "This file was published by the File Open UI automation",
        "published_file_type": published_file_type,
        "path": {"local_path": file_to_publish},
        "entity": asset,
        "version_number": 1,
    }
    sg.create("PublishedFile", publish_data)

    return new_project


# This fixture will launch tk-run-app on first usage
# and will remain valid until the test run ends.
@pytest.fixture(scope="session")
def host_application(context):
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
            context["type"],
            "--context-entity-id",
            str(context["id"]),
            "--commands",
            "file_open",
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


@pytest.fixture(scope="session")
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
            wait = time.time()
            while wait + 5 > time.time():
                # Close Welcome page if it is the first time the File Open app is run
                if app_dialog.root.floatingwindows["Toolkit Help"].exists():
                    app_dialog.root.floatingwindows["Toolkit Help"].buttons[
                        "Close"
                    ].mouseClick()
                    break
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


def test_ui_validation(app_dialog, context):
    # Make Sure the File Open dialog is showing up in the right context
    assert app_dialog.root.captions["File Open"].exists(), "Not the File Open dialog"
    assert app_dialog.root.captions[
        "*Project " + context["name"]
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
    assert app_dialog.root.textfields[
        0
    ].exists(), "Search All Files text field is missing"
    assert app_dialog.root.textfields[
        1
    ].exists(), "Search My Tasks text field is missing"

    # Make sure all checkboxes are showing up
    assert app_dialog.root.checkboxes[
        "All Versions"
    ].exists(), "All Versions checkbox is missing"


def test_assets_tab(app_dialog):
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
    assert app_dialog.root.textfields[1].exists(), "Search Assets text field is missing"

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
    app_dialog.root.textfields[0].typeIn("Rig" "{ENTER}")
    assert app_dialog.root.cells[
        "Rig - Rig"
    ].exists(), "Rig task should be visible in content dialog"
    assert (
        app_dialog.root.cells["Model - Model"].exists() is False
    ), "Model task shouldn't be visible in content dialog"

    # Remove test in the search field and make sure Modal task is back
    app_dialog.root.textfields[0].buttons.mouseClick()
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
    assert app_dialog.root.textfields[1].exists(), "Search Shots text field is missing"

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
    app_dialog.root.textfields[1].typeIn("Light" "{ENTER}")
    assert app_dialog.root.outlineitems[
        "Light"
    ].exists(), "Light task should be visible"
    assert (
        app_dialog.root.outlineitems["Comp"].exists() is False
    ), "Comp task shouldn't be visible"
