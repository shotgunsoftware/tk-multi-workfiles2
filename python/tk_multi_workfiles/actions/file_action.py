# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""
import os

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore
from .action import Action

class FileAction(Action):
    """
    """
    @staticmethod
    def create_folders(ctx):
        """
        Create folders for specified context
        """
        app = sgtk.platform.current_bundle()
        app.log_debug("Creating folders for context %s" % ctx)

        # create folders:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            # (AD) - does this work with non-standard hierarchies? e.g. /Task/Entity?
            ctx_entity = ctx.task or ctx.entity or ctx.project

            # FIXME: The launcher uses the defer_keyword setting, which allows to use keywords other
            # than the engine instance name, which is the default value in the launch app. Using
            # engine.instance_name is the best we can do at the moment because the is no way for workfiles
            # to now what the launcher app would have set when launching directly into that environment.
            #
            # Possible solutions:
            # - Using an app level defer_keyword setting might work, but it it may make sharing
            # settings through includes more difficult.
            # - Using an engine level defer_keyword setting might be a better approach,
            # since an app launcher instance launches a specific engine instance using a given defer_keyword.
            # In theory you could have multiple app launcher instances all launching the same engine
            # instance but with different defer_keywords for the same context, but that might be the
            # most absolute of edge cases.
            # - Look for the settings of the launcher app in the destination context and extract the
            # defer_keyword setting and reuse it.
            #
            # It may very well be that there's no solution that fits everyone and might warrant
            # a hook.
            app.sgtk.create_filesystem_structure(ctx_entity.get("type"), ctx_entity.get("id"),
                                                       engine=app.engine.instance_name)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    @staticmethod
    def create_folders_if_needed(ctx, template):
        """
        Create folders for specified context but only if needed.
        """
        # first, if we are currently in the same context then no need to create
        # folders!
        app = sgtk.platform.current_bundle()
        if ctx == app.context:
            return

        create_folders = False
        try:
            # try to get all context fields from the template.  If this raises a TankError then this
            # is a sign that we need to create folders.
            ctx_fields = ctx.as_template_fields(template, validate=True)
            
            # ok, so we managed to get all fields but we still need to check that the context part
            # of the path exists on disk.  To do this, find the template that only contains context
            # keys:
            ctx_keys = set(ctx_fields.keys())
            ctx_template = template
            while ctx_template:
                template_keys = set([k for k in ctx_template.keys if not ctx_template.is_optional(k)])
                if template_keys <= ctx_keys:
                    # we've found the longest template that contains only context fields
                    break
                ctx_template = ctx_template.parent
                
            if not ctx_template:
                # couldn't figure out the path to test so assume that we need to create folders:
                create_folders = True
            else:
                # build the context path:
                ctx_path = ctx_template.apply_fields(ctx_fields)
                # and check that it exists:
                if not os.path.exists(ctx_path):
                    create_folders = True
        except TankError:
            # assume that we need to create folders!
            create_folders = True

        if create_folders:
            FileAction.create_folders(ctx)

    @staticmethod
    def change_context(ctx):
        """
        Set context to the new context.

        :param ctx: The :class:`sgtk.Context` to change to.

        :raises TankError: Raised when the context change fails.
        """
        app = sgtk.platform.current_bundle()
        app.log_info("Changing context from %s to %s" % (app.context, ctx))

        # Change context.
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            sgtk.platform.change_context(ctx)
        except Exception, e:
            app.log_exception("Context change failed!")
            raise TankError("Failed to change work area - %s" % e)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    @staticmethod
    def restore_context(parent_ui, ctx):
        """
        Utility method to restore the original context when a file operation failed.

        A dialog will display the error if the restoration fails. This method is exception safe.

        :param PySide.QtWidget parent_ui: Parent for the error dialog, if needed.
        :param sgtk.Context ctx: Context to restore.
        """
        app = sgtk.platform.current_bundle()
        app.log_debug("Restoring context.")
        try:
            FileAction.change_context(ctx)
        except Exception, e:
            QtGui.QMessageBox.critical(
                parent_ui,
                "Unable to restore the original context",
                "Failed to change the work area back to '%s':\n\n%s\n\nUnable to continue!" % (ctx, e)
            )
            app.log_exception("Failed to change the work area back to %s!" % ctx)

    def __init__(self, label, file, file_versions, environment):
        """
        """
        Action.__init__(self, label)
        self._file = file
        self._file_versions = file_versions
        self._environment = environment

    @property
    def file(self):
        return self._file

    @property
    def file_versions(self):
        return self._file_versions

    @property
    def environment(self):
        return self._environment
