# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui 
from sgtk import TankError

from .file_item import FileItem
from .wrapper_dialog import WrapperDialog

#from .users import UserCache
from .actions.save_as_file_action import SaveAsFileAction

class WorkFiles(QtCore.QObject):#object):

    @staticmethod
    def show_file_open_dlg():
        """
        """
        app = sgtk.platform.current_bundle()
        handler = WorkFiles(app)
        handler.__show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        """
        app = sgtk.platform.current_bundle()
        handler = WorkFiles(app)
        handler._show_file_save_dlg()

    def __init__(self, app):
        """
        Construction
        """
        QtCore.QObject.__init__(self, None)
        self._app = app

    def __show_file_open_dlg(self):
        """
        """
        try:
            from .file_open_form import FileOpenForm
            res, file_open_ui = self._app.engine.show_modal("File Open", self._app, FileOpenForm, 
                                                            self._init_file_open_form)
        except:
            self._app.log_exception("Failed to create File Open dialog!")
            return
    
    def _init_file_open_form(self, form):
        """
        """
        form.perform_action.connect(self._on_file_open_perform_action)
        form.create_new_task.connect(self._on_create_new_task)

    def _show_file_save_dlg(self):
        """
        """
        try:
            from .file_save_form import FileSaveForm
            
            while True:
                res, file_save_ui = self._app.engine.show_modal("File Save", self._app, FileSaveForm,
                                                                self._init_file_save_form)
                if res == QtGui.QDialog.Accepted:
                    # great - we can save the file:
                    new_path = file_save_ui.path
                    env = file_save_ui.environment

                    try:
                        action = SaveAsFileAction()
                        file = FileItem(new_path, None, True, False, None, {})
                        #print "Saving As %s" % new_path 
                        action.execute(file, None, env, None)
                        #self.save_as(new_path)
                    except Exception, e:
                        QtGui.QMessageBox.critical(None, "Failed to save file!", "Failed to save file:\n\n%s" % e)
                        self._app.log_exception("Something went wrong while saving!")
                
                # all done!
                break
        except:
            self._app.log_exception("Failed to create File Save dialog!")
            return

    def _init_file_save_form(self, form):
        """
        """
        # create models needed by the form:
        form.create_new_task.connect(self._on_create_new_task)
        
        
    def _on_file_open_perform_action(self, action, file, file_versions, environment):
        """
        """
        if not action:
            return
        
        # get the file open form from the sender:
        form = self.sender()
        
        # some debug:
        if file:
            self._app.log_debug("Performing action '%s' on file '%s, v%03d'" % (action.label, file.name, file.version))
        else:
            self._app.log_debug("Performing action '%s'" % action.label)
            
        # execute the action:
        close_dialog = action.execute(file, file_versions, environment, form)
        
        # if this is successful then close the form:
        if close_dialog and form:
            form.close() 
    
    def _on_create_new_task(self, event):
        """
        """
        event.task_created = self._create_new_task(event.entity, event.step)
        
    def _create_new_task(self, current_entity, current_step):
        """
        """
        if not current_entity:
            return False
        
        parent_form = self.sender()
        
        # get the current user:
        current_user = sgtk.util.get_current_user(self._app.sgtk)

        # show new task dialog:
        from .new_task_form import NewTaskForm
        new_task_form = NewTaskForm(current_entity, current_step, current_user)
        
        res = WrapperDialog.show_modal(new_task_form, "Create New Task", parent=parent_form)
        if res != QtGui.QDialog.Accepted:
            return False
        
        # get details from new_task_form:
        entity = new_task_form.entity
        assigned_to = new_task_form.assigned_to
        pipeline_step = new_task_form.pipeline_step
        task_name = new_task_form.task_name
    
        # create the task:    
        new_task = None
        try:
            new_task = self.create_new_task(task_name, pipeline_step, entity, assigned_to)
        except TankError, e:
            QtGui.QMessageBox.warning(parent_ui,
                                  "Failed to create new task!",
                                  ("Failed to create a new task '%s' for pipeline step '%s' on entity '%s %s':\n\n%s" 
                                   % (task_name, pipeline_step.get("code"), entity["type"], entity["code"], e)))
            return False

        # build folders for this new task - we have to do this to ensure
        # that files found during the search are matched to the correct task
        # TODO
        
        # trigger a refresh of all views in the form:
        #parent_form.refresh_all_async()
        return new_task != None


    #def _get_usersandbox_users(self):
    #    """
    #    Find all available user sandbox users for the 
    #    current work area.
    #    """
    #    if not self._work_area_template:
    #        return
    #    
    #    # find 'user' keys to skip when looking for sandboxes:
    #    user_keys = ["HumanUser"]
    #    for key in self._work_area_template.keys.values():
    #        if key.shotgun_entity_type == "HumanUser":
    #            user_keys.append(key.name)
    #    
    #    # use the fields for the current context to get a list of work area paths:
    #    self._app.log_debug("Searching for user sandbox paths skipping keys: %s" % user_keys)
    #    
    #    try:
    #        fields = self._context.as_template_fields(self._work_area_template)
    #    except TankError:
    #        # fields could not be resolved from the context! This can happen because
    #        # the context does not have any structure on disk / path cache but is a 
    #        # "shotgun-only" context which was created from for example a task.
    #        work_area_paths = []
    #    else:
    #        # got our fields. Now get the paths.
    #        work_area_paths = self._app.sgtk.paths_from_template(self._work_area_template, fields, user_keys)
    #    
    #    # from paths, find a unique list of user ids:
    #    user_ids = set()
    #    for path in work_area_paths:
    #        # to find the user, we have to construct a context
    #        # from the path and then inspect the user from this
    #        path_ctx = self._app.sgtk.context_from_path(path)
    #        user = path_ctx.user
    #        if user: 
    #            user_ids.add(user["id"])
    #    
    #    # look these up in the user cache:
    #    user_details = self._user_cache.get_user_details_for_ids(user_ids)
    #    
    #    # return all valid user details:
    #    return [details for details in user_details.values() if details]

