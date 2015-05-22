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

class WorkFiles(QtCore.QObject):

    @staticmethod
    def show_file_open_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_save_dlg()

    def __init__(self):
        """
        Construction
        """
        QtCore.QObject.__init__(self, None)

    def _show_file_open_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_open_form import FileOpenForm
            res, file_open_ui = app.engine.show_modal("File Open", app, FileOpenForm)
        except:
            app.log_exception("Failed to create File Open dialog!")
            return

    def _show_file_save_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_save_form import FileSaveForm
            res, file_save_ui = app.engine.show_modal("File Save", app, FileSaveForm)
        except:
            app.log_exception("Failed to create File Save dialog!")
            return




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

