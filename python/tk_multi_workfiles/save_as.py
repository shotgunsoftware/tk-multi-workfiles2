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
from itertools import chain

import tank
from tank.platform.qt import QtCore, QtGui 
from tank import TankError

from .async_worker import AsyncWorker
from .scene_operation import get_current_path, save_file, SAVE_FILE_AS_ACTION
from .find_files import FileFinder
from .file_item import FileItem

class SaveAs(object):
    """
    Functionality for performing Shotgun Save-As operations on the current scene.  This contains
    commands that will show the Save-As UI as well as the commands that can be used to perform
    the save operation.    
    """
    
    @staticmethod
    def show_save_as_dlg(app):
        """
        Show the save-as dialog
        
        :param app: The instance of the workfiles app that this method is called from/for      
        """
        handler = SaveAs(app)
        handler._show_save_as_dlg()
        
    def __init__(self, app):
        """
        Construction
        """
        self._app = app
        
        self._work_template = self._app.get_template("template_work")
        self._publish_template = self._app.get_template("template_publish")
        
        self._cached_files = None
        
        # cache any fields that should be ignored when looking for work files:
        self.__version_compare_ignore_fields = self._app.get_setting("version_compare_ignore_fields", [])
        
    def _show_save_as_dlg(self):
        """
        Show the save as dialog
        """
        # get the current file path:
        try:
            current_path = get_current_path(self._app, SAVE_FILE_AS_ACTION, self._app.context)
        except Exception, e:
            msg = ("Failed to get the current file path:\n\n"
                  "%s\n\n"
                  "Unable to continue!" % e)
            QtGui.QMessageBox.critical(None, "Save As Error!", msg)
            self._app.log_exception("Failed to get the current file path")
            return
        
        # determine if this is a publish path or not:
        is_publish = self._publish_template.validate(current_path) and self._publish_template != self._work_template
        
        # see if name is used in the work template:
        name_is_used = "name" in self._work_template.keys
        name_is_optional = name_is_used and self._work_template.is_optional("name")

        # see if version is used in the work template:
        version_is_used = "version" in self._work_template.keys
        
        # update some initial info:        
        title = "Save to Work Area" if is_publish else "Shotgun Save As"
        name = ""
        if name_is_used:
            if is_publish:
                fields = self._publish_template.get_fields(current_path)
                name = fields.get("name")
            else:
                # get the default name from settings:
                default_name = self._app.get_setting("saveas_default_name")
                if not default_name and not name_is_optional:
                    # name isn't optional so we should use something:
                    default_name = "scene"

                # determine the initial name depending on the current path:
                fields = {}
                if self._work_template.validate(current_path):
                    fields = self._work_template.get_fields(current_path)
                    name = fields.get("name")
                    if not name and not name_is_optional:
                        name = default_name
                else:
                    fields = self._app.context.as_template_fields(self._work_template)
                    name = default_name
                
                # see if versioning up is preferred - if it is then the version will be incremented instead
                # of appending/incrementing a number as a suffix on the name if a file with the same name
                # already exists.
                prefer_version_up = version_is_used and self._app.get_setting("saveas_prefer_version_up")
                
                if name and not prefer_version_up:
                    # default is to not version-up so lets make sure we
                    # at least start with a unique name!

                    try:
                        # make sure the work file name doesn't already exist:
                        # note, this could potentially be slow so for now lets
                        # limit it:

                        # split name into alpha and numeric parts so that we can 
                        # increment the numeric part in order to find a unique name
                        name_alpha = name.rstrip("0123456789")
                        name_num_str = name[len(name_alpha):] or "0"
                        name_num = int(name_num_str)
                        name_format_str = "%s%%0%dd" % (name_alpha, len(name_num_str))
                    
                        counter_limit = 10
                        for counter in range(0, counter_limit):
                            test_name = name
                            if counter > 0:
                                # build new name
                                test_name = name_format_str % (name_num+counter)
                        
                            test_fields = fields.copy()
                            test_fields["name"] = test_name
                        
                            existing_files = self._app.tank.paths_from_template(self._work_template, test_fields, ["version"])
                            if not existing_files:
                                name = test_name
                                break
                        
                    except TankError, e:
                        # this shouldn't be fatal so just log a debug message:
                        self._app.log_debug("Warning - failed to find a default name for Shotgun Save-As: %s" % e)
                
        worker_cb = (lambda details, wp=current_path, ip=is_publish: 
                            self.generate_new_work_file_path(wp, ip, details.get("name"), details.get("reset_version")))
        try:
            preview_updater = AsyncWorker(worker_cb)
            preview_updater.start()
            while True:
                # reset cached files just in case something has changed:
                self._cached_files = None
                
                # show modal dialog:
                from .save_as_form import SaveAsForm
                (res, form) = self._app.engine.show_modal(title, self._app, SaveAsForm, preview_updater, 
                                                          is_publish, name_is_used, name, version_is_used)
                print "RES: %s" % res
                
                if res == QtGui.QDialog.Accepted:
                    # get details from UI:
                    name = form.name
                    reset_version = form.reset_version
                    
                    details = self.generate_new_work_file_path(current_path, is_publish, name, reset_version)
                    new_path = details.get("path")
                    msg = details.get("message")
                    
                    if not new_path:
                        # something went wrong!
                        QtGui.QMessageBox.information(None, "Unable to Save", "Unable to Save!\n\n%s" % msg)
                        continue
                     
                    # ok, so do save-as:
                    try:
                        self.save_as(new_path)
                    except Exception, e:
                        QtGui.QMessageBox.critical(None, "Failed to save file!", "Failed to save file:\n\n%s" % msg)
                        self._app.log_exception("Something went wrong while saving!")
                
                # ok, all done or cancelled        
                break
        finally:
            preview_updater.stop()
        
    def save_as(self, new_path):
        """
        Do actual save-as of the current scene as the new path - assumes all validity checking has already
        been done
        
        :param new_path:    The new path to save the current script/scene to
        """
        # we used to always create folders but this seems unnecessary as the folders should have been
        # created when the work area was set - either as part of the launch process or when switching
        # work area within the app.
        # To be on the safe side though, we'll check if the directory that the file is being saved in
        # to exists and run create folders if it doesn't - this covers any potential edge cases where
        # the Work area has been set without folder creation being run correctly.
        dir = os.path.dirname(new_path)
        if not dir or not os.path.exists(dir):
            # work files always operates in some sort of context, either project, entity or task
            ctx_entity = self._app.context.task or self._app.context.entity or self._app.context.project
            self._app.log_debug("Creating folders for context %s" % self._app.context)
            self._app.tank.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"))
            # finally, make sure that the folder exists - this will handle any leaf folders that aren't
            # created above (e.g. a dynamic static folder that isn't part of the schema)
            self._app.ensure_folder_exists(dir)
        
        # and save the current file as the new path:
        save_file(self._app, SAVE_FILE_AS_ACTION, self._app.context, new_path)
        
    def generate_new_work_file_path(self, current_path, current_is_publish, new_name, reset_version):
        """
        Generate a new work file path from the current path taking into
        account existing work files and publishes.
        """
        new_work_path = ""
        msg = None
        can_reset_version = False

        has_name_field = "name" in self._work_template.keys
        has_version_field = "version" in self._work_template.keys

        # validate name:
        if has_name_field:
            if not self._work_template.is_optional("name") and not new_name:
                msg = "You must enter a name!"
                return {"message":msg}

            if new_name and not self._work_template.keys["name"].validate(new_name):
                msg = "Your filename contains illegal characters!"
                return {"message":msg}

        # build fields dictionary to use for the new path:
        fields = {}

        # start with fields from context:
        fields = self._app.context.as_template_fields(self._work_template)

        # add in any additional fields from current path:
        base_template = self._publish_template if current_is_publish else self._work_template
        if base_template.validate(current_path):
            template_fields = base_template.get_fields(current_path)
            fields = dict(chain(template_fields.iteritems(), fields.iteritems()))
        else:
            if has_version_field:
                # just make sure there is a version
                fields["version"] = 1

        # keep track of the current name:
        current_name = fields.get("name")

        # update name field:
        if new_name:
            fields["name"] = new_name
        else:
            # clear the current name:
            if "name" in fields:
                del fields["name"]

        # if we haven't cached the file list already, do it now:
        if not self._cached_files:
            finder = FileFinder(self._app)
            self._cached_files = finder.find_files(self._work_template, self._publish_template, self._app.context)

        # construct a file key that represents all versions of this publish/work file:
        file_key = FileItem.build_file_key(fields, self._work_template, 
                                           self.__version_compare_ignore_fields + ["version"])

        # find the max work file and publish versions:        
        work_versions = [f.version for f in self._cached_files if f.is_local and f.key == file_key]
        max_work_version = max(work_versions) if work_versions else 0
        publish_versions = [f.version for f in self._cached_files if f.is_published and f.key == file_key]
        max_publish_version = max(publish_versions) if publish_versions else 0
        max_version = max(max_work_version, max_publish_version)
        
        if has_version_field:
            # get the current version:
            current_version = fields.get("version")
            
            # now depending on what the source was 
            # and if the name has been changed:
            new_version = None
            if current_is_publish and ((not has_name_field) or new_name == current_name):
                # we're ok to just copy publish across and version up
                can_reset_version = False
                new_version = max_version + 1 if max_version else 1
                msg = None
            else:
                if max_version:
                    # already have a publish and/or work file
                    can_reset_version = False
                    new_version = max_version + 1
                    
                    if max_work_version > max_publish_version:
                        if has_name_field:
                            msg = ("A work file with this name already exists.  If you proceed, your file "
                                   "will use the next available version number.")
                        else:
                            msg = ("A previous version of this work file already exists.  If you proceed, "
                                   "your file will use the next available version number.")
    
                    else:
                        if has_name_field:
                            msg = ("A publish file with this name already exists.  If you proceed, your file "
                                   "will use the next available version number.")
                        else:
                            msg = ("A published version of this file already exists.  If you proceed, "
                                   "your file will use the next available version number.")
                        
                else:
                    # don't have an existing version
                    can_reset_version = True
                    msg = ""
                    if reset_version:
                        new_version = 1
                        
            if new_version:
                fields["version"] = new_version

        else:
            # handle when version isn't in the work template:
            if max_work_version > 0 and max_work_version >= max_publish_version:
                msg = "A file with this name already exists.  If you proceed, the existing file will be overwritten."
            elif max_publish_version:
                msg = "A published version of this file already exists."
                
        # create the new path                
        new_work_path = self._work_template.apply_fields(fields)
        
        return {"path":new_work_path, "message":msg, "can_reset_version":can_reset_version}

    
