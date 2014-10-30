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
from pprint import pprint

import tank
from tank.platform.qt import QtCore, QtGui 
from tank import TankError
from tank_vendor.shotgun_api3 import sg_timezone

from .file_item import FileItem
from .wrapper_dialog import WrapperDialog
from .select_work_area_form import SelectWorkAreaForm
            
from .scene_operation import reset_current_scene, prepare_new_scene, open_file, OPEN_FILE_ACTION, NEW_FILE_ACTION

from .file_list_view import FileListView
from .file_filter import FileFilter
from .find_files import FileFinder
from .users import UserCache

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
    
    @staticmethod
    def show_file_open_dlg():
        """
        """
        app = tank.platform.current_bundle()
        handler = WorkFiles(app)
        handler.__show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        """
        app = tank.platform.current_bundle()
        handler = WorkFiles(app)
        handler.__show_file_save_dlg()
    
    def __show_file_open_dlg(self):
        """
        """
        try:
            from .file_open_form import FileOpenForm
            self._file_open_ui = self._app.engine.show_dialog("File Open", self._app, FileOpenForm)
        except:
            self._app.log_exception("Failed to create File Open dialog!")
            return
    
    def __show_file_save_dlg(self):
        """
        """
        try:
            from .file_save_form import FileSaveForm
            self._file_save_ui = self._app.engine.show_dialog("File Save", self._app, FileSaveForm)
        except:
            self._app.log_exception("Failed to create File Save dialog!")
            return
    
    def __init__(self, app):
        """
        Construction
        """
        self._app = app
        self._workfiles_ui = None

        # user cache used to cache Shotgun user details:
        self._user_cache = UserCache(self._app)
        
        # determine if changing work area should be available based on the sg_entity_types setting:
        self._can_change_workarea = (len(self._app.get_setting("sg_entity_types", [])) > 0)
        
        # cache any fields that should be ignored when looking for work files:
        self.__version_compare_ignore_fields = self._app.get_setting("version_compare_ignore_fields", [])
        
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
        try:
            from .work_files_form import WorkFilesForm
            self._workfiles_ui = self._app.engine.show_dialog("Shotgun File Manager", self._app, 
                                                              WorkFilesForm, self._app, self)
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
        
    def find_files(self, filter):
        """
        Find files using the current context, work and publish templates
        
        :param filter:  The filter to use when finding files.  If the filter specifies a user 
                        then the context will be overriden to be this user when resolving paths.
        
        :returns:       A list of FileItem instances for every file found in either the work or 
                        publish areas
        """
        find_ctx = self._context
    
        # check to see if the user is overriden by the filter:
        filter_user = filter.user if filter else None
        if filter_user:
            current_user = tank.util.get_current_user(self._app.tank)
            if current_user and filter_user["id"] != current_user["id"]:
                # create a context for the specific filter user:
                find_ctx = self._context.create_copy_for_user(filter_user)        
        
        finder = FileFinder(self._app, self._user_cache)
        return finder.find_files(self._work_template, self._publish_template, find_ctx)        
        
    def _on_show_in_file_system(self):
        """
        Show the work area/publish area path in the file system
        """
        # get the current filter being used:
        current_filter = self._workfiles_ui.filter
        
        try:
            # first, determine which template to use:
            template = self._work_area_template
            if (current_filter.mode == FileFilter.PUBLISHES_MODE):
                template = self._publish_area_template
            
            if not self._context or not template:
                return
            
            # construct a new context to use for the search overriding the user if required:
            work_area_ctx = (self._context if not current_filter.user 
                             else self._context.create_copy_for_user(current_filter.user))
            
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
        self._app.tank.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"), 
                                                   engine=self._app.engine.name)
        
    def _on_open_publish(self, publish_file, work_file):
        """
        Function called when user clicks Open for a file
        in the Publish Area
        """
        if not publish_file:
            return

        # calculate the next version:
        next_version = self._get_next_available_version(work_file.path if work_file else None, 
                                                        publish_file.publish_path)
        
        # options are different if the publish and work files are the same path as there
        # doesn't need to be the option of opening the publish read-only.
        publish_requires_copy = True
        if self._publish_template == self._work_template:
            if "version" not in self._publish_template.keys:
                publish_requires_copy = False
        
        # different options depending if the work file is more 
        # recent or not:
        dlg_title = ""
        if work_file and work_file.compare_with_publish(publish_file) > 0:
            dlg_title = "Found a More Recent Work File!"
        else:
            dlg_title = "Open Publish"    
            work_file = None
            
        if work_file or publish_requires_copy:
            # show dialog with options to user:
            from .open_file_form import OpenFileForm
            open_mode = OpenFileForm.OPEN_PUBLISH
            
            mode = OpenFileForm.OPEN_PUBLISH_MODE if publish_requires_copy else OpenFileForm.OPEN_PUBLISH_NO_READONLY_MODE 
            form = OpenFileForm(self._app, work_file, publish_file, mode, next_version, publish_requires_copy)
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
                if not self._do_open_publish_read_only(publish_file, True):
                    return
            else:
                return
        elif not work_file:
            # just open the published file:
            if not self._do_open_publish_as_workfile(publish_file, next_version):
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
        if publish_file and work_file.compare_with_publish(publish_file) < 0:

            # options are different if the publish and work files are the same path as there
            # doesn't need to be the option of opening the publish read-only.
            publish_requires_copy = True
            if self._publish_template == self._work_template:
                if "version" not in self._publish_template.keys:
                    publish_requires_copy = False
            
            next_version = self._get_next_available_version(work_file.path, publish_file.publish_path)
            
            form = OpenFileForm(self._app, work_file, publish_file, OpenFileForm.OPEN_WORKFILE_MODE, 
                                next_version, publish_requires_copy)
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
        if self._do_open_publish_read_only(file, False):
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

        if self._do_copy_and_open(None, file.path, file.version, False, new_ctx):
            # close work files UI:
            self._workfiles_ui.close()
        
    def _do_open_workfile(self, file):
        """
        Handles opening a work file - this checks to see if the file
        is in another users sandbox before opening        
        """
        if not file or not file.is_local:
            return False

        if not file.editable:
            answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file read-only?",
                                                ("The work file you are opening: '%s', is "
                                                "read-only:\n\n%s.\n\nWould you like to continue?" 
                                                % (file.name, file.not_editable_reason)), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
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
                                           ("Failed to resolve the user sandbox file path:\n\n%s\n\nto the local "
                                           "path:\n\n%s\n\nUnable to open file!" % (work_path, e)))
                    self._app.log_exception("Failed to resolve user sandbox file path %s" % work_path)
                    return False
        
                if local_path != work_path:
                    # more than just an open so prompt user to confirm:
                    #TODO: replace with tank dialog
                    answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file from another user?",
                                                        ("The work file you are opening:\n\n%s\n\n"
                                                        "is in a user sandbox belonging to %s.  Would "
                                                        "you like to copy the file to your sandbox and open it?" 
                                                        % (work_path, wp_ctx.user["name"])), 
                                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                    if answer == QtGui.QMessageBox.Cancel:
                        return False

                    src_path = work_path
                    work_path = local_path      
                    
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  

        return self._do_copy_and_open(src_path, work_path, None, not file.editable, new_ctx)
        
    def _do_open_publish_as_workfile(self, file, new_version):
        """
        Open the published file - this will construct a new work path from the 
        work template and the publish fields before copying it and opening it 
        as a new work file
        """
        if not file or not file.is_published:
            return False

        if not file.editable:
            answer = QtGui.QMessageBox.question(self._workfiles_ui, "Open file read-only?",
                                                ("The published file you are opening: '%s', is "
                                                "read-only:\n\n%s.\n\nWould you like to continue?" 
                                                % (file.name, file.not_editable_reason)), 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
                return False

        # trying to open a publish:
        work_path = None
        src_path = file.publish_path
        
        # early check to see if the publish path & work path will actually be different:
        if self._publish_template == self._work_template and "version" not in self._publish_template.keys:
            # assume that the work and publish paths will actally be the same!
            work_path = src_path        
        else:
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
                fields["version"] = new_version
                
                # construct work path:
                work_path = self._work_template.apply_fields(fields)
            except Exception, e:
                QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to get work file path", 
                                       ("Failed to resolve work file path from publish path:\n\n%s\n\n%s\n\n"
                                       "Unable to open file!" % (src_path, e)))
                self._app.log_exception("Failed to resolve work file path from publish path: %s" % src_path)
                return False

        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))
        
        return self._do_copy_and_open(src_path, work_path, None, not file.editable, new_ctx)
        
    def _do_open_publish_read_only(self, file, is_latest):
        """
        Open a previous version of a publish file from the publish 
        area - this just opens it directly without any file copying 
        or validation
        """
        # get best context we can for file:
        ctx_entity = file.task or file.entity or self._context.project
        new_ctx = self._app.tank.context_from_entity(ctx_entity.get("type"), ctx_entity.get("id"))  
        
        return self._do_copy_and_open(None, file.publish_path, file.version if is_latest else None, True, new_ctx)
        
    def _do_copy_and_open(self, src_path, work_path, version, read_only, new_ctx):
        """
        Copies src_path to work_path, creates folders, restarts the engine and then opens 
        the file from work_path
        
        :param src_path:    The path of the file to copy
        :param work_path:   The destination work file path
        :param version:     The version of the work file to be opened
        :param read_only:   True if the work file should be opened read-only
        :param new_ctx:     The context that the work file should be opened in
        :returns:           True of the source file is copied and successfully opened
        """
        if not work_path or not new_ctx:
            # can't do anything!
            return False
           
        if src_path and src_path != work_path:
            # check that the source path exists:        
            if not os.path.exists(src_path):
                QtGui.QMessageBox.critical(self._workfiles_ui, "File doesn't exist!", 
                                           "The file\n\n%s\n\nCould not be found to open!" % src_path)
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
        if src_path and src_path != work_path:
            # check that local path doesn't already exist:
            if os.path.exists(work_path):
                #TODO: replace with tank dialog
                answer = QtGui.QMessageBox.question(self._workfiles_ui, "Overwrite file?",
                                "The file\n\n%s\n\nalready exists.  Would you like to overwrite it?" % (work_path), 
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return False
                
            try:
                # make sure that the folder exists - this will handle any leaf folders that aren't
                # created by Toolkit (e.g. a dynamic static folder that isn't part of the schema)
                work_dir = os.path.dirname(work_path)
                self._app.ensure_folder_exists(work_dir)
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
            open_file(self._app, OPEN_FILE_ACTION, self._context, work_path, version, read_only)
        except Exception, e:
            QtGui.QMessageBox.critical(self._workfiles_ui, "Failed to open file", 
                                       "Failed to open file\n\n%s\n\n%s" % (work_path, e))
            self._app.log_exception("Failed to open file %s!" % work_path)    
            return False
        
        return True

    def _get_next_available_version(self, work_path, publish_path):
        """
        Get the next available version number for the specified work and/or publish
        paths.  This is the version number that should be used for the next version
        of the file.

        :param work_path:       The path of the work file to use
        :param publish_path:    The path of the publish file to use
        :returns:               The next available version number
        """
        # First extract a set of fields - prefer work path if we have one:
        fields = {}
        if work_path:
            fields = self._work_template.get_fields(work_path)
        else:
            fields = self._publish_template.get_fields(publish_path)
       
        # Add in the context fields for the work template - this ensures that the user is correct
        # if the file is in a user sandbox:
        ctx_fields = self._context.as_template_fields(self._work_template)
        fields.update(ctx_fields)
        
        # build unique key to use when searching for existing files:
        file_key = FileItem.build_file_key(fields, self._work_template, 
                                           self.__version_compare_ignore_fields + ["version"])
        
        # find all files that match the file key:
        finder = FileFinder(self._app, self._user_cache)
        found_files = finder.find_files(self._work_template, self._publish_template, self._context, file_key)
        
        # find highest file version out of all files returned:
        versions = [f.version for f in found_files]
        return (max(versions) if versions else 0) + 1

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
            context_and_flags = self.select_work_area(SelectWorkAreaForm.CHANGE_WORK_AREA if enable_start_new 
                                                      else SelectWorkAreaForm.CHANGE_WORK_AREA_NO_NEW)
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
        
        # ensure our local path cache is up to date
        self._app.log_debug("Synchronizing remote path cache...")
        self._app.sgtk.synchronize_filesystem_structure()
        self._app.log_debug("Path cache up to date!")
            
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
            QtGui.QMessageBox.critical(self._workfiles_ui,
                                       "Could not Change Work Area!",
                                       "Could not change work area and start a new "
                                       "engine. This may be because the task doesn't "
                                       "have a step. Details: %s" % e)
            return False
        return True
    
    def get_file_filters(self):
        """
        Return a list of filters to be presented in the UI.  The selected
        filter is passed to the find files method along with the selected
        work area/context.
        """
        filters = []

        current_user = tank.util.get_current_user(self._app.tank)
        
        # always add workfiles filter:
        filters.append(FileFilter({"menu_label":"Show Files in my Work Area", 
                        "list_title":"Available Work Files",
                        "show_in_file_system":True,
                        "user":current_user,
                        "mode":FileFilter.WORKFILES_MODE}))
        
        # always add publishes filter:
        filters.append(FileFilter({"menu_label":"Show Files in the Publish Area", 
                        "list_title":"Available Publishes",
                        "show_in_file_system":self._publish_area_template != None,
                        "mode":FileFilter.PUBLISHES_MODE}))
      
        # add user sandbox filters:
        users = self._get_usersandbox_users()
        if users:
            filters.append("separator")
            
            for user in users:
                if current_user is not None and user["id"] == current_user["id"]:
                    continue
                
                filters.append(FileFilter({"menu_label":"Show Files in %s's Work Area" % user["name"],
                                "list_title":"%s's Work Files" % user["name"],
                                "show_in_file_system":True,
                                "user":user,
                                "mode":FileFilter.WORKFILES_MODE}))
            
        return filters
    
    def _get_usersandbox_users(self):
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
        
        # from paths, find a unique list of user ids:
        user_ids = set()
        for path in work_area_paths:
            # to find the user, we have to construct a context
            # from the path and then inspect the user from this
            path_ctx = self._app.tank.context_from_path(path)
            user = path_ctx.user
            if user: 
                user_ids.add(user["id"])
        
        # look these up in the user cache:
        user_details = self._user_cache.get_user_details_for_ids(user_ids)
        
        # return all valid user details:
        return [details for details in user_details.values() if details]
        
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
