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
import copy
from itertools import chain

import tank
from tank import TankError
from tank.platform.qt import QtCore, QtGui 

from .wrapper_dialog import WrapperDialog
from .scene_operation import get_current_path, save_file, VERSION_UP_FILE_ACTION


class Versioning(object):
    """
    Main versioning functionality
    """
    @staticmethod
    def show_change_version_dlg(app):
        """
        Help method to show a dialog allowing the user to 
        change the version of the current work file        
        """
        handler = Versioning(app)
        handler._show_change_version_dlg()
        
    def __init__(self, app, work_template=None, publish_template=None, context=None):
        """
        Construction
        """
        self._app = app
        self._work_template = work_template if work_template else self._app.get_template("template_work")
        self._publish_template = publish_template if publish_template else self._app.get_template("template_publish")
        self._context = context if context else self._app.context

        # cache any fields that should be ignored when looking for work files:
        self._version_compare_ignore_fields = self._app.get_setting("version_compare_ignore_fields", [])
        
    def change_work_file_version(self, work_path, new_version):
        """
        Change the current work file version
        
        :param work_path:    The file path of the work file to change the version of
        :param new_version:  The new version for the work file
        """
        if not "version" in self._work_template.keys:
            raise TankError("Work template does not contain a version key - unable to change version!")
        
        # update version and get new path:
        ctx_fields = self._app.context.as_template_fields(self._work_template)
        current_fields = self._work_template.get_fields(work_path)
        fields = dict(chain(current_fields.iteritems(), ctx_fields.iteritems()))
        fields["version"] = new_version
        new_work_file = self._work_template.apply_fields(fields)
        
        # do save:
        save_file(self._app, VERSION_UP_FILE_ACTION, self._app.context, new_work_file)        
        
    def _show_change_version_dlg(self):
        """
        Show the change version dialog
        """
        try:
            work_path = get_current_path(self._app, VERSION_UP_FILE_ACTION, self._app.context) 
        except Exception, e:
            msg = ("Failed to get the current file path:\n\n"
                  "%s\n\n"
                  "Unable to continue!" % e)
            QtGui.QMessageBox.critical(None, "Change Version Error!", msg)
            self._app.log_exception("Failed to get the current file path!")
            return

        if not work_path or not self._work_template.validate(work_path):
            msg = ("Unable to Change Version!\n\nPlease save the scene as a valid work file before continuing")
            QtGui.QMessageBox.information(None, "Unable To Change Version!", msg)
            return

        if not "version" in self._work_template.keys:
            raise TankError("Work template does not contain a version key - unable to change version!")
        
        # use work template to get current version:
        fields = self._work_template.get_fields(work_path)
        current_version = fields.get("version")
        
        # get next available version:
        new_version = self._get_max_workfile_version(fields)+1
        
        while True:
            # show modal dialog:
            from .change_version_form import ChangeVersionForm
            form = ChangeVersionForm(current_version, new_version)
            try:
                dlg = WrapperDialog(form, "Change Version", form.geometry().size())
                res = dlg.exec_()
                
                if res == QtGui.QDialog.Accepted:
                    # get new version:
                    new_version = form.new_version
                    
                    if new_version == current_version:
                        QtGui.QMessageBox.information(None, "Version Error", "The new version (v%03d) must be different to the current version!" % new_version)
                        continue
                    
                    # validate:
                    msg = self._check_version_availability(work_path, new_version)
                    if msg:
                        msg = "<b>Warning: %s<b><br><br>Are you sure you want to change to this version?" % msg
                        res = QtGui.QMessageBox.question(None, "Confirm", msg, 
                                                         QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                         QtGui.QMessageBox.No)
                        if res == QtGui.QMessageBox.No:
                            continue
                        elif res == QtGui.QMessageBox.Cancel:
                            break
                        
                    # ok, so change version:
                    try:
                        self.change_work_file_version(work_path, new_version)
                    except Exception, e:
                        QtGui.QMessageBox.critical(None, "Failure", "Version up of scene failed!\n\n%s" % e)
                        self._app.log_exception("Something went wrong while changing the version!")
                        continue

                    break
                else:                 
                    break
            finally:
                dlg.clean_up()
            
    def _find_workfile_versions(self, fields):
        """
        Find all version numbers for all work files that match the specified fields.
        
        :param fields:    Dictionary of fields to be used when searching for work files
        :returns:         List of all version numbers found for matching work files
        """
        # find workfiles that match the specified fields:
        work_area_paths = self._app.tank.paths_from_template(self._work_template, 
                                                             fields,
                                                             self._version_compare_ignore_fields + ["version"])
        # and find all versions for these files:
        all_versions = [self._work_template.get_fields(p).get("version") for p in work_area_paths]
        return all_versions
            
    def _get_max_workfile_version(self, fields):
        """
        Get the current highest version of the work file that is generated using the current 
        work template and the specified fields
        
        :param fields:    Dictionary of fields to be used when searching for work files
        :returns:         The maximum version found for all matching work files
        """
        existing_work_versions = self._find_workfile_versions(fields)
        return max(existing_work_versions) if existing_work_versions else None
                    
    def _check_version_availability(self, work_path, version):
        """
        Check to see if there is already a work file with the specified version Note: this 
        doesn't check for user sandboxes atm
        
        :param work_path:    The work file path to check
        :param version:      The new version to check for
        :returns:            Warning/error message if the specified version of the work file already
                             exists, otherwise None
        """
        if version == None or version < 0:
            return "'%d' is not a valid version number!" % version 
        
        # get fields for work file path:
        fields = self._work_template.get_fields(work_path)
        
        # check that version is actually different:
        if fields["version"] == version:
            return "The current work file is already version v%03d" % version

        # check to see if a work file of that version exists:
        all_versions = self._find_workfile_versions(fields)
        if all_versions and version in all_versions:        
            return ("Work file already exists for version v%03d - "
                    "changing to this version will overwrite the existing file!" % version)
