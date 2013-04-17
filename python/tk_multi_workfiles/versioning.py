"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os

import tank
from tank import TankError
from tank.platform.qt import QtCore, QtGui 

from .wrapper_dialog import WrapperDialog

from .async_worker import AsyncWorker

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
        # validate that scene is actually a work file with a version:
        try:
            if not self._work_template:
                raise TankError("Work template is invalid")
            
            work_path = self._get_current_file_path()
            current_version = self.get_work_file_version(work_path)
        except TankError, e:
            # TODO: change to tank dialog
            msg = ("Failed to get a version for the current work file:\n\n"
                  "%s\n\n"
                  "Unable to change version!" % e)
            QtGui.QMessageBox.information(None, "Change Version Error!", msg)
            return
        except Exception, e:
            self._app.log_exception("Failed to get a version for the current work file")
            return
        
        # initial new version:
        # TODO: do something more clever here?
        new_version = current_version + 1
        
        worker_cb = lambda v, wp=work_path: self.check_version_availability(wp, v)
        with AsyncWorker(worker_cb) as version_checker:
            while True:
                # show modal dialog:
                from .change_version_form import ChangeVersionForm
                #(res, form) = self._app.engine.show_modal("Change Version", self._app, ChangeVersionForm, version_checker, current_version, new_version)
                form = ChangeVersionForm(version_checker, current_version, new_version)
                with WrapperDialog(form, "Change Version", form.geometry().size()) as dlg:
                    res = dlg.exec_()
                    
                    if res == QtGui.QDialog.Accepted:
                        # get new version:
                        new_version = form.new_version
                        
                        # validate:
                        msg = self.check_version_availability(work_path, new_version)
                        if msg:
                            msg = "<b>Warning: %s<b><br><br>Are you sure you want to change to this version?" % msg
                            res = QtGui.QMessageBox.question(None, "Confirm", msg, QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
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
            
    def get_work_file_version(self, work_path):
        """
        Get the current work file version:
        """
        # use the work template to extract the version:
        fields = self._work_template.get_fields(work_path)
        current_version = fields.get("version")
        
        return current_version
            
    def get_max_workfile_version(self, fields):
        """
        
        """
        work_area_paths = self._app.tank.paths_from_template(self._work_template, fields, ["version"])
        existing_work_versions = [self._work_template.get_fields(p).get("version") for p in work_area_paths]
        max_work_version = max(existing_work_versions) if existing_work_versions else None
        return max_work_version
    
    def get_max_publish_version(self, name):
        """
        
        """
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
                    
    def check_version_availability(self, work_path, version):
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
        
        # check to see if a publish of that version already exists:
        # TODO: do we need to add anything to fields?
        publish_file = self._publish_template.apply_fields(fields)
        matches = tank.util.find_publish(self._app.tank, [publish_file])
        if matches:
            return "Published file already exists for version v%03d - changing to this version will mean you are shadowing existing work!" % version
    
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
        
        
        
        
        
        
        
        
        