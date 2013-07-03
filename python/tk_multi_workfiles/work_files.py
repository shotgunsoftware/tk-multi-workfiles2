"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import sys
import os
from itertools import chain
from datetime import datetime

import tank
from tank.platform.qt import QtCore, QtGui 
from tank import TankError
from tank_vendor.shotgun_api3 import sg_timezone

from .work_file import WorkFile

class WorkFiles(object):
    
    def __init__(self, app):
        """
        Construction
        """
        self._app = app
        self._workfiles_ui = None
        
        self._user_details_by_id = {}
        self._user_details_by_login = {}
        
        # set up the work area from the app:
        self._context = None
        self._configuration_is_valid = False
        self._work_template = None
        self._work_area_template = None
        self._publish_template = None
        self._publish_area_template = None
        
        initial_ctx = self._app.context
        if not initial_ctx or not initial_ctx:
            # TODO: load from setting
            pass
        
        self._update_current_work_area(initial_ctx)
        
    def show_dlg(self):
        """
        Show the main tank file manager dialog 
        """
        
        from .work_files_form import WorkFilesForm
        self._workfiles_ui = self._app.engine.show_dialog("Shotgun File Manager", self._app, WorkFilesForm, self._app, self)

        # hook up signals:
        self._workfiles_ui.open_file.connect(self._on_open_file)
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
        work_fields = find_ctx.as_template_fields(self._work_template)
        work_file_paths = self._app.tank.paths_from_template(self._work_template, work_fields, ["version"])
        
        # build an index of the published file tasks to use if we don't have a task in the context:
        publish_task_map = {}
        task_id_to_task_map = {}
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
                work_path_key = self._work_template.apply_fields(dict(chain(work_fields.iteritems(), publish_fields.iteritems())))
                
                task_id_to_task_map[task["id"]] = task
                publish_task_map.setdefault(work_path_key, set()).add(task["id"])
         
        # add entries for work files:
        file_details = []
        handled_publish_files = set()
        
        for work_path in work_file_paths:
            # resolve the publish path:
            fields = self._work_template.get_fields(work_path)
            publish_path = self._publish_template.apply_fields(fields)
            
            handled_publish_files.add(publish_path)
            publish_details = publish_file_details.get(publish_path)
                
            # create file entry:
            details = {}
            if "version" in fields:
                details["version"] = fields["version"]
            if "name" in fields:
                details["name"] = fields["name"]

            # entity is always the context entity:
            details["entity"] = find_ctx.entity
            
            if publish_details:
                # add other info from publish:
                details["task"] = publish_details.get("task")
                details["thumbnail"] = publish_details.get("image")
                details["modified_time"] = publish_details.get("created_at")
                details["modified_by"] = publish_details.get("created_by", {})
                details["publish_description"] = publish_details.get("description")
                details["published_file_id"] = publish_details.get("published_file_id")
            else:
                if find_ctx.task:
                    # can use the task form the context
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

                # get the local file modified time - ensure it has a time-zone set:
                details["modified_time"] = datetime.fromtimestamp(os.path.getmtime(work_path), tz=sg_timezone.local)
                
                # get the last modified by:
                last_user = self._get_file_last_modified_user(work_path)
                details["modified_by"] = last_user

            file_details.append(WorkFile(work_path, publish_path, True, publish_details != None, details))
         
        # add entries for any publish files that don't have a work file
        for publish_path, publish_details in publish_file_details.iteritems():
            if publish_path in handled_publish_files:
                continue
                
            # resolve the work path using work template fields + publish fields:
            publish_fields = self._publish_template.get_fields(publish_path)
            work_path = self._work_template.apply_fields(dict(chain(work_fields.iteritems(), publish_fields.iteritems())))

            # create file entry:
            is_work_file = (work_path in work_file_paths)
            details = {}            
            if "version" in publish_fields:
                details["version"] = publish_fields["version"]
            if "name" in publish_fields:
                details["name"] = publish_fields["name"]

            details["entity"] = find_ctx.entity
                
            # add additional details from publish record:
            details["task"] = publish_details.get("task")
            details["thumbnail"] = publish_details.get("image")
            details["modified_time"] = publish_details.get("created_at")
            details["modified_by"] = publish_details.get("created_by", {})
            details["publish_description"] = publish_details.get("description")
            details["published_file_id"] = publish_details.get("published_file_id")
                
            file_details.append(WorkFile(work_path, publish_path, is_work_file, True, details))            

        return file_details
        
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
        return self._configuration_is_valid
        
    def can_do_new_file(self):
        """
        Do some validation to see if it's possible to
        start a new file with the selected context.
        """
        if (not self._context
            or not self._context.entity 
            or not self._work_area_template):
            return False
        
        # ensure that context contains everything required by the work area template:
        ctx_fields = self._context.as_template_fields(self._work_area_template)
        if self._work_area_template.missing_keys(ctx_fields):
            return False
        
        return True
        
    def _reset_current_scene(self):
        """
        Use hook to clear the current scene
        """
        res = self._app.execute_hook("hook_scene_operation", operation="reset", file_path=None, context = self._context)
        if res == None or not isinstance(res, bool):
            raise TankError("Unexpected type returned from 'hook_scene_operation' - expected 'bool' but returned '%s'" % type(res).__name__)
        return res
    
    def _open_file(self, path):
        """
        Use hook to open the specified file.
        """
        # do open:
        self._app.execute_hook("hook_scene_operation", operation="open", file_path=path, context = self._context)
        
    def _copy_file(self, source_path, target_path):
        """
        Use hook to copy a file from source to target path
        """
        self._app.execute_hook("hook_copy_file", 
                               source_path=source_path, 
                               target_path=target_path)
        
    def _save_file(self):
        """
        Use hook to save the current file
        """
        self._app.execute_hook("hook_scene_operation", operation="save", file_path=None, context = self._context)
        
    def _restart_engine(self, ctx):
        """
        Set context to the new context.  This will
        clear the current scene and restart the
        current engine with the specified context
        """
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
        # create folders:
        ctx_entity = ctx.task if ctx.task else ctx.entity
        self._app.tank.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), engine=self._app.engine.name)
        
    def _on_open_file(self, file, is_previous_version):
        """
        Main function used to open a file when requested by the UI
        """
        if not file:
            return

        # get the path of the file to open.  Handle
        # other user sandboxes and publishes if need to
        
        src_path = None
        work_path = None
        
        if is_previous_version:
            # if the file is a previous version then we just open it
            # rather than attempting to copy it
            if file.is_local:
                work_path = file.path
            else:
                work_path = file.publish_path
                if not os.path.exists(work_path):
                    QtGui.QMessageBox.critical(self._workfiles_ui, "File doesn't exist!", "The published file\n\n%s\n\nCould not be found to open!" % work_path)
                    return 
        else:
            # what we do depends on the current location of the file
            
            if file.is_local:
                # trying to open a work file...
                work_path = file.path
                
                # construct a context for this path to determine if it's in
                # a user sandbox or not:
                wp_ctx = self._app.tank.context_from_path(work_path)
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
                        except TankError, e:
                            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to resolve file path", 
                                                   "Failed to resolve the user sandbox file path:\n\n%s\n\nto the local path:\n\n%s\n\nUnable to open file!" % (work_path, e))
                            return
                        except Exception, e:
                            self._app.log_exception("Failed to resolve user sandbox file path %s" % work_path)
                            return
                
                        if local_path != work_path:
                            # more than just an open so prompt user to confirm:
                            #TODO: replace with tank dialog
                            answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file from another user?",
                                                                ("The work file you are opening:\n\n%s\n\n"
                                                                "is in a user sandbox belonging to %s.  Would "
                                                                "you like to copy the file to your sandbox and open it?" % (work_path, wp_ctx.user["name"])), 
                                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                            if answer == QtGui.QMessageBox.Cancel:
                                return
    
                            src_path = work_path
                            work_path = local_path        

            else:
                # trying to open a publish:
                src_path = file.publish_path
                
                if not os.path.exists(src_path):
                    QtGui.QMessageBox.critical(self._workfiles_ui, "File doesn't exist!", "The published file\n\n%s\n\nCould not be found to open!" % src_path)
                    return 
                
                new_version = None
                
                # get the work path for the publish:
                try:
                    # get fields for the path:                
                    fields = self._publish_template.get_fields(src_path)

                    # construct a context for the path:
                    sp_ctx = self._app.tank.context_from_path(src_path)

                    # if current user is defined, update fields to use this:
                    current_user = tank.util.get_current_user(self._app.tank)
                    if current_user and sp_ctx.user and sp_ctx.user["id"] != current_user["id"]:
                        sp_ctx = sp_ctx.create_copy_for_user(current_user)
                        
                    # finally, use context to populate additional fields:
                    ctx_fields = sp_ctx.as_template_fields(self._work_template)
                    fields.update(ctx_fields)
                
                    # add next version to fields:                
                    new_version = self._get_next_available_version(fields)
                    fields["version"] = new_version
                    
                    # construct work path:
                    work_path = self._work_template.apply_fields(fields)
                except TankError, e:
                    QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to get work file path", 
                                           "Failed to resolve work file path from publish path:\n\n%s\n\n%s\n\nUnable to open file!" % (src_path, e))
                    return
                except Exception, e:
                    self._app.log_exception("Failed to resolve work file path from publish path: %s" % src_path)
                    return
                
                # prompt user to confirm:
                answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file from publish area?",
                                                                ("The published file:\n\n%s\n\n"
                                                                "will be copied to your work area, versioned "
                                                                "up to v%03d and then opened.\n\n"
                                                                "Would you like to continue?" % (src_path, new_version)), 
                                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return

        # get best context we can for file:
        ctx_entity = file.task if file.task else file.entity
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))

        if not work_path or not new_ctx:
            # can't do anything!
            return
           
        if new_ctx != self._app.context:
            # ensure folders exist.  This serves the
            # dual purpose of populating the path
            # cache and ensuring we can copy the file
            # if we need to
            try:
                self._create_folders(new_ctx)
            except TankError, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to create folders!", 
                                           "Failed to create folders:\n\n%s!" % e)
                return
            except Exception, e:
                self._app.log_exception("Failed to create folders")
                return
        
        # if need to, copy file
        if src_path:
            # check that local path doesn't already exist:
            if os.path.exists(work_path):
                #TODO: replace with tank dialog
                answer = QtGui.QMessageBox.question(self._workfiles_ui, "Overwrite file?",
                                                "The file\n\n%s\n\nalready exists.  Would you like to overwrite it?" % (work_path), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return
                
            try:
                # copy file:
                self._copy_file(src_path, work_path)
            except TankError, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Copy file failed!", 
                                           "Copy of file failed!\n\n%s!" % e)
                return
            except Exception, e:
                self._app.log_exception("Copy file failed")
                return            
                    
        # switch context (including do new file):
        try:
            # reset the current scene:
            if not self._reset_current_scene():
                self._app.log_debug("Unable to perform New Scene operation after failing to reset scene!")
                return
            
            if new_ctx != self._app.context:
                # restart the engine with the new context
                self._restart_engine(new_ctx)
        except TankError, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to change work area", 
                                       "Failed to change the work area to '%s':\n\n%s\n\nUnable to continue!" % (new_ctx, e))
            return
        except Exception, e:
            self._app.log_exception("Failed to set work area to %s!" % new_ctx)
            return

        # open file
        try:
            self._open_file(work_path)
        except TankError, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (work_path, e))
            return
        except Exception, e:
            self._app.log_exception("Failed to open file %s!" % work_path)
            return
        
        # close work files UI as it will no longer
        # be valid anyway as the context has changed
        self._workfiles_ui.close()


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
        # switch context
        try:
            if self._context != self._app.context:
                # ensure folders exist:
                self._create_folders(self._context)

            # reset the current scene:
            if not self._reset_current_scene():
                self._app.log_debug("Unable to perform New Scene operation after failing to reset scene!")
                return

            if self._context != self._app.context:            
                # restart the engine with the new context
                self._restart_engine(self._context)
        except TankError, e:
            QtGui.QMessageBox.information(self._workfiles_ui, "Something went wrong!", 
                                       "Something went wrong:\n\n%s!" % e)
            return
        except Exception, e:
            self._app.log_exception("Failed to do new file")
            return

        # close work files UI:
        self._workfiles_ui.close()
        
    def get_current_work_area(self):
        """
        Get the current work area/context
        """
        return self._context
        
    def change_work_area(self):
        """
        Show a ui for the user to select a new work area/context
        """
        from .select_work_area_form import SelectWorkAreaForm
        (res, widget) = self._app.engine.show_modal("Pick a Work Area", self._app, SelectWorkAreaForm, self._app, self)
        
        # make sure to explicitly call close so 
        # that browser threads are cleaned up
        # correctly
        widget.close()
        
        if res == QtGui.QDialog.Accepted:
            
            # update the current work area:
            self._update_current_work_area(widget.context)
            
            # and return it:
            return self._context

        return None
        
    def create_new_task(self):
        """
        Called when user clicks the new task button 
        on the select work area form
        """
        raise NotImplementedError     
    
    def _update_current_work_area(self, ctx):
        """
        Update the current work area being used
        """
        if self._context != ctx:
            
            # update templates for the new context:
            templates = {}
            try:
                templates = self._get_templates_for_context(ctx, ["template_work", 
                                                                  "template_work_area", 
                                                                  "template_publish",
                                                                  "template_publish_area"])
            except TankError, e:
                # had problems getting the work file settings for the specified context!
                self._app.log_debug(e)
                self._configuration_is_valid = False
            else:
                self._configuration_is_valid = True
            
            #if templates is not None:
            self._work_template = templates.get("template_work")
            self._work_area_template = templates.get("template_work_area")
            self._publish_template = templates.get("template_publish")
            self._publish_area_template = templates.get("template_publish_area")
            self._context = ctx
                    
            # TODO: validate templates?
    
        
    def _get_user_details(self, login_name):
        """
        Get the shotgun HumanUser entry:
        """
        # first look to see if we've already found it:
        sg_user = self._user_details_by_login.get(login_name)
        if not sg_user:
            try:
                filter = ["login", "is", login_name]
                fields = ["id", "type", "email", "login", "name", "image"]
                sg_user = self._app.shotgun.find_one("HumanUser", [filter], fields)
            except:
                sg_user = {}
            self._user_details_by_login[login_name] = sg_user
            if sg_user:
                self._user_details_by_id[sg_user["id"]] = sg_user
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
        filters = [["entity", "is", self._context.entity]]
        if self._context.task:
            filters.append(["task", "is", self._context.task])
        
        published_file_entity_type = tank.util.get_published_file_entity_type(self._app.tank)
        sg_publish_fields = ["description", "version_number", "image", "created_at", "created_by", "name", "path", "task", "description"]
        sg_published_files = self._app.shotgun.find(published_file_entity_type, filters, sg_publish_fields)
        
        publish_files = {}
        for sg_file in sg_published_files:

            path = sg_file.get("path").get("local_path")

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
        fields = self._context.as_template_fields(self._work_area_template)
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
            details = self._user_details_by_id.get(user_id)
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
                self._user_details_by_id[user_id] = sg_user
                self._user_details_by_login[sg_user["login"]] = sg_user
                user_details.append(sg_user)
                users_found.add(user_id)
            
            # and fill in any blanks so we don't bother searching again:
            for user in users_to_fetch:
                if user_id not in users_found:
                    self._user_details_by_id[user_id] = {}
                
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
        for instance_name, engine_app in self._app.engine.apps.iteritems:
            if engine_app == app:
                app_instance_name = instance_name
                break
        if not app_instance_name:
            return
    
        for engine_name, engine_settings in settings_by_engine.iteritems():
            for settings in engine_settings:
                if settings.get("app_instance") == app_instance_name:
                    return settings.get("settings")
        

    
    
    
    
