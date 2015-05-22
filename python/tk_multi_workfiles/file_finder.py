# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import time
from datetime import datetime
from itertools import chain
import threading
import traceback
import copy

import sgtk
from sgtk.platform.qt import QtCore
from tank_vendor.shotgun_api3 import sg_timezone
from sgtk import TankError

from .file_item import FileItem
from .users import g_user_cache

from .sg_published_files_model import SgPublishedFilesModel
from .runnable_task import RunnableTask
from .environment_details import EnvironmentDetails

class FileFinder(QtCore.QObject):
    """
    Helper class to find work and publish files for a specified context and set of templates
    """
    class _FileNameMap(object):
        """
        """
        def __init__(self):
            """
            """
            self._name_map = {}
            self._lock = threading.Lock()
            
        def get_name(self, file_key, path, template, fields=None):
            """
            """
            self._lock.acquire()
            try:
                name = None
                if file_key in self._name_map:
                    name = self._name_map.get(file_key)
                else:
                    # generate the name:
                    name = self._generate_name(path, template, fields)
                    # and add it to the map:
                    self._name_map[file_key] = name
                return name
            finally:
                self._lock.release()
            
        def _generate_name(self, path, template, fields=None):
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
    
    search_failed = QtCore.Signal(object, object) # search_id, message
    files_found = QtCore.Signal(object, object, object) # search_id, file list, EnvironmentDetails
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtCore.QObject.__init__(self, parent)
        self.__app = sgtk.platform.current_bundle()
        self._searches = {}
        self._task_id_map = {}
     
    def begin_search(self, entity, force=False):
        """
        [publishes from Shotgun] ->  
                [find_templates] -> [build publishes list] ->
                                 -> [find work files]      -> [aggregate files]        
        """
        app = sgtk.platform.current_bundle()
        
        # name map to ensure unique names for all files with the same key!
        name_map = FileFinder._FileNameMap()
        
        # build task chain for search:
        construct_environment_task = RunnableTask(self._task_construct_environment, 
                                                  entity=entity)
        
        # tasks needed to find and filter publishes:
        find_publishes_task = RunnableTask(self._task_find_publishes,
                                           upstream_tasks = [construct_environment_task], 
                                           force = force)
        filter_publishes_task = RunnableTask(self._task_filter_publishes, 
                                             upstream_tasks = [construct_environment_task, find_publishes_task])
        build_publish_items_task = RunnableTask(self._task_build_publish_items, 
                                             upstream_tasks = [construct_environment_task, filter_publishes_task],
                                             name_map = name_map)

        # tasks required to find and filter work files:
        find_work_files_task = RunnableTask(self._task_find_work_files, 
                                            upstream_tasks = [construct_environment_task])
        filter_work_files_task = RunnableTask(self._task_filter_work_files,
                                              upstream_tasks = [construct_environment_task, find_work_files_task])
        build_work_items_task = RunnableTask(self._task_build_work_items, 
                                             upstream_tasks = [construct_environment_task, filter_work_files_task],
                                             name_map = name_map)        
        
        # final aggregate task to ensure that all files are aggregated correctly:
        aggregate_files_task = RunnableTask(self._task_aggregate_files,
                                    upstream_tasks = [construct_environment_task, build_work_items_task, build_publish_items_task])
        
        self._task_id_map[build_publish_items_task.id] = aggregate_files_task.id
        self._task_id_map[build_work_items_task.id] = aggregate_files_task.id 
        
        # we care about when the search finds either work files or publishes (or both):
        # ...
        #build_work_items_task.completed.connect(self._on_search_files_found)
        #build_publish_items_task.completed.connect(self._on_search_files_found)
        
        # we only care about when the final task completes or fails:
        aggregate_files_task.completed.connect(self._on_search_completed)
        aggregate_files_task.failed.connect(self._on_search_failed)
        
        # keep track of the search:
        self._searches[aggregate_files_task.id] = aggregate_files_task
        
        #print "----------------------------------------------"
        #print "----------------------------------------------"
        #print "Beginning search [%s] for ctx entity '%s' with filters: %s" % (aggregate_files_task.id, context_entity, publish_filters)
        
        # start the first tasks:
        aggregate_files_task.start()

        return aggregate_files_task.id

    def stop_search(self, search_id):
        """
        """
        search_task = self._searches.get(search_id)
        if search_task:
            #search_task.completed.disconnect(self._on_search_completed)
            #search_task.failed.disconnect(self._on_search_failed)
            search_task.stop()
            del (self._searches[search_id])
    
    def stop_all_searches(self):
        """
        """
        for id in self._searches.keys():
            self.stop_search(id)
    
    def _on_search_failed(self, task, msg, stack_trace):
        """
        """
        # clean up search intermediate data:
        self.stop_search(task.id)
        
        # emit signal:
        self.search_failed.emit(task.id, "%s, %s" % (msg, stack_trace))
        
    def _on_search_completed(self, task, result):
        """
        """
        # clean up search intermediate data:
        self.stop_search(task.id)
        
        # emit signal:
        self.files_found.emit(task.id, result.get("files", []), result.get("environment"))
        
    def _on_search_files_found(self, task, result):
        """
        """
        search_id = self._task_id_map.get(task.id)
        if search_id == None:
            return
        
        # emit signal:
        file_items = result.get("work_items") or result.get("publish_items", {})
        
        self.files_found.emit(search_id, file_items.values(), result.get("environment"))
        
    ################################################################################################
    ################################################################################################
    
    def _task_construct_environment(self, entity, **kwargs):
        """
        """
        app = sgtk.platform.current_bundle()
        env_details = None
        if entity:
            # build a context from the search details:
            context = app.sgtk.context_from_entity_dictionary(entity)

            # build the environment details instance for this context:
            env_details = EnvironmentDetails(context)

        return {"environment":env_details}
    
    def _task_find_publishes(self, environment, force, **kwargs):
        """
        """
        sg_publishes = []
        if environment and environment.context:
            publish_filters = []
            if environment.context.entity:
                publish_filters.append(["entity", "is", environment.context.entity])
            if environment.context.task:
                publish_filters.append(["task", "is", environment.context.task])
            elif environment.context.step:
                publish_filters.append(["task.Task.step", "is", environment.context.step])

            sg_publishes = self._find_publishes(publish_filters, force)
            
        return {"sg_publishes":sg_publishes}
    
    def _task_filter_publishes(self, sg_publishes, environment, **kwargs):
        """
        """
        filtered_publishes = []
        if sg_publishes and environment and environment.publish_template:
            filtered_publishes = self._filter_publishes(sg_publishes, 
                                                        environment.publish_template, 
                                                        environment.valid_file_extensions)
        return {"sg_publishes":filtered_publishes}    
    
    def _task_build_publish_items(self, sg_publishes, environment, name_map, **kwargs):
        """
        """
        publish_items = []
        if (sg_publishes and environment and environment.publish_template 
            and environment.work_template and environment.context and name_map):
            publish_items = self._build_publish_files(sg_publishes, 
                                                      environment.publish_template, 
                                                      environment.work_template, 
                                                      environment.context,
                                                      name_map,
                                                      environment.version_compare_ignore_fields)
        return {"publish_items":publish_items, "environment":environment}
    
    def _task_find_work_files(self, environment, **kwargs):
        """
        """
        work_files = []
        if environment and environment.context and environment.work_template:
            work_files = self._find_work_files(environment.context, environment.work_template, 
                                               environment.version_compare_ignore_fields)
        return {"work_files":work_files}

    def _task_filter_work_files(self, work_files, environment, **kwargs):
        """
        """
        filtered_work_files = []
        if work_files:
            filtered_work_files = self._filter_work_files(work_files, environment.valid_file_extensions)
        return {"work_files":filtered_work_files}

    def _task_build_work_items(self, work_files, environment, name_map, **kwargs):
        """
        """
        work_items = []
        if (work_files and environment and environment.work_template 
            and environment.context and name_map):
            work_items = self._build_work_files(work_files, 
                                                environment.work_template, 
                                                environment.context,
                                                name_map,
                                                environment.version_compare_ignore_fields)
        return {"work_items":work_items, "environment":environment}

    def _task_aggregate_files(self, publish_items, work_items, environment, **kwargs):
        """
        """
        publish_items = publish_items or {}
        work_items = work_items or {}
        
        file_items = list(work_items.values())
        for file_key_and_version, publish in publish_items.iteritems():
            work_file = work_items.get(file_key_and_version)
            if not work_file:
                file_items.append(publish)
                continue
            else:
                # merge with work file:
                work_file.update(is_published=True, publish_path=publish.publish_path, details=publish.details)
        
        #files = [] 
        #if sg_publishes or work_files:
        #    files = self._aggregate_files(work_files, work_template, sg_publishes, publish_template, context) 
        return {"files":file_items, "environment":environment}

    ################################################################################################
    ################################################################################################

    def find_files(self, work_template, publish_template, context, filter_file_key=None):
        """
        Find files using the specified context, work and publish templates
        
        :param work_template:       The template to use when searching for work files
        :param publish_template:    The template to use when searching for publish files
        :param context:             The context to search for file with
        :param filter_file_key:     A unique file 'key' that if specified will limit the returned list of files to just 
                                    those that match.  This 'key' should be generated using the FileItem.build_file_key()
                                    method.
        :returns:                   A list of FileItem instances, one for each unique version of a file found in either 
                                    the work or publish areas
        """
        # can't find anything without a work template!
        if not work_template:
            return []
    
        # determien the publish filters to use from the context:
        publish_filters = [["entity", "is", context.entity or context.project]]
        if context.task:
            publish_filters.append(["task", "is", context.task])
        else:
            publish_filters.append(["task", "is", None])
    
        # get the list of valid file extensions if set:
        valid_file_extensions = [".%s" % ext if not ext.startswith(".") else ext 
                                 for ext in self.__app.get_setting("file_extensions", [])]
        
        # get list of fields that should be ignored when comparing work files:
        version_compare_ignore_fields = self.__app.get_setting("version_compare_ignore_fields", [])    
    
        # find all work & publish files and filter out any that should be ignored:
        work_files = self._find_work_files(context, work_template, version_compare_ignore_fields)
        filtered_work_files = self._filter_work_files(work_files, valid_file_extensions)
        
        published_files = self._find_publishes(publish_filters)
        filtered_published_files = self._filter_publishes(published_files, 
                                                          publish_template, 
                                                          valid_file_extensions)
        
        # turn these into FileItem instances:
        name_map = FileFinder._FileNameMap()
        work_file_items = self._build_work_files(filtered_work_files, 
                                                 work_template, 
                                                 context, 
                                                 name_map, 
                                                 version_compare_ignore_fields, 
                                                 filter_file_key)
        publish_items = self._build_publish_files(filtered_published_files, 
                                                  publish_template, 
                                                  work_template, 
                                                  context, 
                                                  name_map, 
                                                  version_compare_ignore_fields,
                                                  filter_file_key)
        
        # and aggregate the results:
        file_items = list(work_file_items.values())
        for file_key_and_version, publish in publish_items.iteritems():
            work_file = work_file_items.get(file_key_and_version)
            if not work_file:
                file_items.append(publish)
                continue
            
            # merge with work file:
            work_file.update(is_published=True, publish_path=publish.publish_path, details=publish.details)
        
        return file_items
        ## return the aggregated list of all files:
        #return self._aggregate_files(work_files, work_template, published_files, publish_template, context, filter_file_key)

        

    def _build_work_files(self, work_files, work_template, context, name_map, version_compare_ignore_fields, 
                          filter_file_key=None):
        """
        """
        files = {}
        
        for work_file in work_files:
            
            # always have the work path:
            work_path = work_file["path"]
            
            # get fields for work file:
            wf_fields = work_template.get_fields(work_path)
            
            # build the unique file key for the work path.  All files that share the same key are considered
            # to be different versions of the same file.
            #
            file_key = FileItem.build_file_key(wf_fields, work_template, 
                                               version_compare_ignore_fields)
            if filter_file_key and file_key != filter_file_key:
                # we can ignore this file completely!
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
                # TODO - user cache probably isn't thread safe!
                file_details["modified_by"] = g_user_cache.get_file_last_modified_user(work_path)
            
            # make sure all files with the same key have the same name:
            file_details["name"] = name_map.get_name(file_key, work_path, work_template, wf_fields)

            # add new file item
            file_item = FileItem(work_path, None, True, False, file_details, file_key)
            files[(file_key, file_details["version"])] = file_item
                
        return files
        
    def _build_publish_files(self, sg_publishes, publish_template, work_template, context, name_map, 
                             version_compare_ignore_fields, filter_file_key=None):
        """
        """
        files = {}
        
        # and add in publish details:
        ctx_fields = context.as_template_fields(work_template)
                    
        for sg_publish in sg_publishes:
            file_details = {}
    
            # always have a path:
            publish_path = sg_publish["path"]
            
            # determine the work path fields from the publish fields + ctx fields:
            # The order is important as it ensures that the user is correct if the 
            # publish file is in a user sandbox but we also need to be careful not
            # to overrwrite fields that are being ignored when comparing work files
            publish_fields = publish_template.get_fields(publish_path)
            wp_fields = publish_fields.copy()
            for k, v in ctx_fields.iteritems():
                if k not in version_compare_ignore_fields:
                    wp_fields[k] = v
            
            # build the unique file key for the publish path.  All files that share the same key are considered
            # to be different versions of the same file.
            file_key = FileItem.build_file_key(wp_fields, work_template, 
                                               version_compare_ignore_fields)
            if filter_file_key and file_key != filter_file_key:
                # we can ignore this file completely!
                continue

            # resolve the work path:
            work_path = work_template.apply_fields(wp_fields)
            
            # copy common fields from sg_publish:
            #
            file_details = dict([(k, v) for k, v in sg_publish.iteritems() if k != "path"])
            
            # get version from fields if not specified in publish file:
            if file_details["version"] == None:
                file_details["version"] = publish_fields.get("version", 0)
            
            # entity
            file_details["entity"] = context.entity
        
            # local file modified details:
            if os.path.exists(publish_path):
                file_details["modified_at"] = datetime.fromtimestamp(os.path.getmtime(publish_path), tz=sg_timezone.local)
                file_details["modified_by"] = g_user_cache.get_file_last_modified_user(publish_path)
            else:
                # just use the publish info
                file_details["modified_at"] = sg_publish.get("published_at")
                file_details["modified_by"] = sg_publish.get("published_by")

            # make sure all files with the same key have the same name:
            file_details["name"] = name_map.get_name(file_key, publish_path, publish_template, publish_fields)

            # add new file item
            file_item = FileItem(work_path, publish_path, False, True, file_details, file_key)
            files[(file_key, file_details["version"])] = file_item
        return files
    
    def _find_publishes(self, publish_filters, force=True):
        """
        Find all publishes for the specified context and publish template
        
        :param context:             The context to find publishes for
        :returns:                   List of dictionaries, each one containing the details
                                    of an individual published file
        """
        model = SgPublishedFilesModel(self)
        # start the process of finding publishes in Shotgun:
        fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]
        loaded_data = model.load_data(filters = publish_filters, fields = fields)
        if not loaded_data or force:
            # refresh data from Shotgun:
            model.refresh()
        
        sg_publishes = model.get_sg_data()
        
        # convert created_at unix time stamp to shotgun std time stamp for all publishes
        for sg_publish in sg_publishes:
            created_at = sg_publish.get("created_at")
            if created_at:
                created_at = datetime.fromtimestamp(created_at, sg_timezone.LocalTimezone())
                sg_publish["created_at"] = created_at

        return sg_publishes
    
    def _filter_publishes(self, sg_publishes, publish_template, valid_file_extensions):
        """
        """
        # build list of publishes to send to the filter_publishes hook:
        hook_publishes = [{"sg_publish":sg_publish} for sg_publish in sg_publishes]
        
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
            
            # skip file if it doesn't contain a valid file extension:
            if valid_file_extensions and os.path.splitext(path)[1] not in valid_file_extensions:
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
    
        
    def _find_work_files(self, context, work_template, version_compare_ignore_fields):
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
            work_fields = context.as_template_fields(work_template, error_on_missing_fields=True)
        except TankError:
            # could not resolve fields from this context. This typically happens
            # when the context object does not have any corresponding objects on 
            # disk / in the path cache. In this case, we cannot continue with any
            # file system resolution, so just exit early insted.
            return []

        # build list of fields to ignore when looking for files:
        skip_fields = list(version_compare_ignore_fields)

        # Skip any keys from work_fields that are _only_ optional in the template.  This is to
        # ensure we find as wide a range of files as possible considering all optional keys.
        # Note, this may be better as a general change to the paths_from_template method...
        skip_fields += [n for n in work_fields.keys() if work_template.is_optional(n)]
        
        # Find all versions so skip the 'version' key if it's present:
        skip_fields += ["version"]

        # find paths:        
        work_file_paths = self.__app.sgtk.paths_from_template(work_template, 
                                                              work_fields, 
                                                              skip_fields, 
                                                              skip_missing_optional_keys=True)

        # paths_from_template may have returned additional files that we don't want (aren't valid within this
        # work area) if any of the fields were populated by the context.  Filter the list to remove these
        # extra files.
        filtered_paths = []
        for p in work_file_paths:
            # (AD) TODO - this should be optimized as it's doing 'get_fields' again 
            # when this method returns!
            fields = work_template.get_fields(p)
            is_match = True
            for wfn, wfv in work_fields.iteritems():
                if wfn in fields:
                    if fields[wfn] != wfv:
                        is_match = False
                        break
                elif wfn not in skip_fields:
                    is_match = False
                    break
            if is_match:
                filtered_paths.append(p)
        work_file_paths = filtered_paths
        
        return work_file_paths
        
    def _filter_work_files(self, work_file_paths, valid_file_extensions):
        """
        """
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
            
            if valid_file_extensions and os.path.splitext(path)[1] not in valid_file_extensions:
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
        
    #def __get_file_display_name(self, path, template, fields=None):
    #    """
    #    Return the 'name' to be used for the file - if possible
    #    this will return a 'versionless' name
    #    """
    #    # first, extract the fields from the path using the template:
    #    fields = fields.copy() if fields else template.get_fields(path)
    #    if "name" in fields and fields["name"]:
    #        # well, that was easy!
    #        name = fields["name"]
    #    else:
    #        # find out if version is used in the file name:
    #        template_name, _ = os.path.splitext(os.path.basename(template.definition))
    #        version_in_name = "{version}" in template_name
    #    
    #        # extract the file name from the path:
    #        name, _ = os.path.splitext(os.path.basename(path))
    #        delims_str = "_-. "
    #        if version_in_name:
    #            # looks like version is part of the file name so we        
    #            # need to isolate it so that we can remove it safely.  
    #            # First, find a dummy version whose string representation
    #            # doesn't exist in the name string
    #            version_key = template.keys["version"]
    #            dummy_version = 9876
    #            while True:
    #                test_str = version_key.str_from_value(dummy_version)
    #                if test_str not in name:
    #                    break
    #                dummy_version += 1
    #            
    #            # now use this dummy version and rebuild the path
    #            fields["version"] = dummy_version
    #            path = template.apply_fields(fields)
    #            name, _ = os.path.splitext(os.path.basename(path))
    #            
    #            # we can now locate the version in the name and remove it
    #            dummy_version_str = version_key.str_from_value(dummy_version)
    #            
    #            v_pos = name.find(dummy_version_str)
    #            # remove any preceeding 'v'
    #            pre_v_str = name[:v_pos].rstrip("v")
    #            post_v_str = name[v_pos + len(dummy_version_str):]
    #            
    #            if (pre_v_str and post_v_str 
    #                and pre_v_str[-1] in delims_str 
    #                and post_v_str[0] in delims_str):
    #                # only want one delimiter - strip the second one:
    #                post_v_str = post_v_str.lstrip(delims_str)
    #
    #            versionless_name = pre_v_str + post_v_str
    #            versionless_name = versionless_name.strip(delims_str)
    #            
    #            if versionless_name:
    #                # great - lets use this!
    #                name = versionless_name
    #            else: 
    #                # likely that version is only thing in the name so 
    #                # instead, replace the dummy version with #'s:
    #                zero_version_str = version_key.str_from_value(0)        
    #                new_version_str = "#" * len(zero_version_str)
    #                name = name.replace(dummy_version_str, new_version_str)
    #    
    #    return name 
















