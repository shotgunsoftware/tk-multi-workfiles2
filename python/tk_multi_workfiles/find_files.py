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
from sgtk.platform.qt import QtCore
from tank_vendor.shotgun_api3 import sg_timezone
from sgtk import TankError

from .file_item import FileItem
from .users import UserCache
from .util import get_templates_for_context

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel

class ShotgunPublishedFilesModel(ShotgunModel):
        
    def __init__(self, id, parent=None):
        """
        """
        ShotgunModel.__init__(self, parent, download_thumbs=False, asynchronous=False)
        # (AD) TODO - get type from core
        self._published_file_type = "PublishedFile"
        
        self._id = id
        
    @property
    def id(self):
        return self._id
        
    def load_data(self, filters=None, fields=None):
        """
        """
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = [fields[0]]
        return self._load_data(self, self._published_file_type, filters, hierarchy, fields)
        
    def refresh(self):
        """
        """
        self._refresh_data()
        
    def get_sg_data(self):
        sg_data = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            sg_data.append(item.get_sg_data())
        return sg_data
            


class Task(QtCore.QRunnable, QtCore.QObject):
    """
    Runnable task that can be used with QThreadPool and emits signals on
    completion/failure
    """
    
    completed = QtCore.Signal(object, object)
    failed = QtCore.Signal(object, object)
    
    def __init__(self, id, task_type, func, *args, **kwargs):
        """
        """
        QtCore.QRunnable.__init__(self)
        QtCore.QObject.__init__(self)
                
        self._id = id
        self._task_type = task_type
        
        self._func = func
        self._args = args
        self._kwargs = kwargs
        
        self._mutex = QtCore.QMutex()
        self._is_runnable = True
        
    @property
    def id(self):
        return self._id
    
    @property
    def task_type(self):
        return self._task_type
        
    # @property
    def _get_is_runnable(self):
        try:
            self._mutex.lock()
            return self._is_runnable
        finally:
            self._mutex.unlock()
    # @is_runnable.setter
    def _set_is_runnable(self, value):
        try:
            self._mutex.lock()
            self._is_runnable = value
        finally:
            self._mutex.unlock()
    is_runnable=property(_get_is_runnable, _set_is_runnable)        
        
    def autoDelete(self):
        """
        """
        return False
    
    def run(self):
        """
        """
        if not self.is_runnable:
            # just skip this task
            return
        
        try:
            # run the function with the provided args
            result = self._func(*self._args, **self._kwargs)
            self.completed.emit(self, result)
        except Exception, e:
            self.failed.emit(self, str(e))

class FileFinder(QtCore.QObject):
    """
    Helper class to find work and publish files for a specified context and set of templates
    """
    
    search_failed = QtCore.Signal(object, object)
    files_found = QtCore.Signal(object, object) # search_id, file_list
    
    class SearchData(object):
        """
        """
        __next_search_id = 0
        
        def __init__(self, context):
            self._id = FileFinder.SearchData.__next_search_id
            FileFinder.SearchData.__next_search_id += 1

            self.tasks = []
            #self.sg_model = None
            
            self.context = context 
            self.work_template = None
            self.publish_template = None
            
            self.sg_publishes = None
            self.publishes = None
            self.work_files = None
            
        @property
        def id(self):
            return self._id
    
    _FIND_TEMPLATES_TASK_TYPE = "find_templates"
    _FIND_SG_PUBLISHES_TASK_TYPE = "find_sg_publishes"
    _FIND_WORK_FILES_TASK_TYPE = "find_work_files"
    _AGGREGATE_FILES_TASK_TYPE = "aggregate_files"
    
    def __init__(self, app=None, user_cache=None, parent=None):
        """
        Construction
        
        :param app:           The Workfiles app instance
        :param user_cache:    An UserCache instance used to retrieve Shotgun user information
        """
        QtCore.QObject.__init__(self, parent)
        
        self.__app = app or sgtk.platform.current_bundle()
        self.__user_cache = user_cache or UserCache(app)
        
        # cache the valid file extensions that can be found
        self.__visible_file_extensions = [".%s" % ext if not ext.startswith(".") else ext 
                                          for ext in self.__app.get_setting("file_extensions", [])]
        
        # and cache any fields that should be ignored when comparing work files:
        self.__version_compare_ignore_fields = self.__app.get_setting("version_compare_ignore_fields", [])
        
        self._next_search_id = 0
        self._search_data = {}
        
    def start_task(self, search_id, task_type, func, *args, **kwargs):
        """
        """        
        task = Task(search_id, task_type, func, *args, **kwargs)
        task.completed.connect(self._on_task_completed)
        task.failed.connect(self._on_task_failed)
        QtCore.QThreadPool.globalInstance().start(task)
        return task
        
    def begin_search(self, publish_filters, context, force=False):
        """
        [publishes from Shotgun] ->  
                [find_templates] -> [build publishes list] ->
                                 -> [find work files]      -> [aggregate files]        
        """
        search_data = FileFinder.SearchData(context)
        self._search_data[search_data.id] = search_data
        
        # start the task to find the work and publish templates for the specified context:
        find_templates_task = self.start_task(search_data.id, 
                                              FileFinder._FIND_TEMPLATES_TASK_TYPE, 
                                              self._find_templates, context)
        search_data.tasks.append(find_templates_task)

        # start the task to finding publishes in Shotgun:
        find_publishes_task = self.start_task(search_data.id, 
                                              FileFinder._FIND_SG_PUBLISHES_TASK_TYPE, 
                                              self._find_publishes, publish_filters, force)
        search_data.tasks.append(find_publishes_task)
            
        return search_data.id
    
    def stop_search(self, search_id):
        """
        """
        search_data = self._search_data.get(search_id)
        if search_data:
            # stop any currently running tasks:
            for task in search_data.tasks:
                task.is_runnable = False
                #task.completed.disconnect(self._on_task_completed)
                #task.failed.disconnect(self._on_task_failed)

            # clean up the Shotgun model:
            # ???
            
            del(self._search_data[search_id])
    
    def stop_all_searches(self, search_id):
        """
        """
        for id in self._search_data.keys():
            self.stop_search(id)
    
    def _on_search_failed(self, search_id, error):
        """
        """
        # clean up search intermediate data:
        self.stop_search(search_id)
        
        # emit signal:
        self.search_failed.emit(search_id, error)
        
    def _on_search_complete(self, search_id, files):
        """
        """
        # clean up search intermediate data:
        self.stop_search(search_id)
        
        # emit signal:
        self.files_found.emit(search_id, files)
        
    ################################################################################################
    ################################################################################################
    
    def _find_templates(self, context):
        """
        """
        try:
            templates = get_templates_for_context(self.__app, context, ["template_work", "template_publish"])
            work_template = templates.get("template_work")
            publish_template = templates.get("template_publish")
            return (work_template, publish_template)
        except TankError, e:
            # had problems getting the work file settings for the specified context!
            raise
    
    def _find_publishes(self, publish_filters, force):
        """
        """
        model = ShotgunPublishedFilesModel(self)
        model.set_shotgun_connection(self.__app.shotgun)
        
        # start the process of finding publishes in Shotgun:
        loaded_data = model.load_data(publish_filters)
        if not loaded_data or force:
            # refresh data from Shotgun:
            model.refresh()

        sg_publishes = model.get_sg_data()
        return sg_publishes
    
    def _filter_publishes(self, sg_publishes, publish_template, context):
        """
        """
        pass    
    
    def _find_work_files(self, context, work_template):
        """
        """
        return self.__find_work_files(context, work_template)

    def _on_task_completed(self, task, result):
        """
        """
        search_data = self._search_data.get(task.id)
        if not search_data:
            return
        
        if task.task_type == FileFinder._FIND_TEMPLATES_TASK_TYPE:
            search_data.work_template, search_data.publish_template = result
            
            # start task to find work files:
            find_files_task = self.start_task(search_data.id, 
                                              FileFinder._FIND_WORK_FILES_TASK_TYPE, 
                                              self._find_work_files, search_data.context, search_data.work_template)
            search_data.tasks.append(find_files_task)
            
            # trigger publishes found path:
            self._on_publishes_found(search_data.id)
          
        elif task.task_type == FileFinder._FIND_SG_PUBLISHES_TASK_TYPE:
            
            print "SEARCH RES: %s" % result
            search_data.sg_publishes = result
            
            # (AD) TEMP - STEPS MISSING
            search_data.publishes = []
            self._on_find_completed(task.id)
           
        elif task.task_type == FileFinder._FIND_WORK_FILES_TASK_TYPE:
            search_data.work_files = result
            self._on_find_completed(task.id)
            
        elif task.task_type == FileFinder._AGGREGATE_FILES_TASK_TYPE:
            self._on_search_complete(task.id, result)
        else:
            pass
    
    def _on_task_failed(self, task, error):
        """
        """
        self._on_search_failed(task.id, error)
        
        
        
    def _on_publishes_data_refreshed(self, search_id, updated):
        """
        """
        search_data = self._search_data.get(search_id)
        if not search_data:
            return
        
        search_data.sg_publishes = self._publishes_model.get_sg_data()
        
        self._on_publishes_found(search_id)
        
    def _on_publishes_data_refresh_failed(self, search_id, error):
        """
        """
        self._on_search_failed(search_id, error)
        


    def _on_publishes_found(self, search_id):
        """
        """
        search_data = self._search_data.get(search_id)
        if not search_data:
            return
        
        if not search_data.sg_publishes or not search_data.publish_template:
            # don't have everything we need yet to build published file list!
            return
        
        # start new task to aggregate publishes and work files together:
        aggregate_files_task = self.start_task(search_data.id, 
                                               FileFinder._FILTER_PUBLISHES_TASK_TYPE, 
                                               self._filter_publishes, search_data.sg_publishes, 
                                               search_data.publish_template, search_data.context)
        search_data.tasks.append(aggregate_files_task)
        
        
    def _on_find_completed(self, search_id):
        """
        """
        search_data = self._search_data.get(search_id)
        if not search_data:
            return
        
        if search_data.publishes == None or search_data.work_files == None:
            # both searches haven't finished yet so can't aggregate!
            return

        # start new task to aggregate publishes and work files together:
        aggregate_files_task = self.start_task(search_data.id, 
                                               FileFinder._AGGREGATE_FILES_TASK_TYPE, 
                                               self._aggregate_files, search_data.publishes, 
                                               search_data.publish_template, search_data.work_files, 
                                               search_data.work_template, search_data.context)
        search_data.tasks.append(aggregate_files_task)
        
    #    
    #################################################################################################
    #################################################################################################
    ## slots for shotgun model refresh/fail
    #def _on_find_publishes_data_refreshed(self, something_changed):
    #    """
    #    """
    #    # ok, now we have the publishes list we need to start a new task
    #    # to filter them and turn them into a usable list!
    #    
    #
    #def _on_find_publishes_data_refresh_failed(self, error):
    #    """
    #    """
    #    search_id = 0
    #    self._on_search_failed(search_id, error)
    #
    #################################################################################################
    #################################################################################################
    ## mechanism for building publish list:
    #def _build_publishes_list(self):
    #    pass
    #
    #def _on_process_publishes_task_completed(self, task, result):
    #    """
    #    """
    #    if task.id not in self._search_results:
    #        # no longer needed so disgard:
    #        return        
    #    self._search_results[task.id]["publishes"] = result
    #    self._find_completed()
    #
    #def _on_process_publishes_task_failed(self, task, error):
    #    """
    #    """
    #    self._on_search_failed(task.id, error)
    #    

        


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
    
        # find all work & publish files and filter out any that should be ignored:
        work_files = self.__find_work_files(context, work_template)
        published_files = self.__find_publishes(context, publish_template)
        
        return self._aggregate_files(work_files, work_template, published_files, publish_template, context, filter_file_key)

    def _aggregate_files(self, work_files, work_template, published_files, publish_template, context, filter_file_key=None):
        """
        """

        work_files = [wf for wf in work_files if not self.__ignore_file_path(wf["path"])]
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
            
            # build the unique file key for the work path.  All files that share the same key are considered
            # to be different versions of the same file.
            #
            file_key = FileItem.build_file_key(wf_fields, work_template, 
                                               self.__version_compare_ignore_fields + ["version"])
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
            # publish file is in a user sandbox but we also need to be careful not
            # to overrwrite fields that are being ignored when comparing work files
            publish_fields = publish_template.get_fields(publish_path)
            wp_fields = publish_fields.copy()
            for k, v in ctx_fields.iteritems():
                if k not in self.__version_compare_ignore_fields:
                    wp_fields[k] = v
            
            # build the unique file key for the publish path.  All files that share the same key are considered
            # to be different versions of the same file.
            file_key = FileItem.build_file_key(wp_fields, work_template, 
                                               self.__version_compare_ignore_fields + ["version"])
            if filter_file_key and file_key != filter_file_key:
                # we can ignore this file completely!
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
        
        # build list of fields to ignore when looking for files:
        skip_fields = list(self.__version_compare_ignore_fields)

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
















