# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
from datetime import datetime
from itertools import chain

import sgtk
from tank_vendor.shotgun_api3 import sg_timezone
from sgtk import TankError

from .file_item import FileItem
from .users import UserCache

class FileFinder(object):
    """
    Helper class to find work and publish files for a specified context and set of templates
    """
    def __init__(self, app, user_cache=None):
        """
        Construction
        
        :param app:           The Workfiles app instance
        :param user_cache:    An UserCache instance used to retrieve Shotgun user information
        """
        self.__app = app
        self.__user_cache = user_cache or UserCache(app)
        # cache the valid file extensions that can be found
        self.__visible_file_extensions = [".%s" % ext if not ext.startswith(".") else ext 
                                          for ext in self.__app.get_setting("file_extensions", [])]

    def find_files(self, work_template, publish_template, context, filter_file_key=None):
        """
        Find files using the specified context, work and publish templates
        
        :param work_template:       The template to use when searching for work files
        :param publish_template:    The template to use when searching for publish files
        :param context:             The context to search for file with
        :param filter_file_key:     A '0' version work file path 'key' that if specified will limit the returned
                                    list of files to just those that match
        :returns:                   A list of FileItem instances, one for each unique version of a file found in either 
                                    the work or publish areas
        """
        # can't find anything without a work template!
        if not work_template:
            return []
    
        # find all work & publish files and filter out any that should be ignored:
        work_files = self.__find_work_files(context, work_template)
        work_files = [wf for wf in work_files if not self.__ignore_file_path(wf["path"])]
        
        published_files = self.__find_publishes(context, publish_template)
        published_files = [pf for pf in published_files if not self.__ignore_file_path(pf["path"])]
                
        # now amalgamate the two lists together:
        files = {}
        key_to_name_map = {}
        
        # first, process work files:
        for work_file in work_files:
            
            # always have the work path:
            work_path = work_file["path"]
            
            # get fields for work file:
            wf_fields = work_template.get_fields(work_path)
            
            # build unique key for work path (versionless work-file path):
            #
            key_fields = wf_fields.copy()
            key_fields["version"] = 0            
            file_key = work_template.apply_fields(key_fields)    
            
            if filter_file_key and file_key != filter_file_key:
                continue
            
            # copy common fields from work_file:
            #
            file_details = dict([(k, v) for k, v in work_file.iteritems() if k != "path"])
            
            # get version from fields if not specified in work file:
            if not file_details["version"]:
                file_details["version"] = wf_fields.get("version", 0)
            
            # if no task try to determine from context or path:
            if not file_details["task"]:
                if context.task:
                    file_details["task"] = context.task
                else:
                    # try to create a context from the path and see if that contains a task:
                    wf_ctx = self.__app.sgtk.context_from_path(work_path, context)
                    if wf_ctx and wf_ctx.task:
                        file_details["task"] = wf_ctx.task 
            
            # add additional fields:
            #
    
            # entity:
            file_details["entity"] = context.entity
            
            # file modified details:
            if not file_details["modified_at"]:
                file_details["modified_at"] = datetime.fromtimestamp(os.path.getmtime(work_path), tz=sg_timezone.local)
            if not file_details["modified_by"]:                
                file_details["modified_by"] = self.__user_cache.get_file_last_modified_user(work_path)
            
            # make sure all files with the same key have the same name:
            update_name_map = True
            if file_key in key_to_name_map:
                # always use the same name
                update_name_map = False
                file_details["name"] = key_to_name_map[file_key]
            elif not file_details["name"]:
                # ensure we have a name:
                file_details["name"] = self.__get_file_display_name(work_path, work_template, wf_fields)
                
            # add new file item
            file_item = FileItem(work_path, None, True, False, file_details, file_key)
            files[(file_key, file_details["version"])] = file_item
    
            if update_name_map:
                # update name map with name:
                key_to_name_map[file_key] = file_item.name
    
        # and add in publish details:
        ctx_fields = context.as_template_fields(work_template)
                    
        for published_file in published_files:
            file_details = {}
    
            # always have a path:
            publish_path = published_file["path"]
            
            # determine the work path fields from the publish fields + ctx fields:
            # The order is important as it ensures that the user is correct if the 
            # publish file is in a user sandbox.
            publish_fields = publish_template.get_fields(publish_path)
            wp_fields = dict(chain(publish_fields.iteritems(), ctx_fields.iteritems()))
            
            # build unique key for publish path (versionless work-file path):
            key_fields = wp_fields.copy()
            key_fields["version"] = 0            
            file_key = work_template.apply_fields(key_fields)
            if filter_file_key and file_key != filter_file_key:
                continue

            # resolve the work path:
            work_path = work_template.apply_fields(wp_fields)
            
            # copy common fields from published_file:
            #
            file_details = dict([(k, v) for k, v in published_file.iteritems() if k != "path"])
            
            # get version from fields if not specified in publish file:
            if file_details["version"] == None:
                file_details["version"] = publish_fields.get("version", 0)
            
            # look to see if we have a matching work file for this published file
            have_work_file = False
            existing_file_item = files.get((file_key, file_details["version"]))
            if existing_file_item and existing_file_item.is_local:
                # we do so check the paths match:                
                if existing_file_item.path != work_path:
                    raise TankError("Work file mismatch when finding files!")
                
                # and copy the work file details - giving precedence to the published details:
                file_details = dict([(k,v) 
                                     for k, v in chain(existing_file_item.details.iteritems(), file_details.iteritems()) 
                                        if v != None])
    
                have_work_file = True
            else:
                # no work file so just use publish details:                
                
                # entity
                file_details["entity"] = context.entity
            
                # local file modified details:
                if os.path.exists(publish_path):
                    file_details["modified_at"] = datetime.fromtimestamp(os.path.getmtime(publish_path), tz=sg_timezone.local)
                    file_details["modified_by"] = self.__user_cache.get_file_last_modified_user(publish_path)
                else:
                    # just use the publish info
                    file_details["modified_at"] = published_file.get("published_at")
                    file_details["modified_by"] = published_file.get("published_by")
    
            # make sure all files with the same key have the same name:
            update_name_map = True
            if file_key in key_to_name_map:
                # always use the same name
                update_name_map = False
                file_details["name"] = key_to_name_map[file_key]
            elif not file_details["name"]:
                # ensure we have a name:
                file_details["name"] = self.__get_file_display_name(publish_path, publish_template, publish_fields)
                    
            # add new file item
            file_item = FileItem(work_path, publish_path, have_work_file, True, file_details, file_key)
            files[(file_key, file_details["version"])] = file_item
    
            if update_name_map:
                # update name map with name:
                key_to_name_map[file_key] = file_item.name
                
        # return list of FileItems
        return files.values()
    
    def __find_publishes(self, context, publish_template):
        """
        Find all publishes for the specified context and publish template
        
        :param context:             The context to find publishes for
        :param publish_template:    The publish template to match found publishes against
        :returns:                   List of dictionaries, each one containing the details
                                    of an individual published file
        """
        # get list of published files for the context from Shotgun:
        sg_filters = [["entity", "is", context.entity or context.project]]
        if context.task:
            sg_filters.append(["task", "is", context.task])
        published_file_entity_type = sgtk.util.get_published_file_entity_type(self.__app.sgtk)
        sg_fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]
        sg_res = self.__app.shotgun.find(published_file_entity_type, sg_filters, sg_fields)
    
        # build list of publishes to send to the filter_publishes hook:
        hook_publishes = [{"sg_publish":sg_publish} for sg_publish in sg_res]
        
        # execute the hook - this will return a list of filtered publishes:
        hook_result = self.__app.execute_hook("hook_filter_publishes", publishes = hook_publishes)
        if not isinstance(hook_result, list):
            self.__app.log_error("hook_filter_publishes returned an unexpected result type '%s' - ignoring!" 
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
    
        
    def __find_work_files(self, context, work_template):
        """
        Find all work files for the specified context and work template
        
        :param context:             The context to find work files for
        :param publish_template:    The work template to match found files against
        :returns:                   List of dictionaries, each one containing the details
                                    of an individual work file        
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
        work_file_paths = self.__app.sgtk.paths_from_template(work_template, work_fields, ["version"], 
                                                             skip_missing_optional_keys=True)
        
        # build list of work files to send to the filter_work_files hook:
        hook_work_files = [{"work_file":{"path":path}} for path in work_file_paths]
        
        # execute the hook - this will return a list of filtered publishes:
        hook_result = self.__app.execute_hook("hook_filter_work_files", work_files = hook_work_files)
        if not isinstance(hook_result, list):
            self.__app.log_error("hook_filter_work_files returned an unexpected result type '%s' - ignoring!" 
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
        
    def __ignore_file_path(self, path):
        """
        Determine if this file should be ignored when finding files
        
        :param path:    Path to check
        :returns:       True if the path should be ignored.
        """
        if self.__visible_file_extensions:
            _, ext = os.path.splitext(path)
            if ext and ext not in self.__visible_file_extensions:
                # we want to ignore this file!
                return True
            
        return False

    def __get_file_display_name(self, path, template, fields=None):
        """
        Return the 'name' to be used for the file - if possible
        this will return a 'versionless' name
        """
        # first, extract the fields from the path using the template:
        fields = fields.copy() if fields else template.get_fields(path)
        if "name" in fields and fields["name"]:
            # well, that was easy!
            name = fields["name"]
        else:
            # find out if version is used in the file name:
            template_name, _ = os.path.splitext(os.path.basename(template.definition))
            version_in_name = "{version}" in template_name
        
            # extract the file name from the path:
            name, _ = os.path.splitext(os.path.basename(path))
            delims_str = "_-. "
            if version_in_name:
                # looks like version is part of the file name so we        
                # need to isolate it so that we can remove it safely.  
                # First, find a dummy version whose string representation
                # doesn't exist in the name string
                version_key = template.keys["version"]
                dummy_version = 9876
                while True:
                    test_str = version_key.str_from_value(dummy_version)
                    if test_str not in name:
                        break
                    dummy_version += 1
                
                # now use this dummy version and rebuild the path
                fields["version"] = dummy_version
                path = template.apply_fields(fields)
                name, _ = os.path.splitext(os.path.basename(path))
                
                # we can now locate the version in the name and remove it
                dummy_version_str = version_key.str_from_value(dummy_version)
                
                v_pos = name.find(dummy_version_str)
                # remove any preceeding 'v'
                pre_v_str = name[:v_pos].rstrip("v")
                post_v_str = name[v_pos + len(dummy_version_str):]
                
                if (pre_v_str and post_v_str 
                    and pre_v_str[-1] in delims_str 
                    and post_v_str[0] in delims_str):
                    # only want one delimiter - strip the second one:
                    post_v_str = post_v_str.lstrip(delims_str)

                versionless_name = pre_v_str + post_v_str
                versionless_name = versionless_name.strip(delims_str)
                
                if versionless_name:
                    # great - lets use this!
                    name = versionless_name
                else: 
                    # likely that version is only thing in the name so 
                    # instead, replace the dummy version with #'s:
                    zero_version_str = version_key.str_from_value(0)        
                    new_version_str = "#" * len(zero_version_str)
                    name = name.replace(dummy_version_str, new_version_str)
        
        return name 
















