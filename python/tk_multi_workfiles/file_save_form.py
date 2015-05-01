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
Qt widget where the user can enter name, version and file type in order to save the
current work file.  Also give the user the option to select the file to save from
the list of current work files.
"""

import threading
import os
from itertools import chain

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from sgtk import TankError

from .file_form_base import FileFormBase
from .ui.file_save_form import Ui_FileSaveForm

from .runnable_task import RunnableTask
from .scene_operation import get_current_path, save_file, SAVE_FILE_AS_ACTION
from .environment_details import EnvironmentDetails
from .file_item import FileItem
from .find_files import FileFinder

from .breadcrumb_widget import Breadcrumb
from .util import value_to_str

class FileSaveForm(FileFormBase):
    """
    UI for saving a work file
    """
    @property
    def exit_code(self):
        return self._exit_code
    
    def __init__(self, init_callback, parent=None):
        """
        Construction
        """
        app = sgtk.platform.current_bundle()

        FileFormBase.__init__(self, parent)

        self._expanded_size = QtCore.QSize(930, 700)
        self._collapsed_size = None

        self._exit_code = QtGui.QDialog.Rejected
        self._current_env = None
        self._current_path = ""
        self._extension_choices = []
        self._preview_task = None
        self._navigating = False

        try:
            # doing this inside a try-except to ensure any exceptions raised don't 
            # break the UI and crash the dcc horribly!
            self._init(init_callback)
        except:
            app.log_exception("Unhandled exception during File Save Form construction!")
        
    def _init(self, init_callback):
        """
        Actual construction!
        """
        app = sgtk.platform.current_bundle()

        # set up the UI
        self._ui = Ui_FileSaveForm()
        self._ui.setupUi(self)

        # temp
        #self._ui.location_label.hide()

        # define which controls are visible before initial show:        
        self._ui.browser.hide()
        self._ui.nav.hide()
        self._ui.feedback_stacked_widget.setCurrentWidget(self._ui.preview_page)
        self._ui.work_area_preview.elide_mode = QtCore.Qt.ElideLeft
        self._ui.work_area_preview.setText("")
        
        self.layout().setStretch(0, 0)
        self.layout().setStretch(3, 1)
        
        # resize to minimum:
        self.window().resize(self.minimumSizeHint())

        # default state for the version controls is to use the next available version:
        self._ui.use_next_available_cb.setChecked(True)
        self._ui.version_spinner.setEnabled(False)

        # hook up signals on controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.save_btn.clicked.connect(self._on_save)
        self._ui.expand_checkbox.toggled.connect(self._on_expand_toggled)
        self._ui.name_edit.textEdited.connect(self._on_name_edited)
        self._ui.name_edit.returnPressed.connect(self._on_name_return_pressed)
        self._ui.version_spinner.valueChanged.connect(self._on_version_value_changed)
        self._ui.file_type_menu.currentIndexChanged.connect(self._on_extension_current_index_changed)
        self._ui.use_next_available_cb.toggled.connect(self._on_use_next_available_version_toggled)
        self._ui.browser.create_new_task.connect(self._on_create_new_task)
        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(self._on_browser_file_double_clicked)
        #self._ui.browser.file_context_menu_requested.connect(self._on_browser_context_menu_requested)
        self._ui.browser.work_area_changed.connect(self._on_browser_work_area_changed)
        
        self._ui.nav.navigate.connect(self._on_navigate)
        self._ui.nav.home_clicked.connect(self._on_navigate_home)

        # start the preview update:
        self._start_preview_update()

        # initialize the browser:
        self._ui.browser.enable_show_all_versions(False)
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        env = EnvironmentDetails(app.context)
        current_file = self._get_current_file()
        self._ui.browser.select_work_area(app.context)
        self._ui.browser.select_file(current_file, app.context)
        
        #self._on_work_area_changed(env)
        #self._on_selected_file_changed(current_file)

        # execute the init callback:
        if init_callback:
            init_callback(self)


    @property
    def path(self):
        """
        """
        return self._current_path

    @property
    def environment(self):
        return self._current_env

    def _on_name_edited(self, txt):
        """
        """
        self._start_preview_update()

    def _on_name_return_pressed(self):
        #self._on_continue()
        pass
    
    def _on_version_value_changed(self, value):
        self._start_preview_update()
        
    def _on_extension_current_index_changed(self, value):
        self._start_preview_update()
        #self._update_preview()

    def _on_use_next_available_version_toggled(self, checked):
        """
        """
        self._ui.version_spinner.setEnabled(not checked)
        self._start_preview_update()
        
        #self._on_name_changed()
        
    def _start_preview_update(self):
        """
        """
        # stop previous running task:
        if self._preview_task:
            self._preview_task.stop()
            self._preview_task = None

        # clear the current path - this will ensure hitting save doesn't 
        # do anything whilst we're updating the path
        self._current_path = None
        
        # get the name, version and extension from the UI:
        name = value_to_str(self._ui.name_edit.text())
        version = self._ui.version_spinner.value()
        use_next_version = self._ui.use_next_available_cb.isChecked()
        ext_idx = self._ui.file_type_menu.currentIndex() 
        ext = self._extension_choices[ext_idx] if ext_idx >= 0 else ""

        self._preview_task = RunnableTask(self._generate_path,
                                          env = self._current_env,
                                          name = name,
                                          version = version,
                                          use_next_version = use_next_version,
                                          ext = ext)
        self._preview_task.completed.connect(self._on_preview_generation_complete)
        self._preview_task.failed.connect(self._on_preview_generation_failed)
        
        self._preview_task.start()

    def _on_preview_generation_complete(self, task, result):
        """
        """
        if task != self._preview_task:
            return
        self._preview_task = None
        
        self._current_path = result["path"]
        version = result["version"]
        next_version = result["next_version"]
        use_next_version = result["use_next_version"]

        # update version controls:
        self._update_version_spinner(version, next_version)
        
        # update path preview:
        self._ui.feedback_stacked_widget.setCurrentWidget(self._ui.preview_page)
        path_preview, name_preview = os.path.split(self._current_path)
        self._ui.file_name_preview.setText(name_preview)
        self._ui.work_area_preview.setText(path_preview)

        self._ui.save_btn.setEnabled(True)

    def _on_preview_generation_failed(self, task, msg, stack_trace):
        """
        """
        if task != self._preview_task:
            return
        self._preview_task = None
        self._current_path = None
        
        self._ui.feedback_stacked_widget.setCurrentWidget(self._ui.warning_page)
        error_msg = "<p style='color:rgb(226, 146, 0)'>Warning: %s</p>" % msg
        self._ui.warning.setText(error_msg)
        
        self._ui.save_btn.setEnabled(False)
    
    def _generate_path(self, env, name, version, use_next_version, ext):
        """
        :returns:   Tuple containing (path, min_version)
        :raises:    Error if something goes wrong!
        """

        # first make  sure the environment is complete:
        if not env or not env.context:
            raise TankError("Please select a work area to save into...")
        elif not env.work_template:
            raise TankError("Unable to save into this work area.  Please select a different work area!")

        # build the fields dictionary from the environment:
        fields = env.context.as_template_fields(env.work_template)
        
        name_is_used = "name" in env.work_template.keys
        if name_is_used:
            if not env.work_template.is_optional("name") and not name:
                raise TankError("Name is required, please enter a valid name!")
            if name:
                if not env.work_template.keys["name"].validate(name):
                    raise TankError("Name contains illegal characters!")
                fields["name"] = name
        
        ext_is_used = "extension" in env.work_template.keys
        if ext_is_used and ext != None:
            fields["extension"] = ext

        next_version = None
        version_is_used = "version" in env.work_template.keys
        if version_is_used:
            # need a file key to find all versions so lets build it:
            file_key = FileItem.build_file_key(fields, env.work_template, 
                                               env.version_compare_ignore_fields)

            file_versions = self._file_model.get_file_versions(file_key, env)
            if file_versions == None:
                # fall back to finding the files manually.  
                # TODO, this should be replaced by an access into the model!
                finder = FileFinder()
                try:
                    files = finder.find_files(env.work_template, 
                                              env.publish_template, 
                                              env.context,
                                              file_key) or []
                except TankError, e:
                    raise TankError("Failed to find files for this work area: %s" % e)
                file_versions = [f.version for f in files]

            max_version = max(file_versions or [0])
            next_version = max_version + 1

            # update version:
            version = next_version if use_next_version else max(version, next_version)
            fields["version"] = version 

        # see if we can build a valid path from the fields:
        path = None
        try:
            path = env.work_template.apply_fields(fields)
        except TankError, e:
            raise TankError("Failed to build a valid path: %s" % e)

        return {"path":path, 
                "version":version, 
                "next_version":next_version,
                "use_next_version":use_next_version}

    def _update_version_spinner(self, version, min_version, block_signals=True):
        """
        """
        signals_blocked = self._ui.version_spinner.blockSignals(block_signals)
        try:
            self._ui.version_spinner.setMinimum(min_version)
            self._ui.version_spinner.setValue(version)
        finally:
            self._ui.version_spinner.blockSignals(signals_blocked)

    def _update_extension_menu(self, ext, block_signals=True):
        """
        """
        signals_blocked = self._ui.file_type_menu.blockSignals(block_signals)
        try:
            if ext in self._extension_choices:
                self._ui.file_type_menu.setCurrentIndex(self._extension_choices.index(ext))
        finally:
            self._ui.file_type_menu.blockSignals(signals_blocked)

    def _populate_extension_menu(self, extensions, block_signals=True):
        """
        """
        signals_blocked = self._ui.file_type_menu.blockSignals(block_signals)
        try:
            self._ui.file_type_menu.clear()
            for label in extensions.values():
                self._ui.file_type_menu.addItem(label)
            self._extension_choices = extensions.keys()
        finally:
            self._ui.file_type_menu.blockSignals(signals_blocked)
        
    def _on_browser_file_selected(self, file, env):
        """
        """
        self._on_work_area_changed(env)
        self._on_selected_file_changed(file)
        self._start_preview_update()
    
    def _on_browser_file_double_clicked(self, file, env):
        """
        """
        self._on_browser_file_selected(file, env)
        # TODO: this won't actually work until the preview has 
        # been updated!
        self._on_save()

    def _on_navigate(self, breadcrumb_trail):
        """
        """
        if not breadcrumb_trail:
            return

        # awesome, just navigate to the breadcrumbs:
        self._ui.breadcrumbs.set(breadcrumb_trail)
        self._navigating = True
        try:
            self._ui.browser.navigate_to(breadcrumb_trail)
        finally:
            self._navigating = False

    def _on_navigate_home(self):
        """
        Navigate to the current work area
        """
        app = sgtk.platform.current_bundle()
        self._ui.browser.select_work_area(app.context)

    def _on_selected_file_changed(self, file):
        """
        """
        if not self._current_env or not self._current_env.work_template or not file:
            return

        name_is_used = "name" in self._current_env.work_template.keys
        ext_is_used = "extension" in self._current_env.work_template.keys
        
        if not name_is_used and not ext_is_used:
            return
        
        # get the fields for this file:
        fields = {}
        try:
            if not file.is_local and file.is_published:
                if self._current_env.publish_template:
                    fields = self._current_env.publish_template.get_fields(file.publish_path)
            else:
                if self._current_env.work_template:
                    fields = self._current_env.work_template.get_fields(file.path)
        except:
            pass

        # pull the current name/extension from the file:
        if name_is_used:
            name = fields.get("name", "")
            name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
            if not name and not name_is_optional:
                # need to use either the current name if we have it or the default if we don't!
                current_name = value_to_str(self._ui.name_edit.text())
                default_name = self._current_env.save_as_default_name
                name = current_name or default_name or "scene"

            self._ui.name_edit.setText(name)

        ext_is_used = "extension" in self._current_env.work_template.keys
        if ext_is_used:
            ext = fields.get("extension", "")
            if ext in self._extension_choices:
                # update extension:
                self._update_extension_menu(ext)
                #self._ui.file_type_menu.setCurrentIndex(self._extension_choices.index(ext))
            else:
                # TODO try to get extension from path?
                pass

    def _on_browser_work_area_changed(self, entity, breadcrumbs):#, step, task):
        """
        """
        env = None
        if entity:
            app = sgtk.platform.current_bundle()
            context = app.sgtk.context_from_entity_dictionary(entity)
            env = EnvironmentDetails(context)
        self._on_work_area_changed(env)
        self._start_preview_update()

        if not self._navigating:
            destination_label = breadcrumbs[-1].label if breadcrumbs else "..."
            self._ui.nav.add_destination(destination_label, breadcrumbs)
        self._ui.breadcrumbs.set(breadcrumbs)

    def _on_work_area_changed(self, env):
        """
        """
        if env and self._current_env and env.context == self._current_env.context:
            # nothing changed so nothing to do here!
            return
        
        self._current_env = env
        
        # use the new work area to update the UI:
        if self._current_env and self._current_env.work_template:
            # looks like we have a valid work template :)

            # update visibility and value of the name field:
            name_is_used = "name" in self._current_env.work_template.keys
            if name_is_used:
                # try to set something valid for the name:
                name = value_to_str(self._ui.name_edit.text())
                name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
                if not name and not name_is_optional:
                    # lets populate name with a default value:
                    name = self._current_env.save_as_default_name or "scene"
                self._ui.name_edit.setText(name)

            self._ui.name_label.setVisible(name_is_used)
            self._ui.name_edit.setVisible(name_is_used)

            # update the visibility and available/default values of the extension menu:
            ext_is_used = "extension" in self._current_env.work_template.keys
            if ext_is_used:
                ext_key = self._current_env.work_template.keys["extension"]
                #ext_choices = ext_key.choices
                #ext_labels = ext_key.choice_labels
                
                ext_choices = ext_key.labelled_choices
                
                ext = ext_key.default
                
                current_ext_idx = self._ui.file_type_menu.currentIndex()
                current_ext = ""
                if current_ext_idx >= 0 and current_ext_idx < len(self._extension_choices):
                    current_ext = self._extension_choices[current_ext_idx]
                if current_ext in ext_choices.keys():
                    ext = current_ext

                self._populate_extension_menu(ext_choices)#, ext_labels)
                self._update_extension_menu(ext)

            self._ui.file_type_label.setVisible(ext_is_used)
            self._ui.file_type_menu.setVisible(ext_is_used)

            # update the visibility of the version field:
            version_is_used = "version" in self._current_env.work_template.keys
            self._ui.version_label.setVisible(version_is_used)
            self._ui.version_spinner.setVisible(version_is_used)
            self._ui.use_next_available_cb.setVisible(version_is_used)
        
    def _on_expand_toggled(self, checked):
        """
        """
        if checked:
            if self._collapsed_size == None:
                # keep track of the collapsed size the first time it's resized:
                self._collapsed_size = self.window().size()

            # show the browser and nav buttons:
            self._ui.browser.show()
            self._ui.nav.show()

            # update the layout for the browser:
            self.layout().setStretch(0, 1)
            self.layout().setStretch(3, 0)

            # and resize the window to the expanded size:
            self.window().resize(self._expanded_size)
        else:
            # collapsing so keep track of previous expanded size:
            self._expanded_size = self.window().size()

            # hide the browser and nav buttons:
            self._ui.browser.hide()
            self._ui.nav.hide()

            # update the layout for the browser:
            self.layout().setStretch(0, 0)
            self.layout().setStretch(3, 1)

            # resize the window to the collapsed size:
            self.window().resize(self._collapsed_size)

    def resizeEvent(self, event):
        pass
        #print self.size(), self.window().size()

    #def resizeEvent(self, event):
    #    """
    #    """
    #    if self._collapsed_size == None or not self._collapsed_size.isValid():
    #        self._collapsed_size = event.oldSize()
    #    
    #    print "COLLAPSED", self._collapsed_size
    #    print "SIZE", event.size()
    #    
    #    if (event.size().height() <= self._collapsed_size.height()):
    #        if self._ui.expand_checkbox.isChecked():
    #            print "off"
    #            self._ui.expand_checkbox.setChecked(False)
    #    else:
    #        if not self._ui.expand_checkbox.isChecked():
    #            print "on"
    #            self._ui.expand_checkbox.setChecked(True)
        
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()
        
    def _on_save(self):
        """
        """
        if not self._current_env or not self._current_path:
            return
        
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
