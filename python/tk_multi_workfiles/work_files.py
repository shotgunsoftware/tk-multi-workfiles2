# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import os
from itertools import chain
from datetime import datetime

import tank
from tank.platform.qt import QtCore, QtGui 
from tank import TankError
from tank_vendor.shotgun_api3 import sg_timezone

from .work_file import WorkFile
from .wrapper_dialog import WrapperDialog
from .select_work_area_form import SelectWorkAreaForm
            
from .scene_operation import *

class WorkFiles(object):
    
    @staticmethod
    def show_file_manager_dlg(app):
        """
        Static method to show the WorkFiles dialog
        """
        handler = WorkFiles(app)
        handler.show_dlg()
        
    @staticmethod
    def show_change_work_area_dlg(app, enable_start_new=True):
        """
        Static method to show the WorkFiles Change 
        Work Area dialog
        """
        handler = WorkFiles(app)
        handler.change_work_area(enable_start_new)    
    
    # cached user details:
    _user_details_by_id = {}
    _user_details_by_login = {}
    
    def __init__(self, app):
        """
        Construction
        """
        self._app = app
        self._workfiles_ui = None
        
        self._can_change_workarea = (len(self._app.get_setting("sg_entity_types", [])) > 0)
        self._visible_file_extensions = [".%s" % ext if not ext.startswith(".") else ext for ext in self._app.get_setting("file_extensions", [])]
        
        # set up the work area from the app:
        self._context = None
        self._configuration_is_valid = False
        self._work_template = None
        self._work_area_template = None
        self._publish_template = None
        self._publish_area_template = None
        
        initial_ctx = self._app.context
        if not initial_ctx:
            # TODO: load from setting
            pass
        
        self._update_current_work_area(initial_ctx)
        
    def show_dlg(self):
        """
        Show the main tank file manager dialog 
        """
        #print self.find_files(None)
        #return
        
        try:
            from .work_files_form import WorkFilesForm
            self._workfiles_ui = self._app.engine.show_dialog("Shotgun File Manager", self._app, WorkFilesForm, self._app, self)
        except:
            self._app.log_exception("Failed to create File Manager dialog!")
            return

        # hook up signals:
        self._workfiles_ui.open_publish.connect(self._on_open_publish)
        self._workfiles_ui.open_workfile.connect(self._on_open_workfile)
        self._workfiles_ui.open_previous_publish.connect(self._on_open_previous_publish)
        self._workfiles_ui.open_previous_workfile.connect(self._on_open_previous_workfile)
        
        self._workfiles_ui.new_file.connect(self._on_new_file)
        self._workfiles_ui.show_in_fs.connect(self._on_show_in_file_system)
        self._workfiles_ui.show_in_shotgun.connect(self._on_show_in_shotgun)
        
    def find_files(self, user):
        """
        Find files using the current context, work and publish templates
        
        If user is specified then the context user will be overriden to 
        be this user when resolving paths.
        
        Will return a WorkFile instance for every file found in both
        work and publish areas
        """
        if not self._work_template or not self._publish_template:
            return []
        
        current_user = tank.util.get_current_user(self._app.tank)
        if current_user and user and user["id"] == current_user["id"]:
            # user is current user. Set to none not to override.
            user = None

        # find all published files that match the current template:
        publish_file_details = self._get_published_file_details()
        
        # construct a new context to use for the search overriding the user if required:
        find_ctx = self._context if not user else self._context.create_copy_for_user(user)
        
        # find work files that match the current work template:
        try:
            work_fields = find_ctx.as_template_fields(self._work_template)
        except TankError:
            # could not resolve fields from this context. This typically happens
            # when the context object does not have any corresponding objects on 
            # disk / in the path cache. In this case, we cannot continue with any
            # file system resolution, so basically just exit early insted.
            return []
        
        work_file_paths = self._app.tank.paths_from_template(self._work_template, work_fields, ["version"], skip_missing_optional_keys=True)
            
        # build an index of the published file tasks to use if we don't have a task in the context:
        publish_task_map = {}
        task_id_to_task_map = {}
        publish_file_keys = {}
        if not find_ctx.task:
            for publish_path, publish_details in publish_file_details.iteritems():
                task = publish_details.get("task")
                if not task:
                    continue

                # the key for the path-task map is the 'version zero' work file that 
                # matches this publish path.  This is constructed from the publish
                # fields together with any additional fields from the context etc.
                publish_fields = self._publish_template.get_fields(publish_path)
                publish_fields["version"] = 0
                key = self._work_template.apply_fields(dict(chain(work_fields.iteritems(), publish_fields.iteritems())))

                task_id_to_task_map[task["id"]] = task
                publish_task_map.setdefault(key, set()).add(task["id"])
                publish_file_keys[publish_path] = key
         
        # add entries for work files:
        file_details = {}
        handled_publish_files = set()
        
        key_to_name_map = {}

        for work_path in work_file_paths:
            
            # check if this path should be ignored:
            if self._ignore_file_path(work_path):
                continue
            
            # resolve the publish path:
            fields = self._work_template.get_fields(work_path)

            publish_path = None
            publish_details = None
            try:
                publish_path = self._publish_template.apply_fields(fields)
            except:
                # failed to convert from work path to publish path!
                pass
            else:
                handled_publish_files.add(publish_path)
                publish_details = publish_file_details.get(publish_path)
                
            # create file entry:
            details = {}
            if "version" in fields:
                details["version"] = fields["version"]
            details["name"] = self._get_file_display_name(work_path, self._work_template, fields)

            # entity is always the context entity:
            details["entity"] = find_ctx.entity
            
            if publish_details:
                # add other info from publish:
                details["task"] = publish_details.get("task")
                details["thumbnail"] = publish_details.get("image")
                details["published_at"] = publish_details.get("created_at")
                details["published_by"] = publish_details.get("created_by", {})
                details["publish_description"] = publish_details.get("description")
                details["published_file_id"] = publish_details.get("published_file_id")
            else:
                if find_ctx.task:
                    # can use the task from the context
                    details["task"] = find_ctx.task
                else:
                    task = None
                    # try to create a context from the path and see if that contains a task:
                    wf_ctx = self._app.tank.context_from_path(work_path, find_ctx)
                    task = wf_ctx.task
                    if not task:
                        # try creating a versionless version and see if there is a match in the
                        # published files:
                        key_fields = fields.copy()
                        key_fields["version"] = 0
                        key = self._work_template.apply_fields(key_fields)
                        if key:
                            task_ids = publish_task_map.get(key)
                            if task_ids and len(task_ids) == 1:
                                task = task_id_to_task_map[list(task_ids)[0]]
                            
                    details["task"] = task

            # get the local file modified details:
            details["modified_at"] = datetime.fromtimestamp(os.path.getmtime(work_path), tz=sg_timezone.local)
            details["modified_by"] = self._get_file_last_modified_user(work_path)

            # construct a unique 'key' for this file - this is the versionless path
            # and is used to match up versions across work and published files
            # This can't be 'name' as there may not be a name field!
            fields["version"] = 0
            key = self._work_template.apply_fields(fields)
            
            # ensure that onle one name is used for all versions of a file:
            if key in key_to_name_map:
                details["name"] = key_to_name_map[key]
            else:
                key_to_name_map[key] = details["name"] 

            file_details[work_path] = WorkFile(work_path, publish_path, True, publish_details != None, details)
         
        # add entries for any publish files that don't have a work file
        for publish_path, publish_details in publish_file_details.iteritems():
            if publish_path in handled_publish_files:
                continue
                
            # resolve the work path using work template fields + publish fields:
            publish_fields = self._publish_template.get_fields(publish_path)
            work_path = self._work_template.apply_fields(dict(chain(work_fields.iteritems(), publish_fields.iteritems())))

            details = {}
            
            # check to see if we have this workfile:
            wf = file_details.get(work_path)
            if wf:
                # start with the details from the work file:
                details = wf.details
                
            # add publish details from publish record:
            details["task"] = publish_details.get("task")
            details["thumbnail"] = publish_details.get("image")
            details["published_at"] = publish_details.get("created_at")
            details["published_by"] = publish_details.get("created_by", {})
            details["publish_description"] = publish_details.get("description")
            details["published_file_id"] = publish_details.get("published_file_id")         
                
            if not wf:
                # no work file found!
                
                # fill in general details for the publish:
                details["entity"] = find_ctx.entity
                
                # version - prefer version from Shotgun over fields
                # (although they should be the same!)
                details["version"] = publish_details.get("version_number") or publish_fields.get("version")
                
                # name - prefer name from Shotgun over fields - this
                # only gets used if there is no work file though!
                details["name"] = publish_details.get("name") or self._get_file_display_name(publish_path, self._publish_template, publish_fields)
    
                # get the local file modified details:
                if os.path.exists(publish_path):
                    details["modified_at"] = datetime.fromtimestamp(os.path.getmtime(publish_path), tz=sg_timezone.local)
                    details["modified_by"] = self._get_file_last_modified_user(publish_path)
                else:
                    details["modified_at"] = details["published_at"]
                    details["modified_by"] = details["published_by"]

            key = publish_file_keys.get(publish_path)
            if not key:
                # construct a unique 'key' for this file - this is the versionless work 
                # file path and is used to match up versions across work and published 
                # files.  This can't be 'name' as there may not be a name field!
                publish_fields["version"] = 0
                key = self._work_template.apply_fields(dict(chain(work_fields.iteritems(), publish_fields.iteritems())))

            # ensure that onle one name is used for all versions of a file:
            if key in key_to_name_map:
                details["name"] = key_to_name_map[key]
            else:
                key_to_name_map[key] = details["name"] 

            file_details[work_path] = WorkFile(work_path, publish_path, bool(wf), True, details) 
                        
        return file_details.values()
        
    def _get_file_display_name(self, path, template, fields=None):
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
        
    def _on_show_in_file_system(self, work_area, user):
        """
        Show the work area/publish area path in the file system
        """
        try:
            # first, determine which template to use:
            template = self._work_area_template if work_area else self._publish_area_template
            if not self._context or not template:
                return
            
            # construct a new context to use for the search overriding the user if required:
            work_area_ctx = self._context if not user else self._context.create_copy_for_user(user)
            
            # now build fields to construct path with:
            fields = work_area_ctx.as_template_fields(template)
                
            # try to build a path from the template with these fields:
            while template and template.missing_keys(fields):
                template = template.parent
            if not template:
                # failed to find a template with no missing keys!
                return
            
            # build the path:
            path = template.apply_fields(fields)
        except TankError, e:
            return
        
        # now find the deepest path that actually exists:
        while path and not os.path.exists(path):
            path = os.path.dirname(path)
        if not path:
            return
        path = path.replace("/", os.path.sep)
        
        # build the command:
        system = sys.platform
        if system == "linux2":
            cmd = "xdg-open \"%s\"" % path
        elif system == "darwin":
            cmd = "open \"%s\"" % path
        elif system == "win32":
            cmd = "cmd.exe /C start \"Folder\" \"%s\"" % path
        else:
            raise TankError("Platform '%s' is not supported." % system)
        
        # run the command:
        exit_code = os.system(cmd)
        if exit_code != 0:
            self._app.log_error("Failed to launch '%s'!" % cmd)     
        
    def _on_show_in_shotgun(self, file):
        """
        Show the specified published file in shotgun
        """
        if not file.is_published or file.published_file_id is None:
            return
        
        # construct and open the url:
        published_file_entity_type = tank.util.get_published_file_entity_type(self._app.tank)
        url = "%s/detail/%s/%d" % (self._app.tank.shotgun.base_url, published_file_entity_type, file.published_file_id)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
    def have_valid_configuration_for_work_area(self):
        """
        Returns True if the configuration for the
        current work area is valid
        """
        return self._configuration_is_valid
        
    def can_change_work_area(self):
        """
        Returns True if the work area can 
        be changed        
        """
        return self._can_change_workarea
        
    def can_do_new_file(self):
        """
        Do some validation to see if it's possible to
        start a new file with the selected context.
        """
        can_do_new = (self._context != None 
                      and (self._context.entity or self._context.project)
                      and self._work_area_template != None)
        if not can_do_new:
            return False
        
        # (AD) - this used to check that the context contained everything
        # required by the work area template.  However, this meant that it
        # wasn't possible to start a new file from an entity that didn't
        # exist in the path cache!  This has now been changed so that it's
        # possible to start a new file as long as a work area has been 
        # selected - it's then up to the apps in the new environment to
        # decide what to do if there isn't enough information available in
        # the context.
        
        return True
        
    def _copy_file(self, source_path, target_path):
        """
        Use hook to copy a file from source to target path
        """
        self._app.log_debug("Copying file '%s' to '%s' via hook" % (source_path, target_path))
        self._app.execute_hook("hook_copy_file", 
                               source_path=source_path, 
                               target_path=target_path)
        
    def _restart_engine(self, ctx):
        """
        Set context to the new context.  This will
        clear the current scene and restart the
        current engine with the specified context
        """
        self._app.log_debug("Restarting the engine...")
        
        # restart engine:        
        try:
            current_engine_name = self._app.engine.name
            
            # stop current engine:            
            if tank.platform.current_engine(): 
                tank.platform.current_engine().destroy()
                
            # start engine with new context:
            tank.platform.start_engine(current_engine_name, ctx.tank, ctx)
        except Exception, e:
            raise TankError("Failed to change work area and start a new engine - %s" % e)
        
    def _create_folders(self, ctx):
        """
        Create folders for specified context
        """
        self._app.log_debug("Creating folders for context %s" % ctx)
        
        # create folders:
        ctx_entity = ctx.task or ctx.entity or ctx.project
        self._app.tank.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), engine=self._app.engine.name)
        
    def _on_open_publish(self, publish_file, work_file):
        """
        Function called when user clicks Open for a file
        in the Publish Area
        """
        if not publish_file:
            return
        
        fields = self._publish_template.get_fields(publish_file.publish_path)
        next_version = self._get_next_available_version(fields)
        
        # different options depending if the work file is more 
        # recent or not:
        from .open_file_form import OpenFileForm
        open_mode = OpenFileForm.OPEN_PUBLISH
        
        dlg_title = ""
        if work_file and work_file.is_more_recent_than_publish(publish_file):
            dlg_title = "Found a More Recent Work File!"
        else:
            dlg_title = "Open Publish"    
            work_file = None
            
        form = OpenFileForm(self._app, work_file, publish_file, OpenFileForm.OPEN_PUBLISH_MODE, next_version)
        open_mode = WrapperDialog.show_modal(form, dlg_title, parent=self._workfiles_ui)
            
        if open_mode == OpenFileForm.OPEN_WORKFILE:
            # open the work file:
            if not self._do_open_workfile(work_file):
                return
        elif open_mode == OpenFileForm.OPEN_PUBLISH:
            # open the published file instead:
            if not self._do_open_publish_as_workfile(publish_file, next_version):
                return
        elif open_mode == OpenFileForm.OPEN_PUBLISH_READONLY:
            # open the published file read-only instead:
            if not self._do_open_publish_read_only(publish_file):
                return
        else:
            return
        
        # close work files UI:
        self._workfiles_ui.close()
        
    def _on_open_workfile(self, work_file, publish_file):
        """
        Function called when user clicks Open for a file
        in the Work Area
        """
        if not work_file:
            return
        
        next_version = 0
        
        # different options depending if the publish file is more 
        # recent or not:
        from .open_file_form import OpenFileForm        
        open_mode = OpenFileForm.OPEN_WORKFILE
        if publish_file and not work_file.is_more_recent_than_publish(publish_file):
            
            fields = self._publish_template.get_fields(publish_file.publish_path)
            next_version = self._get_next_available_version(fields)
            
            form = OpenFileForm(self._app, work_file, publish_file, OpenFileForm.OPEN_WORKFILE_MODE, next_version)
            open_mode = WrapperDialog.show_modal(form, "Found a More Recent Publish!", parent=self._workfiles_ui)
            
        if open_mode == OpenFileForm.OPEN_WORKFILE:
            # open the work file:
            if not self._do_open_workfile(work_file):
                return
        elif open_mode == OpenFileForm.OPEN_PUBLISH:
            # open the published file instead:
            if not self._do_open_publish_as_workfile(publish_file, next_version):
                return
        else:
            return
        
        # close work files UI:
        self._workfiles_ui.close()
        
    def _on_open_previous_publish(self, file):
        """
        Open a previous version of a publish file
        """
        if self._do_open_publish_read_only(file):
            # close work files UI:
            self._workfiles_ui.close()
    
    def _on_open_previous_workfile(self, file):
        """
        Open a previous version of a work file - this just opens
        it directly without any file copying or validation
        """
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  

        if self._do_copy_and_open(None, file.path, new_ctx):
            # close work files UI:
            self._workfiles_ui.close()
        
    def _do_open_workfile(self, file):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file or not file.is_local:
            return False
        
        # trying to open a work file...
        src_path = None
        work_path = file.path
        
        # construct a context for this path to determine if it's in
        # a user sandbox or not:
        wp_ctx = self._app.tank.context_from_path(work_path, self._context)
        if wp_ctx.user:
            current_user = tank.util.get_current_user(self._app.tank)
            if current_user and current_user["id"] != wp_ctx.user["id"]:
                
                # file is in a user sandbox - construct path
                # for the current user's sandbox:
                try:                
                    # get fields from work path:
                    fields = self._work_template.get_fields(work_path)
                    
                    # add in the fields from the context with the current user:
                    local_ctx = wp_ctx.create_copy_for_user(current_user)
                    ctx_fields = local_ctx.as_template_fields(self._work_template)
                    fields.update(ctx_fields)
                    
                    # construct the local path from these fields:
                    local_path = self._work_template.apply_fields(fields)                     
                except Exception, e:
                    QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to resolve file path", 
                                           "Failed to resolve the user sandbox file path:\n\n%s\n\nto the local path:\n\n%s\n\nUnable to open file!" % (work_path, e))
                    self._app.log_exception("Failed to resolve user sandbox file path %s" % work_path)
                    return False
        
                if local_path != work_path:
                    # more than just an open so prompt user to confirm:
                    #TODO: replace with tank dialog
                    answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file from another user?",
                                                        ("The work file you are opening:\n\n%s\n\n"
                                                        "is in a user sandbox belonging to %s.  Would "
                                                        "you like to copy the file to your sandbox and open it?" % (work_path, wp_ctx.user["name"])), 
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                    if answer == QtGui.QMessageBox.Cancel:
                        return False

                    src_path = work_path
                    work_path = local_path      
                    
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  

        return self._do_copy_and_open(src_path, work_path, new_ctx)
        
        
    def _do_open_publish_as_workfile(self, file, new_version):
        """
        Open the published file - this will construct a new work path from the 
        work template and the publish fields before copying it and opening it 
        as a new work file
        """
        if not file or not file.is_published:
            return False
        
        # trying to open a publish:
        work_path = None
        src_path = file.publish_path
        
        if not os.path.exists(src_path):
            QtGui.QMessageBox.critical(self._workfiles_ui, "File doesn't exist!", "The published file\n\n%s\n\nCould not be found to open!" % src_path)
            return False 
        
        # get the work path for the publish:
        try:
            # get fields for the path:                
            fields = self._publish_template.get_fields(src_path)

            # construct a context for the path:
            sp_ctx = self._app.tank.context_from_path(src_path, self._context)

            # if current user is defined, update fields to use this:
            current_user = tank.util.get_current_user(self._app.tank)
            if current_user and sp_ctx.user and sp_ctx.user["id"] != current_user["id"]:
                sp_ctx = sp_ctx.create_copy_for_user(current_user)
                
            # finally, use context to populate additional fields:
            ctx_fields = sp_ctx.as_template_fields(self._work_template)
            fields.update(ctx_fields)
        
            # add next version to fields:                
            #new_version = self._get_next_available_version(fields)
            fields["version"] = new_version
            
            # construct work path:
            work_path = self._work_template.apply_fields(fields)
        except Exception, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to get work file path", 
                                   "Failed to resolve work file path from publish path:\n\n%s\n\n%s\n\nUnable to open file!" % (src_path, e))
            self._app.log_exception("Failed to resolve work file path from publish path: %s" % src_path)
            return False
        
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))
        
        return self._do_copy_and_open(src_path, work_path, new_ctx)
        
    def _do_open_publish_read_only(self, file):
        """
        Open a previous version of a publish file from the publish 
        area - this just opens it directly without any file copying 
        or validation
        """
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  

        if not os.path.exists(file.publish_path):
            QtGui.QMessageBox.critical(self._workfiles_ui, "File doesn't exist!", "The published file\n\n%s\n\nCould not be found to open!" % file.publish_path)
            return False

        return self._do_copy_and_open(None, file.publish_path, new_ctx)
        
    def _do_copy_and_open(self, src_path, work_path, new_ctx):
        """
        Copies src_path to work_path, creates folders, restarts
        the engine and then opens the file from work_path        
        """
        if not work_path or not new_ctx:
            # can't do anything!
            return False
           
        if not new_ctx == self._app.context:
            # ensure folders exist.  This serves the
            # dual purpose of populating the path
            # cache and ensuring we can copy the file
            # if we need to
            try:
                self._create_folders(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to create folders!", 
                                           "Failed to create folders:\n\n%s!" % e)
                self._app.log_exception("Failed to create folders")
                return False
        
        # reset the current scene:
        try:
            if not reset_current_scene(self._app, OPEN_FILE_ACTION, self._context):
                self._app.log_debug("Failed to reset the current scene!")
                return False
        except Exception, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to reset the scene", 
                                       "Failed to reset the scene:\n\n%s\n\nUnable to continue!" % e)
            self._app.log_exception("Failed to reset the scene!")
            return False
    
        # if need to, copy the file
        if src_path:
            # check that local path doesn't already exist:
            if os.path.exists(work_path):
                #TODO: replace with tank dialog
                answer = QtGui.QMessageBox.question(self._workfiles_ui, "Overwrite file?",
                                                "The file\n\n%s\n\nalready exists.  Would you like to overwrite it?" % (work_path), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return False
                
            try:
                # copy file:
                self._copy_file(src_path, work_path)
            except Exception, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Copy file failed!", 
                                           "Copy of file failed!\n\n%s!" % e)
                self._app.log_exception("Copy file failed")
                return False            
                    
        # switch context:
        if not new_ctx == self._app.context:
            try:
                # restart the engine with the new context
                self._restart_engine(new_ctx)
            except Exception, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to change the work area", 
                                           "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" % (new_ctx, e))
                self._app.log_exception("Failed to change the work area to %s!" % new_ctx)
                return False

        # open file
        try:
            open_file(self._app, OPEN_FILE_ACTION, self._context, work_path)
        except Exception, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (work_path, e))
            self._app.log_exception("Failed to open file %s!" % work_path)    
            return False
        
        return True

    def _get_next_available_version(self, fields):
        """
        Get the next available version
        """
        from .versioning import Versioning
        versioning = Versioning(self._app, self._work_template, self._publish_template, self._context)
        return versioning.get_next_available_version(fields)

    def _on_new_file(self):
        """
        Perform a new-scene operation initialized with
        the current context
        """
        if not self.can_do_new_file():
            # should never get here as the new button in the UI should
            # be disabled!
            return
        
        # switch context
        try:
            create_folders = not (self._context == self._app.context)
            if not create_folders:
                # see if we have all fields for the work area:
                ctx_fields = self._context.as_template_fields(self._work_area_template)
                if self._work_area_template.missing_keys(ctx_fields):
                    # missing fields might be because the path cache isn't populated
                    # so lets create folders anyway to populate it!
                    create_folders = True
            
            if create_folders:
                # ensure folders exist:
                self._create_folders(self._context)
                
            # reset the current scene:
            if not reset_current_scene(self._app, NEW_FILE_ACTION, self._context):
                self._app.log_debug("Unable to perform New Scene operation after failing to reset scene!")
                return
            
            # prepare the new scene:
            prepare_new_scene(self._app, NEW_FILE_ACTION, self._context)

            if not self._context == self._app.context:            
                # restart the engine with the new context
                self._restart_engine(self._context)
        except Exception, e:
            QtGui.QMessageBox.information(self._workfiles_ui, "Failed to complete new file operation!", 
                                       "Failed to complete new file operation:\n\n%s!" % e)
            self._app.log_exception("Failed to complete new file operation")
            return

        # close work files UI:
        self._workfiles_ui.close()
        
    def get_current_work_area(self):
        """
        Get the current work area/context
        """
        return self._context
        
    def select_work_area(self, mode=SelectWorkAreaForm.SELECT_WORK_AREA):
        """
        Show a ui for the user to select a new work area/context
        :return: Returns the selected context or None if the user cancels
        """
        widget = None
        try:
            title="Pick a Work Area" if mode == SelectWorkAreaForm.SELECT_WORK_AREA else "Change the Current Work Area"
            (res, widget) = self._app.engine.show_modal(title, self._app, SelectWorkAreaForm, self._app, self, mode)
        finally:
            # make sure to explicitly call close so 
            # that browser threads are cleaned up
            # correctly
            if widget:
                widget.close()
        
        if res == QtGui.QDialog.Accepted:

            do_new = widget.do_new_scene

            # update the current work area in the app:
            self._update_current_work_area(widget.context)
            
            # and return it:
            return (self._context, do_new)
        
        return None

    def change_work_area(self, enable_start_new=True):
        """
        Show a ui for the user to select a new work area/context
        and then switch to the new context:
        """     
        if not self.can_change_work_area():
            return
        
        while True:
            context_and_flags = self.select_work_area(SelectWorkAreaForm.CHANGE_WORK_AREA if enable_start_new else SelectWorkAreaForm.CHANGE_WORK_AREA_NO_NEW)
            if not context_and_flags:
                # user cancelled!
                break
            
            if self._do_change_work_area(context_and_flags[1]):
                break
            
        
        
    def create_new_task(self, name, pipeline_step, entity, assigned_to=None):
        """
        Create a new task with the specified information
        :return: Returns the newly created task
        """
        # construct the data for the new Task entity:
        data = {
                "step":pipeline_step,
                "project":self._app.context.project,
                "entity":entity,
                "content":name
        }
        if assigned_to:
            data["task_assignees"] = [assigned_to]
        
        # create the task:
        sg_result = self._app.shotgun.create("Task", data)
        if not sg_result:
            raise TankError("Failed to create new task - reason unknown!") 
        
        # try to set it to IP - not all studios use IP so be careful!
        try:
            self._app.shotgun.update("Task", sg_result["id"], {"sg_status_list": "ip"})
        except:
            pass
        
        return sg_result
    
    def _update_current_work_area(self, ctx):
        """
        Update the current work area being used
        """
        self._app.log_debug("Updating the current work area for context")#: %s..." % ctx)
        
        if ctx == self._context:
            self._app.log_debug("Context hasn't changed so nothing to do!")    
            return
            
        # update templates for the new context:
        templates = {}
        try:
            self._app.log_debug("Retrieving configuration for context")# %s..." % ctx)
            templates = self._get_templates_for_context(ctx, ["template_work", 
                                                              "template_work_area", 
                                                              "template_publish",
                                                              "template_publish_area"])
        except TankError, e:
            # had problems getting the work file settings for the specified context!
            self._app.log_debug("Failed to rerieve configuration: %s" % e)
            self._configuration_is_valid = False
        else:
            self._app.log_debug("Successfully retrieved configuration")
            self._configuration_is_valid = True
        
        #if templates is not None:
        self._work_template = templates.get("template_work")
        self._work_area_template = templates.get("template_work_area")
        self._publish_template = templates.get("template_publish")
        self._publish_area_template = templates.get("template_publish_area")
        self._context = ctx
                    
        # TODO: validate templates?
    
    def _do_change_work_area(self, do_new=False):
        """
        Set context based on selected task
        :return: True if the action was succesful of the user cancelled it, False
        otherwise
        """
        # only change if we have a valid context:
        if not self._context or (self._context == self._app.context and not do_new):
            return True

        # validate that we can change the work area - ideally these
        # checks would be in the UI but they take a little time and
        # the UI feels sluggish so lets do the checks here instead!
        have_valid_config = self.have_valid_configuration_for_work_area()
        can_do_new_file = not do_new or self.can_do_new_file()
        if not have_valid_config or not can_do_new_file:
            msg = ("Unable to change the Work Area to:\n\n"
                   "    %s\n\n" % self._context)
            if not have_valid_config:
                msg += ("Shotgun File Manager has not been configured for the environment "
                        "being used by the selected Work Area!  Please choose a different "
                        "Work Area to continue.\n\n"
                        "(Note: A common reason for this error is if you are using a Task based "
                        "workflow but have not selected a Task in the Work Area.)")
            elif not can_do_new_file:
                msg += ("Shotgun File Manager is not able able to start a new file with the "
                        "selected Work Area.  Please try selecting a more specific Work Area.")
                
            QtGui.QMessageBox.information(self._workfiles_ui, "Shotgun: Unable to change Work Area", msg)
            return False

        if do_new:
            # use the scene operation hook to reset the scene:
            try:
                if not reset_current_scene(self._app, NEW_FILE_ACTION, self._context):
                    self._app.log_debug("Unable to change the current Work Area after failing to reset the scene!")
                    return True
            except Exception, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to reset the scene", 
                                       "Failed to reset the scene:\n\n%s\n\nUnable to continue!" % e)
                self._app.log_exception("Failed to reset the scene!")
                return False

        # create folders and restart engine:
        try:
            self._create_folders(self._context)
            self._restart_engine(self._context)
        except Exception, e:
            QtGui.QMessageBox.critical(self,
                                       "Could not Change Work Area!",
                                       "Could not change work area and start a new "
                                       "engine. This may be because the task doesn't "
                                       "have a step. Details: %s" % e)
            return False
        return True
        
    def _get_user_details(self, login_name):
        """
        Get the shotgun HumanUser entry:
        """
        # first look to see if we've already found it:
        sg_user = WorkFiles._user_details_by_login.get(login_name)
        if not sg_user:
            try:
                filter = ["login", "is", login_name]
                fields = ["id", "type", "email", "login", "name", "image"]
                sg_user = self._app.shotgun.find_one("HumanUser", [filter], fields)
            except:
                sg_user = {}
            WorkFiles._user_details_by_login[login_name] = sg_user
            if sg_user:
                WorkFiles._user_details_by_id[sg_user["id"]] = sg_user
        return sg_user
        
    def _get_file_last_modified_user(self, path):
        """
        Get the user details of the last person
        to modify the specified file        
        """
        login_name = None
        if sys.platform == "win32":
            # TODO: add windows support..
            pass
        else:
            try:
                from pwd import getpwuid                
                login_name = getpwuid(os.stat(path).st_uid).pw_name
            except:
                pass
        
        if login_name:
            return self._get_user_details(login_name)
        
        return None
                        
    def _get_published_file_details(self):
        """
        Get the details of all published files that
        match the current publish template.
        """
        
        # get list of published files for entity:
        filters = [["entity", "is", self._context.entity or self._context.project]]
        if self._context.task:
            filters.append(["task", "is", self._context.task])
        
        published_file_entity_type = tank.util.get_published_file_entity_type(self._app.tank)
        sg_publish_fields = ["description", "version_number", "image", "created_at", "created_by", "name", "path", "task", "description"]
        
        sg_published_files = self._app.shotgun.find(published_file_entity_type, filters, sg_publish_fields)
        
        publish_files = {}
        for sg_file in sg_published_files:
            if not sg_file.get("path"):
                continue
            
            path = sg_file.get("path").get("local_path")
            
            # check if this path should be ignored:
            if self._ignore_file_path(path):
                continue

            # make sure path matches publish template:            
            if not self._publish_template.validate(path):
                continue
                
            details = sg_file.copy()
            details["path"] = path
            details["published_file_id"] = sg_file.get("id")
            
            publish_files[path] = details
            
        return publish_files
    
    def get_usersandbox_users(self):
        """
        Find all available user sandbox users for the 
        current work area.
        """
        if not self._work_area_template:
            return
        
        # find 'user' keys to skip when looking for sandboxes:
        user_keys = ["HumanUser"]
        for key in self._work_area_template.keys.values():
            if key.shotgun_entity_type == "HumanUser":
                user_keys.append(key.name)
        
        # use the fields for the current context to get a list of work area paths:
        self._app.log_debug("Searching for user sandbox paths skipping keys: %s" % user_keys)

        
        try:
            fields = self._context.as_template_fields(self._work_area_template)
        except TankError:
            # fields could not be resolved from the context! This can happen because
            # the context does not have any structure on disk / path cache but is a 
            # "shotgun-only" context which was created from for example a task.
            work_area_paths = []
        else:
            # got our fields. Now get the paths.
            work_area_paths = self._app.tank.paths_from_template(self._work_area_template, fields, user_keys)
        
        # from paths, find a unique list of user's:
        user_ids = set()
        for path in work_area_paths:
            # to find the user, we have to construct a context
            # from the path and then inspect the user from this
            path_ctx = self._app.tank.context_from_path(path)
            user = path_ctx.user
            if user: 
                user_ids.add(user["id"])
        
        # now look for user details in cache:
        user_details = []
        users_to_fetch = []
        for user_id in user_ids:
            details = WorkFiles._user_details_by_id.get(user_id)
            if details is None:
                users_to_fetch.append(user_id)
            else:
                if details:
                    user_details.append(details)
             
        if users_to_fetch:
            # get remaining details from shotgun:
            filter = ["id", "in"] + list(users_to_fetch)
            search_fields = ["id", "type", "email", "login", "name", "image"]
            sg_users = self._app.shotgun.find("HumanUser", [filter], search_fields)

            users_found = set()
            for sg_user in sg_users:
                user_id = sg_user.get("id")
                if user_id not in users_to_fetch:
                    continue
                
                # add to cache:
                WorkFiles._user_details_by_id[user_id] = sg_user
                WorkFiles._user_details_by_login[sg_user["login"]] = sg_user
                user_details.append(sg_user)
                users_found.add(user_id)
            
            # and fill in any blanks so we don't bother searching again:
            for user in users_to_fetch:
                if user_id not in users_found:
                    WorkFiles._user_details_by_id[user_id] = {}
                
        return user_details
        
    def _get_templates_for_context(self, context, keys):
        """
        Find templates for the given context.
        """
        settings = self._get_app_settings_for_context(context)
        if not settings:
            raise TankError("Failed to find Work Files settings for context '%s'.\n\nPlease ensure that"
                            " the Work Files app is installed for the environment that will be used for"
                            " this context" % context)
        
        templates = {}
        for key in keys:
            template = self._app.get_template_from(settings, key)
            templates[key] = template
            
        return templates
            
        
    def _get_app_settings_for_context(self, context):
        """
        Find settings for the app in the specified context
        """
        if not context:
            return
        
        # find settings for all instances of app in 
        # the environment picked for the given context:
        other_settings = tank.platform.find_app_settings(self._app.engine.name, self._app.name, self._app.tank, context)
        
        if len(other_settings) == 1:
            return other_settings[0].get("settings")
    
        settings_by_engine = {}
        for settings in other_settings:
            settings_by_engine.setdefault(settings.get("engine_instance"), list()).append(settings)
        
        # can't handle more than one engine!  
        if len(settings_by_engine) != 1:
            return
            
        # ok, so have a single engine but multiple apps
        # lets try to find an app with the same instance
        # name:
        app_instance_name = None
        for instance_name, engine_app in self._app.engine.apps.iteritems():
            if engine_app == self._app:
                app_instance_name = instance_name
                break
        if not app_instance_name:
            return

        for engine_name, engine_settings in settings_by_engine.iteritems():
            for settings in engine_settings:
                if settings.get("app_instance") == app_instance_name:
                    return settings.get("settings")

    def _ignore_file_path(self, path):
        """
        Return True if this file should be ignored
        completely!
        """
        if self._visible_file_extensions:
            _, ext = os.path.splitext(path)
            if ext and ext not in self._visible_file_extensions:
                # we want to ignore this file!
                return True
            
        return False
