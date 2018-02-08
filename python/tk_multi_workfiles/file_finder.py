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
from datetime import datetime
import copy
import time

import sgtk
from sgtk.platform.qt import QtCore
from tank_vendor.shotgun_api3 import sg_timezone
from sgtk import TankError

from .file_item import FileItem
from .user_cache import g_user_cache

from .sg_published_files_model import SgPublishedFilesModel

task_manager = sgtk.platform.import_framework("tk-framework-shotgunutils", "task_manager")
BackgroundTaskManager = task_manager.BackgroundTaskManager

from .work_area import WorkArea
from .util import monitor_qobject_lifetime, Threaded


class FileFinder(QtCore.QObject):
    """
    Helper class to find work and publish files for a specified context and set of templates
    """

    class _FileNameMap(Threaded):
        """
        """
        def __init__(self):
            """
            """
            Threaded.__init__(self)
            self._name_map = {}

        @Threaded.exclusive
        def get_name(self, file_key, path, template, fields=None):
            """
            Thread safe method to get the unique name for the specified file key
            """
            name = None
            if file_key in self._name_map:
                name = self._name_map.get(file_key)
            else:
                # generate the name:
                name = self._generate_name(path, template, fields)
                # and add it to the map:
                self._name_map[file_key] = name
            return name

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

    def __init__(self, parent=None):
        """
        Construction
        """
        QtCore.QObject.__init__(self, parent)
        self._app = sgtk.platform.current_bundle()

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
                                 for ext in self._app.get_setting("file_extensions", [])]
        
        # get list of fields that should be ignored when comparing work files:
        version_compare_ignore_fields = self._app.get_setting("version_compare_ignore_fields", [])    

        # find all work & publish files and filter out any that should be ignored:
        work_files = self._find_work_files(context, work_template, version_compare_ignore_fields)
        filtered_work_files = self._filter_work_files(work_files, valid_file_extensions)
        
        published_files = self._find_publishes(publish_filters)
        filtered_published_files = self._filter_publishes(published_files, 
                                                          publish_template, 
                                                          valid_file_extensions)
        
        # turn these into FileItem instances:
        name_map = FileFinder._FileNameMap()
        work_file_item_details = self._process_work_files(filtered_work_files, 
                                                        work_template, 
                                                        context, 
                                                        name_map, 
                                                        version_compare_ignore_fields, 
                                                        filter_file_key)
        work_file_items = dict([(k, FileItem(**kwargs)) for k, kwargs in work_file_item_details.iteritems()])

        publish_item_details = self._process_publish_files(filtered_published_files, 
                                                         publish_template, 
                                                         work_template, 
                                                         context, 
                                                         name_map, 
                                                         version_compare_ignore_fields,
                                                         filter_file_key)
        publish_items = dict([(k, FileItem(**kwargs)) for k, kwargs in publish_item_details.iteritems()])

        # and aggregate the results:
        file_items = list(work_file_items.values())
        for file_key_and_version, publish in publish_items.iteritems():
            work_file = work_file_items.get(file_key_and_version)
            if not work_file:
                file_items.append(publish)
                continue

            # merge with work file:
            work_file.update_from_publish(publish)

        return file_items

    def _process_work_files(self, work_files, work_template, context, name_map, version_compare_ignore_fields, 
                          filter_file_key=None):
        """
        :param work_files: A list of dictionaries with file details.
        :param work_template: The template which was used to generate the files list.
        :param context: The context for which the files are retrieved.
        :param name_map: A :class:`_FileNameMap` instance.
        :param version_compare_ignore_fields: A list of template fields to ignore
                                              when building a key for the file.
        :param filter_file_key: A unique file 'key' that, if specified, will limit
                                the returned list of files to just those that match.
        returns: A dictionary where keys are (file key, version number) tuples
                  and values are dictionaries which can be used to instantiate
                  :class:`FileItem`.
        """
        files = {}
        
        for work_file in work_files:
            
            # always have the work path:
            work_path = work_file["path"]
            
            # get fields for work file:
            wf_fields = work_template.get_fields(work_path)
            wf_ctx = None


            # Build the unique file key for the work path.
            # All files that share the same key are considered
            # to be different versions of the same file.
            #
            file_key = FileItem.build_file_key(
                wf_fields,
                work_template,
                version_compare_ignore_fields
            )
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
                    wf_ctx = self._app.sgtk.context_from_path(work_path, context)
                    if wf_ctx and wf_ctx.task:
                        file_details["task"] = wf_ctx.task 

            # Add additional fields:
            #
    
            # Entity:
            file_details["entity"] = context.entity

            # File modified details:
            if not file_details["modified_at"]:
                try:
                    modified_at = os.path.getmtime(work_path)
                    file_details["modified_at"] = datetime.fromtimestamp(
                        modified_at, tz=sg_timezone.local
                    )
                except OSError:
                    # ignore OSErrors as it's probably a permissions thing!
                    pass

            if not file_details["modified_by"]:
                file_details["modified_by"] = g_user_cache.get_file_last_modified_user(work_path)

            # make sure all files with the same key have the same name:
            file_details["name"] = name_map.get_name(
                file_key, work_path, work_template, wf_fields
            )

            # add to the list of files
            files[(file_key, file_details["version"])] = {
                "key": file_key,
                "is_work_file": True,
                "work_path": work_path,
                "work_details": file_details
            }
                
        return files
        
    def _process_publish_files(self, sg_publishes, publish_template, work_template, context, name_map, 
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
            work_path = ""
            try:
                work_path = work_template.apply_fields(wp_fields)
            except TankError, e:
                # unable to generate a work path - this means we are probably missing a field so it's going to
                # be a problem matching this publish up with its corresponding work file!
                work_path = ""
            
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
                try:
                    modified_at = os.path.getmtime(publish_path)
                    file_details["modified_at"] = datetime.fromtimestamp(modified_at, tz=sg_timezone.local)
                except OSError:
                    # ignore OSErrors as it's probably a permissions thing!
                    pass
                file_details["modified_by"] = g_user_cache.get_file_last_modified_user(publish_path)
            else:
                # just use the publish info
                file_details["modified_at"] = sg_publish.get("published_at")
                file_details["modified_by"] = sg_publish.get("published_by")

            # make sure all files with the same key have the same name:
            file_details["name"] = name_map.get_name(file_key, publish_path, publish_template, publish_fields)

            # add new file item for this publish.  Note that we also keep track of the
            # work path even though we don't know if this publish has a corresponding
            # work file.
            files[(file_key, file_details["version"])] = {"key":file_key, 
                                                          "work_path":work_path,
                                                          "is_published":True,
                                                          "publish_path":publish_path,
                                                          "publish_details":file_details}
        return files

    def _find_publishes(self, publish_filters):
        """
        Find all publishes for the specified context and publish template

        :returns:                   List of dictionaries, each one containing the details
                                    of an individual published file
        """
        fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]
        published_file_type = sgtk.util.get_published_file_entity_type(self._app.sgtk)
        sg_publishes = self._app.shotgun.find(
            published_file_type, publish_filters, fields
        )
        return sg_publishes

    def _filter_publishes(self, sg_publishes, publish_template, valid_file_extensions):
        """
        """
        # build list of publishes to send to the filter_publishes hook:
        hook_publishes = [{"sg_publish":sg_publish} for sg_publish in sg_publishes]
        
        # execute the hook - this will return a list of filtered publishes:
        hook_result = self._app.execute_hook("hook_filter_publishes", publishes = hook_publishes)
        if not isinstance(hook_result, list):
            self._app.log_error("hook_filter_publishes returned an unexpected result type '%s' - ignoring!" 
                          % type(hook_result).__name__)
            hook_result = []
        
        # split back out publishes:
        published_files = []
        for item in hook_result:
            sg_publish = item.get("sg_publish")
            if not sg_publish:
                continue

            # A PublishedFile entity can be created with sgtk.util.register_publish, which will
            # always set a valid path. However, it is possible to create them manually in the web
            # UI or with the Shotgun API, in which cases local_path might not be set and ["path"]
            # will contain None.
            path = (sg_publish["path"] or {}).get("local_path")
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
        Find all work files for the specified context and work template.
        
        :param context:                         The context to find work files for
        :param work_template:                   The work template to match found files against
        :param version_compare_ignore_fields:   List of fields to ignore when comparing files in order to find 
                                                different versions of the same file
        :returns:                               A list of file paths.
        """
        # find work files that match the current work template:
        work_fields = []
        try:
            work_fields = context.as_template_fields(work_template, validate=True)
        except TankError as e:
            # could not resolve fields from this context. This typically happens
            # when the context object does not have any corresponding objects on 
            # disk / in the path cache. In this case, we cannot continue with any
            # file system resolution, so just exit early insted.
            return []

        # Build list of fields to ignore when looking for files, any missing key
        # is treated as a wildcard, which allows, for example to retrieve all files
        # for any pipeline step for a given Entity.
        skip_fields = list(version_compare_ignore_fields or [])

        # Skip any keys from work_fields that are _only_ optional in the template.  This is to
        # ensure we find as wide a range of files as possible considering all optional keys.
        # Note, this may be better as a general change to the paths_from_template method...
        skip_fields += [n for n in work_fields.keys() if work_template.is_optional(n)]
        
        # Find all versions so skip the 'version' key if it's present and not
        # already registered in our wildcards:
        if "version" not in skip_fields:
            skip_fields += ["version"]

        # find paths:
        work_file_paths = self._app.sgtk.paths_from_template(
            work_template,
            work_fields,
            skip_fields,
            skip_missing_optional_keys=True
        )
        return work_file_paths

    def _filter_work_files(self, work_file_paths, valid_file_extensions):
        """
        Filter the given list of file paths by calling the `hook_filter_work_files`
        hook, and validate them against the given extensions list.

        :param work_file_paths: A list of file paths to consider.
        :param valid_file_extensions: A list of valid extensions.
        :returns: A list of dictionaries for every filtered path, with details
                  about the filtered path.
        """
        # Build list of work files to send to the filter_work_files hook.
        # TODO: the hook expects details in the dictionary but we are just
        # populationg the path value, so either the hook documentation should be
        # changed or additional details should be added here.
        hook_work_files = [
            {"work_file":{"path":path}} for path in work_file_paths
        ]
        
        # Execute the hook - this will return a list of filtered paths:
        hook_result = self._app.execute_hook(
            "hook_filter_work_files",
            work_files = hook_work_files
        )
        if not isinstance(hook_result, list):
            self._app.log_error(
                "hook_filter_work_files returned an unexpected result type '%s' - ignoring..."
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
            
            # Build the dictionary with details for the filtered path.
            # Please note that unless the hook added additional details, we only
            # have a path key in the work_file dictionary.
            file_details = {
                "path": path,
                "version": work_file.get("version_number"),
                "name": work_file.get("name"),
                "task": work_file.get("task"),
                "description": work_file.get("description"),
                "thumbnail": work_file.get("thumbnail"),
                "modified_at": work_file.get("modified_at"),
                "modified_by": work_file.get("modified_by", {}),
            }
            
            # Find additional information:
            editable_info = item.get("editable")
            if editable_info and isinstance(editable_info, dict):
                file_details["editable"] = editable_info.get("can_edit", True)
                file_details["editable_reason"] = editable_info.get("reason", "")        
            
            work_files.append(file_details)
            
        return work_files

class AsyncFileFinder(FileFinder):
    """
    Version of the file finder that can perform multiple searches asyncrounously emitting
    any files found via signals as they are found.
    """
    class _SearchData(object):
        def __init__(self, search_id, entity, users, publish_model):
            """
            """
            self.id = search_id
            self.entity = copy.deepcopy(entity)
            self.users = copy.deepcopy(users)
            self.publish_model = publish_model
            self.publish_model_refreshed = False
            self.aborted = False

            self.name_map = FileFinder._FileNameMap()

            self.construct_work_area_task = None
            self.resolve_work_area_task = None
            self.find_work_files_tasks = set()
            self.load_cached_pubs_task = None
            self.find_publishes_tasks = set()
            self.user_work_areas = {}

    _FIND_PUBLISHES_PRIORITY, _FIND_FILES_PRIORITY = (20, 40)

    # Signals
    work_area_found = QtCore.Signal(object, object)
    work_area_resolved = QtCore.Signal(object, object) # search_id, WorkArea
    files_found = QtCore.Signal(object, object, object) # search_id, file list, WorkArea
    publishes_found = QtCore.Signal(object, object, object) # search_id, file list, WorkArea
    search_failed = QtCore.Signal(object, object) # search_id, message
    search_completed = QtCore.Signal(object) # search_id

    def __init__(self, bg_task_manager, parent=None):
        """
        """
        FileFinder.__init__(self, parent)

        self._searches = {}
        self._available_publish_models = []

        self._bg_task_manager = bg_task_manager
        self._bg_task_manager.task_completed.connect(self._on_background_task_completed)
        self._bg_task_manager.task_failed.connect(self._on_background_task_failed)
        self._bg_task_manager.task_group_finished.connect(self._on_background_search_finished)

    def shut_down(self):
        """
        """
        # clean up any publish models - not doing this will result in 
        # severe instability!
        for search in self._searches:
            if search.publish_model:
                self._available_publish_models.append(search.publish_model)
        self._searches = {}
        for publish_model in self._available_publish_models:
            publish_model.destroy()
        self._available_publish_models = []

        # and shut down the task manager
        if self._bg_task_manager:
            # disconnect from the task manager:
            self._bg_task_manager.task_completed.disconnect(self._on_background_task_completed)
            self._bg_task_manager.task_failed.disconnect(self._on_background_task_failed)
            self._bg_task_manager.task_group_finished.disconnect(self._on_background_search_finished)


    def begin_search(self, entity, users = None):
        """
        A full search involves several stages:

        Stage 1;
           - Construct Work Area
               - resolve user sandboxes

        Stage 2:
           - find work-files
               - process work files
           - find cached publishes
               - process cached publishes
           - refresh un-cached publishes

        Stage 3:
           - Process un-cached publishes

        :param entity:  The entity to search for files for
        :param users:   A list of user sandboxes to search for files for.  If 'None' then only files for the current
                        users sandbox will be searched for.
        """
        users = users or []

        # get a new unique group id from the task manager - this will be used as the search id
        search_id = self._bg_task_manager.next_group_id()

        # get a publish model - re-use if possible, otherwise create a new one.  Max number of publish
        # models created will be the max number of searches at any one time.
        publish_model = None
        if self._available_publish_models:
            # re-use an existing publish model:
            publish_model = self._available_publish_models.pop(0)
        else:
            # create a new model:
            publish_model = SgPublishedFilesModel(search_id, self._bg_task_manager, parent=self)
            publish_model.data_refreshed.connect(self._on_publish_model_refreshed)
            publish_model.data_refresh_fail.connect(self._on_publish_model_refresh_failed)
            monitor_qobject_lifetime(publish_model, "Finder publish model")
        publish_model.uid = search_id

        # construct the new search data:
        search = AsyncFileFinder._SearchData(search_id, entity, users, publish_model)
        self._searches[search.id] = search

        # begin the search stage 1:
        self._begin_search_stage_1(search)

        # and return the search id:
        return search.id

    def _begin_search_stage_1(self, search):
        """
        """
        # start Stage 1 to construct the work area:
        # 1a. Construct a work area for the entity.  The work area contains the context as well as
        # all settings, etc. specific to the work area.
        search.construct_work_area_task = self._bg_task_manager.add_task(self._task_construct_work_area,
                                                                         group=search.id,
                                                                         task_kwargs = {"entity": search.entity})

        # 1b. Resolve sandbox users for the work area (if there are any)
        search.resolve_work_area_task = self._bg_task_manager.add_task(self._task_resolve_sandbox_users,
                                                                    group=search.id,
                                                                    upstream_task_ids = [search.construct_work_area_task])

    def _begin_search_for_work_files(self, search, work_area):
        """
        """

        # 2a. Add tasks to find and filter work files:
        for user in search.users:
            user_id = user["id"] if user else None

            # create a copy of the work area for this user:
            user_work_area = work_area.create_copy_for_user(user) if user else work_area
            search.user_work_areas[user_id] = user_work_area

            # find work files:
            find_work_files_task = self._bg_task_manager.add_task(self._task_find_work_files, 
                                                                  group=search.id,
                                                                  priority=AsyncFileFinder._FIND_FILES_PRIORITY,
                                                                  task_kwargs = {"environment":user_work_area})

            # filter work files:
            filter_work_files_task = self._bg_task_manager.add_task(self._task_filter_work_files,
                                                                    group=search.id,
                                                                    priority=AsyncFileFinder._FIND_FILES_PRIORITY,
                                                                    upstream_task_ids = [find_work_files_task],
                                                                    task_kwargs = {"environment":user_work_area})

            # build work items:
            process_work_items_task = self._bg_task_manager.add_task(self._task_process_work_items,
                                                                     group=search.id, 
                                                                     priority=AsyncFileFinder._FIND_FILES_PRIORITY,
                                                                     upstream_task_ids = [filter_work_files_task],
                                                                     task_kwargs = {"environment":user_work_area,
                                                                                    "name_map":search.name_map})
            search.find_work_files_tasks.add(process_work_items_task)

    def _begin_search_process_publishes(self, search, sg_publishes):
        """
        """
        # 3a. Process publishes
        for user in search.users:
            user_id = user["id"] if user else None
            user_work_area = search.user_work_areas[user_id]

            users_publishes = copy.deepcopy(sg_publishes)

            # filter publishes:
            filter_publishes_task = self._bg_task_manager.add_task(self._task_filter_publishes,
                                                                   group=search.id,
                                                                   priority=AsyncFileFinder._FIND_PUBLISHES_PRIORITY,
                                                                   task_kwargs = {"environment":user_work_area,
                                                                                  "sg_publishes":users_publishes})
            # build publish items:
            process_publish_items_task = self._bg_task_manager.add_task(self._task_process_publish_items,
                                                                        group=search.id,
                                                                        priority=AsyncFileFinder._FIND_PUBLISHES_PRIORITY,
                                                                        upstream_task_ids = [filter_publishes_task],
                                                                        task_kwargs = {"environment":user_work_area,
                                                                                       "name_map":search.name_map})

            search.find_publishes_tasks.add(process_publish_items_task)

    def _on_publish_model_refreshed(self, data_changed):
        """
        """
        model = self.sender()
        if model.uid not in self._searches:
            return
        search = self._searches[model.uid]
        search.publish_model_refreshed = True

        # get any publishes from the publish model:
        sg_publishes = copy.deepcopy(search.publish_model.get_sg_data())

        # and begin processing:
        self._begin_search_process_publishes(search, sg_publishes)

    def _on_publish_model_refresh_failed(self, msg):
        """
        """
        model = self.sender()
        search_id = model.search_id
        if search_id not in self._searches:
            return
        self.stop_search(search_id)
        self.search_failed.emit(search_id, msg)

    def _on_background_task_completed(self, task_id, search_id, result):
        """
        Handle completed tasks, emit completion signals, and schedule next steps.

        Runs in main thread
        """
        if search_id not in self._searches:
            return
        search = self._searches[search_id]
        work_area = result.get("environment")

        if task_id == search.construct_work_area_task:
            search.construct_work_area_task = None
            self.work_area_found.emit(search_id, work_area)

            # If one or more template hasn't been configured, derail the whole process
            # and return nothing found.
            missing_templates = work_area.get_missing_templates()
            if missing_templates:
                # Notify that no files were found so the UI can update
                self.publishes_found.emit(search_id, [], work_area)
                self.files_found.emit(search_id, [], work_area)
                search.aborted = True
                return

            # we have successfully constructed a work area that we can 
            # use for the next stage so begin searching for work files:
            self._begin_search_for_work_files(search, work_area)
            # and also add a task to process cached publishes:
            search.load_cached_pubs_task = self._bg_task_manager.add_pass_through_task(group = search.id,
                                                                    priority=AsyncFileFinder._FIND_PUBLISHES_PRIORITY,
                                                                    task_kwargs = {"environment":work_area})
        elif task_id == search.resolve_work_area_task:
            search.resolve_work_area_task = None
            # found a work area so emit it:
            self.work_area_resolved.emit(search_id, work_area)

        elif task_id == search.load_cached_pubs_task:
            search.load_cached_pubs_task = None
            # ok so now it's time to load the cached publishes:
            sg_publishes = self._load_cached_publishes(search, work_area)
            # begin stage 3 for the un-cached publishes:
            self._begin_search_process_publishes(search, sg_publishes)
            # we can also start the background refresh of the publishes model:
            search.publish_model.refresh()

        elif task_id in search.find_publishes_tasks:
            search.find_publishes_tasks.remove(task_id)
            # found publishes:
            publish_item_args = result.get("publish_items", {}).values()
            files = [FileItem(**kwargs) for kwargs in publish_item_args]
            self.publishes_found.emit(search_id, files, work_area)

        elif task_id in search.find_work_files_tasks:
            search.find_work_files_tasks.remove(task_id)
            # found work files:
            work_item_args = result.get("work_items", {}).values()
            files = [FileItem(**kwargs) for kwargs in work_item_args]
            self.files_found.emit(search_id, files, work_area)

    def _on_background_task_failed(self, task_id, search_id, msg, stack_trace):
        """
        """
        if search_id not in self._searches:
            return
        self.stop_search(search_id)

        app = sgtk.platform.current_bundle()
        app.log_error(msg)
        app.log_debug(stack_trace)

        # emit signal:
        self.search_failed.emit(search_id, msg)

    def _on_background_search_finished(self, search_id):
        """
        """
        if search_id not in self._searches:
            return
        search = self._searches[search_id]

        # because of the way the search is split into stages, this signal may
        # be emitted multiple times for a single search so we need to check
        # that the search has actually finished!
        if search.users and not search.aborted:
            if (search.find_publishes_tasks or search.find_work_files_tasks 
                or search.load_cached_pubs_task or not search.publish_model_refreshed
                ):
                # we still have work outstanding!
                return

        # ok, looks like the search is actually complete!
        self.stop_search(search_id)

        # emit search completed signal:
        self.search_completed.emit(search_id)

    def stop_search(self, search_id):
        """
        """
        search = self._searches.get(search_id)
        if not search:
            return

        self._bg_task_manager.stop_task_group(search_id)
        if search.publish_model:
            search.publish_model.clear()
            self._available_publish_models.append(search.publish_model)
        del self._searches[search_id]

    def stop_all_searches(self):
        """
        """
        for search in self._searches.values():
            self._bg_task_manager.stop_task_group(search.id)
            if search.publish_model:
                self._available_publish_models.append(search.publish_model)
        self._searches = {}

    ################################################################################################
    ################################################################################################
    def _task_construct_work_area(self, entity, **kwargs):
        """
        """
        app = sgtk.platform.current_bundle()
        work_area = None
        if entity:
            # build a context from the search details:
            context = app.sgtk.context_from_entity_dictionary(entity)

            # build the work area for this context: This may throw, but the background task manager framework
            # will catch
            work_area = WorkArea(context)
        return {"environment": work_area}

    def _task_resolve_sandbox_users(self, environment, **kwargs):
        """
        """
        if environment:
            environment.resolve_user_sandboxes()
        return {"environment":environment}

    def _load_cached_publishes(self, search, work_area):
        """
        Runs in main thread.
        """
        publish_filters = []
        # If there is no entity in the context then we are trying to load the publishes from the project.
        publish_filters.append(["entity", "is", work_area.context.entity or work_area.context.project])
        if work_area.context.task:
            publish_filters.append(["task", "is", work_area.context.task])
        elif work_area.context.step:
            publish_filters.append(["task.Task.step", "is", work_area.context.step])
        fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]

        # load the data into the publish model:
        search.publish_model.load_data(filters=publish_filters, fields=fields)
        return copy.deepcopy(search.publish_model.get_sg_data())

    def _task_filter_publishes(self, sg_publishes, environment, **kwargs):
        """
        """
        #time.sleep(5)
        filtered_publishes = []
        if sg_publishes and environment and environment.publish_template and environment.context:

            # convert created_at unix time stamp to shotgun std time stamp for all publishes
            for sg_publish in sg_publishes:
                created_at = sg_publish.get("created_at")
                if created_at:
                    created_at = datetime.fromtimestamp(created_at, sg_timezone.LocalTimezone())
                    sg_publish["created_at"] = created_at

            filtered_publishes = self._filter_publishes(sg_publishes, 
                                                        environment.publish_template, 
                                                        environment.valid_file_extensions)
        return {"sg_publishes":filtered_publishes}    

    def _task_process_publish_items(self, sg_publishes, environment, name_map, **kwargs):
        """
        """
        publish_items = {}
        if (sg_publishes and environment and environment.publish_template 
            and environment.work_template and environment.context and name_map):
            publish_items = self._process_publish_files(sg_publishes, 
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
        if (environment and environment.context and environment.work_template):
            work_files = self._find_work_files(environment.context, 
                                               environment.work_template, 
                                               environment.version_compare_ignore_fields)
        return {"work_files":work_files}


    def _task_filter_work_files(self, work_files, environment, **kwargs):
        """
        """
        filtered_work_files = []
        if work_files:
            filtered_work_files = self._filter_work_files(work_files, environment.valid_file_extensions)
        return {"work_files":filtered_work_files}

    def _task_process_work_items(self, work_files, environment, name_map, **kwargs):
        """
        """
        work_items = {}
        if (work_files and environment and environment.work_template 
            and environment.context and name_map):
            work_items = self._process_work_files(work_files, 
                                                  environment.work_template, 
                                                  environment.context,
                                                  name_map,
                                                  environment.version_compare_ignore_fields)
        return {"work_items":work_items, "environment":environment}








