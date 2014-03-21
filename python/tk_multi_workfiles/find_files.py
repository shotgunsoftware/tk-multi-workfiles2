# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

def find_all_files(app, work_template, publish_template, context):
    """
    Find all work files and publishes for the specified context 
    and templates.
    
    This will return a dictionary containing all versions of all 
    files found.
    """
    publishes = __find_publishes(app, context, publish_template)
    work_files = __find_work_files(app, context, work_template)
    return {"publish":publishes, "work":work_files}

def __find_publishes(app, context, publish_template):
    """
    Find all publishes for the specified context and publish template
    """
    # get list of published files for the context from Shotgun:
    sg_filters = [["entity", "is", context.entity or context.project]]
    if context.task:
        sg_filters.append(["task", "is", context.task])
    published_file_entity_type = sgtk.util.get_published_file_entity_type(app.sgtk)
    sg_fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]
    sg_res = app.shotgun.find(published_file_entity_type, sg_filters, sg_fields)

    # build list of publishes to send to the filter_publishes hook:
    hook_publishes = [{"sg_publish":sg_publish} for sg_publish in sg_res]
    
    # execute the hook - this will return a list of filtered publishes:
    hook_result = app.execute_hook("hook_filter_publishes", publishes = hook_publishes)
    if not isinstance(hook_result, list):
        app.log_error("hook_filter_publishes returned an unexpected result type '%s' - ignoring!" 
                      % type(hook_result).__name__)
        hook_result = []
    
    # split back out publishes:
    published_files = []
    for item in hook_result:
        sg_publish = item.get("sg_publish")
        if not sg_publish:
            continue
        
        # all publishes should have a local path:
        path = sg_publish.get("path", {}).get("local_path")
        if not path:
            continue

        # make sure path matches the publish template:            
        if not publish_template.validate(path):
            continue

        # build file details for this publish:
        file_details = {"path":path}
        
        # add in details from sg record:
        file_details["version"] = sg_publish.get("version_number")
        file_details["name"] = sg_publish.get("name")
        file_details["task"] = sg_publish.get("task")
        file_details["publish_description"] = sg_publish.get("description")
        file_details["thumbnail"] = sg_publish.get("image")
        
        file_details["published_at"] = sg_publish.get("created_at")
        file_details["published_by"] = sg_publish.get("created_by", {})
        file_details["published_file_entity_id"] = sg_publish.get("id")
        
        # find additional information:
        editable_info = item.get("editable")
        if editable_info and isinstance(editable_info, dict):
            file_details["editable"] = editable_info.get("can_edit", True)
            file_details["editable_reason"] = editable_info.get("reason", "")
        
        # append to published files list:
        published_files.append(file_details)    
        
    return published_files

    
def __find_work_files(app, context, work_template):
    """
    Find all work files for the specified context and work template
    """
    # find work files that match the current work template:
    work_fields = []
    try:
        work_fields = context.as_template_fields(work_template)
    except TankError:
        # could not resolve fields from this context. This typically happens
        # when the context object does not have any corresponding objects on 
        # disk / in the path cache. In this case, we cannot continue with any
        # file system resolution, so just exit early insted.
        return []
    
    # find all versions so skip the 'version' key if it's present:
    work_file_paths = app.sgtk.paths_from_template(work_template, work_fields, ["version"], 
                                                         skip_missing_optional_keys=True)
    
    # build list of work files to send to the filter_work_files hook:
    hook_work_files = [{"work_file":{"path":path}} for path in work_file_paths]
    
    # execute the hook - this will return a list of filtered publishes:
    hook_result = app.execute_hook("hook_filter_work_files", work_files = hook_work_files)
    if not isinstance(hook_result, list):
        app.log_error("hook_filter_work_files returned an unexpected result type '%s' - ignoring!" 
                      % type(hook_result).__name__)
        hook_result = []

    # split back out work files:
    work_files = []
    for item in hook_result:
        work_file = item.get("work_file")
        if not work_file:
            continue
        
        path = work_file.get("path")
        if not path:
            continue
        
        file_details = {"path":path}
        file_details["version"] = work_file.get("version_number")
        if not file_details["version"]:
            wf_fields = work_template.get_fields(path)
            file_details["version"] = wf_fields.get("version", 0)
        
        file_details["name"] = work_file.get("name")
        file_details["task"] = work_file.get("task")
        file_details["description"] = work_file.get("description")
        file_details["thumbnail"] = work_file.get("thumbnail")
        file_details["modified_at"] = work_file.get("modified_at")
        file_details["modified_by"] = work_file.get("modified_by", {})
        
        # find additional information:
        editable_info = item.get("editable")
        if editable_info and isinstance(editable_info, dict):
            file_details["editable"] = editable_info.get("can_edit", True)
            file_details["editable_reason"] = editable_info.get("reason", "")        
        
        work_files.append(file_details)
        
        
    return work_files
        




















