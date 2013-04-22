"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os

import tank
from tank import TankError
from tank.platform.qt import QtCore, QtGui 

from .wrapper_dialog import WrapperDialog

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
        
    def _show_change_version_dlg(self):
        """
        Show the change version dialog
        """
        try:
            work_path = self._get_current_file_path()
        except Exception, e:
            msg = ("Failed to get the current file path:\n\n"
                  "%s\n\n"
                  "Unable to continue!" % e)
            QtGui.QMessageBox.critical(None, "Change Version Error!", msg)
            return
        
        if not work_path or not self._work_template.validate(work_path):
            msg = ("Unable to Change Version!\n\nPlease save the scene as a valid work file before continuing")
            QtGui.QMessageBox.information(None, "Unable To Change Version!", msg)
            return
        
        # use work template to get current version:
        fields = self._work_template.get_fields(work_path)
        current_version = fields.get("version")
        
        # get next available version:
        new_version = self.get_max_workfile_version(fields)
        
        while True:
            # show modal dialog:
            from .change_version_form import ChangeVersionForm
            form = ChangeVersionForm(current_version, new_version)
            with WrapperDialog(form, "Change Version", form.geometry().size()) as dlg:
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
                    except TankError, e:
                        QtGui.QMessageBox.critical(None, "Failure", "Version up of scene failed!\n\n%s" % e)
                        continue
                    except Exception, e:
                        self._app.log_exception("Something went wrong while changing the version!")
                        continue

                    break
                else:                 
                    break
            
    def get_next_available_version(self, fields):
        """
        Get the next available version
        """
        max_work_version = self.get_max_workfile_version(fields)
        max_publish_version = self.get_max_publish_version(fields.get("name"))
        return max(max_work_version, max_publish_version) + 1
            
    def get_max_workfile_version(self, fields):
        """
        Get the current highest version of the work file that
        is generated using the current work template and the
        specified fields
        """
        work_area_paths = self._app.tank.paths_from_template(self._work_template, fields, ["version"])
        existing_work_versions = [self._work_template.get_fields(p).get("version") for p in work_area_paths]
        max_work_version = max(existing_work_versions) if existing_work_versions else None
        return max_work_version
    
    def get_max_publish_version(self, name):
        """
        Get the current highest publish version using the current
        context and the specified 'name' field.
        """
        # TODO - change this to do a simpler query as it only needs to return a
        # version number!
        
        publish_paths = self._get_published_file_paths_for_context(self._context)
        existing_publish_versions = []
        for p in publish_paths:
            if not self._publish_template.validate(p):
                continue

            # only care about published files that match 
            # the template and have the new name
            publish_fields = self._publish_template.get_fields(p)
            if publish_fields.get("name") == name:
                existing_publish_versions.append(publish_fields.get("version"))

        max_publish_version = max(existing_publish_versions) if existing_publish_versions else None
        return max_publish_version
                    
    def _check_version_availability(self, work_path, version):
        """
        Check to see if the specified version is already in use
        either as a work file or as a publish
        
        Note: this doesn't check for user sandboxes atm
        """
        if version == None or version < 0:
            return "'%d' is not a valid version number!" % version 
        
        # get fields for work file path:
        fields = self._work_template.get_fields(work_path)
        
        # check that version is actually different:
        if fields["version"] == version:
            return "The current work file is already version v%03d" % version

        # check to see if a work file of that version exists:        
        fields["version"] = version
        new_work_file = self._work_template.apply_fields(fields)
        if os.path.exists(new_work_file):
            return "Work file already exists for version v%03d - changing to this version will overwrite the existing file!" % version
    
    def change_work_file_version(self, work_path, new_version):
        """
        Change the current work file version
        """
        # update version and get new path:
        fields = self._work_template.get_fields(work_path)
        current_version = fields["version"]
        fields["version"] = new_version
        new_work_file = self._work_template.apply_fields(fields)
        
        # do save-as:
        self._save_current_file_as(new_work_file)
        
    def _save_current_file_as(self, path):
        """
        Use hook to get the current work/scene file path
        """
        self._app.execute_hook("hook_scene_operation", operation="save_as", file_path=path)
        
    def _get_current_file_path(self):
        """
        Use hook to get the current work/scene file path
        """
        return self._app.execute_hook("hook_scene_operation", operation="current_path", file_path="")
        
    def _get_published_file_paths_for_context(self, ctx):
        """
        Get list of published files for the current context
        """
        
        filters = [["entity", "is", ctx.entity]]
        if ctx.task:
            filters.append(["task", "is", ctx.task])
        
        sg_result = self._app.shotgun.find("TankPublishedFile", filters, ["path"])
        publish_paths = [r.get("path").get("local_path") for r in sg_result]
 
        return publish_paths          
        
        
        
        
        
        
        
        
        