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
from .work_area import WorkArea
from .file_item import FileItem
from .file_finder import FileFinder
from .util import value_to_str

from .actions.save_as_file_action import SaveAsFileAction

class FileSaveForm(FileFormBase):
    """
    UI for saving a work file
    """
    _WARNING_COLOUR = (226, 146, 0)

    @property
    def exit_code(self):
        return self._exit_code
    
    def __init__(self, parent=None):
        """
        Construction
        """
        app = sgtk.platform.current_bundle()

        FileFormBase.__init__(self, parent)

        self._expanded_size = QtCore.QSize(930, 700)
        self._collapsed_size = None

        self._exit_code = QtGui.QDialog.Rejected
        self._current_env = None
        self._extension_choices = []
        self._preview_task = None
        self._navigating = False

        font_colour = self.palette().text().color()
        if font_colour.value() < 0.5:
            # make preview text colour 40% lighter
            preview_colour = font_colour.lighter(140)
        else:
            # make preview text colour 40% darker
            preview_colour = font_colour.darker(140)
        self._preview_colour = (preview_colour.red(), preview_colour.green(), preview_colour.blue())

        try:
            # doing this inside a try-except to ensure any exceptions raised don't 
            # break the UI and crash the dcc horribly!
            self._init()
        except:
            app.log_exception("Unhandled exception during File Save Form construction!")
        
    def _init(self):
        """
        Actual construction!
        """
        app = sgtk.platform.current_bundle()

        # set up the UI
        self._ui = Ui_FileSaveForm()
        self._ui.setupUi(self)

        self._ui.preview_label.setText("<p style='color:rgb%s'><b>Preview:</b></p>" % (self._preview_colour, ))
        self._ui.file_name_preview.setText("<p style='color:rgb%s'></p>" % (self._preview_colour, ))
        self._ui.work_area_label.setText("<p style='color:rgb%s'><b>Work Area:</b></p>" % (self._preview_colour, ))
        self._ui.work_area_preview.setText("<p style='color:rgb%s'></p>" % (self._preview_colour, ))
        self._ui.warning_label.setText("<p style='color:rgb%s'><b>Warning:</b></p>" % (FileSaveForm._WARNING_COLOUR, ))
        self._ui.warning.setText("<p style='color:rgb%s'></p>" % (FileSaveForm._WARNING_COLOUR, ))

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
        self._ui.browser.work_area_changed.connect(self._on_browser_work_area_changed)

        self._ui.nav.navigate.connect(self._on_navigate)
        self._ui.nav.home_clicked.connect(self._on_navigate_home)

        # initialize the browser:
        self._ui.browser.enable_show_all_versions(False)
        self._ui.browser.enable_show_user_sandboxes(False)
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        env = WorkArea(app.context)
        current_file = self._get_current_file()
        self._ui.browser.select_work_area(app.context)
        self._ui.browser.select_file(current_file, app.context)

        # initialize the browser with the current file and environment:
        self._on_browser_file_selected(current_file, env)

        # if it's not possible to save into the initial work area then start the UI expanded:
        if not env or not env.work_template:
            self._ui.expand_checkbox.setChecked(True)
            self._on_expand_toggled(True)

    # ------------------------------------------------------------------------------------------
    # protected methods

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

    def _on_use_next_available_version_toggled(self, checked):
        """
        """
        self._ui.version_spinner.setEnabled(not checked)
        self._start_preview_update()

    def _start_preview_update(self):
        """
        """
        # stop previous running task:
        if self._preview_task:
            self._preview_task.stop()
            self._preview_task = None

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
                                          ext = ext,
                                          require_path = False)
        self._preview_task.completed.connect(self._on_preview_generation_complete)
        self._preview_task.failed.connect(self._on_preview_generation_failed)
        
        self._preview_task.start()

    def _on_preview_generation_complete(self, task, result):
        """
        """
        if task != self._preview_task:
            return
        self._preview_task = None

        name_preview = ""
        path_preview = ""
        path = result.get("path")
        if path is None:
            # something went wrong causing the preview path to not get generated!
            # Report this but still allow the user to attempt saving.
            # This can happen when folders haven't yet been created, resulting in
            # Toolkit not being able to fully resolve fields from the context.
            name_preview = ("Unable to generate preview - this may be because nothing has "
                            "ever been saved into this Work Area!")
            path_preview = ""
            self._ui.work_area_label.setVisible(False)
        else:
            path_preview, name_preview = os.path.split(path)
            self._ui.work_area_label.setVisible(True)

        self._ui.feedback_stacked_widget.setCurrentWidget(self._ui.preview_page)
        self._ui.file_name_preview.setText("<p style='color:rgb%s'>%s</p>" 
                                           % (self._preview_colour, name_preview))
        self._ui.work_area_preview.setText("<p style='color:rgb%s'>%s</p>" 
                                           % (self._preview_colour, path_preview))

        # update version controls:
        version = result.get("version") or 1
        next_version = result.get("next_version") or 1
        self._update_version_spinner(version, next_version)

        self._ui.save_btn.setEnabled(True)

    def _on_preview_generation_failed(self, task, msg, stack_trace):
        """
        """
        if task != self._preview_task:
            return
        self._preview_task = None
        
        self._ui.feedback_stacked_widget.setCurrentWidget(self._ui.warning_page)
        self._ui.warning.setText("<p style='color:rgb%s'>%s</p>" % (FileSaveForm._WARNING_COLOUR, msg))
        
        self._ui.save_btn.setEnabled(False)
    
    def _generate_path(self, env, name, version, use_next_version, ext, require_path=False):
        """
        :returns:   Tuple containing (path, min_version)
        :raises:    Error if something goes wrong!
        """
        app = sgtk.platform.current_bundle()

        # first make  sure the environment is complete:
        if not env or not env.context:
            raise TankError("Please select a work area to save into...")
        elif not env.work_template:
            raise TankError("Unable to save into this work area.  Please select a different work area!")

        # build the fields dictionary from the environment:
        fields = {}
        
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

        # query the context fields:
        ctx_fields = {}
        try:
            ctx_fields = env.context.as_template_fields(env.work_template, validate=True)
            fields = dict(chain(fields.iteritems(), ctx_fields.iteritems()))
        except TankError, e:
            app.log_debug("Unable to generate preview path: %s" % e)
            if require_path:
                # log the original exception (useful for tracking down the problem) 
                app.log_exception("Unable to resolve template fields!")
                # and raise a new, clearer exception for this specific use case:
                raise TankError("Unable to resolve template fields!  This could mean there is a mismatch "
                                "between your folder schema and templates.  Please email "
                                "toolkitsupport@shotgunsoftware.com if you need help fixing this.")

            # it's ok not to have a path preview at this point!
            return {}

        next_version = None
        version_is_used = "version" in env.work_template.keys
        if version_is_used:
            # version is used so we need to find the latest version - this means 
            # searching for files...

            # need a file key to find all versions so lets build it:
            file_key = FileItem.build_file_key(fields, env.work_template, 
                                               env.version_compare_ignore_fields)

            file_versions = self._file_model.get_file_versions(file_key, env)
            if file_versions == None:
                # fall back to finding the files manually - this will be slower!  
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
        else:
            # version isn't used!
            version = None

        # see if we can build a valid path from the fields:
        path = None
        try:
            path = env.work_template.apply_fields(fields)
        except TankError, e:
            if require_path:
                # we need a path so re-raise the exception!
                raise

            # otherwise it's ok to not have a path!
            app.log_debug("Unable to generate preview path: %s" % e)
            path = None

        return {"path":path, 
                "version":version, 
                "next_version":next_version}

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
        if env != None:
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

    def _on_browser_work_area_changed(self, entity, breadcrumbs):
        """
        """
        env = None
        if entity:
            app = sgtk.platform.current_bundle()
            context = app.sgtk.context_from_entity_dictionary(entity)
            env = WorkArea(context)
        self._on_work_area_changed(env)
        self._start_preview_update()

        if not self._navigating:
            destination_label = breadcrumbs[-1].label if breadcrumbs else "..."
            self._ui.nav.add_destination(destination_label, breadcrumbs)
        self._ui.breadcrumbs.set(breadcrumbs)


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
        version_is_used = "version" in self._current_env.work_template.keys
        
        if not name_is_used and not ext_is_used and not version_is_used:
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

        if name_is_used:
            # update name edit:
            name = fields.get("name", "")
            name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
            if not name and not name_is_optional:
                # need to use either the current name if we have it or the default if we don't!
                current_name = value_to_str(self._ui.name_edit.text())
                default_name = self._current_env.save_as_default_name
                name = current_name or default_name or "scene"

            self._ui.name_edit.setText(name)

        if ext_is_used:
            # update extension menu:
            ext = fields.get("extension", "")
            if ext in self._extension_choices:
                # update extension:
                self._update_extension_menu(ext)
                #self._ui.file_type_menu.setCurrentIndex(self._extension_choices.index(ext))
            else:
                # TODO try to get extension from path?
                pass

        if version_is_used:
            # update version spinner
            version = fields.get("version", 1)
            # update the version spinner:
            use_next_version = self._ui.use_next_available_cb.isChecked()
            version_to_set = version+1
            if not use_next_version:
                spinner_version = self._ui.version_spinner.value()
                version_to_set = max(version_to_set, spinner_version)
            self._update_version_spinner(version_to_set, version+1)

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

    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()

    def _on_save(self):
        """
        """
        app = sgtk.platform.current_bundle()
        if not self._current_env:
            return

        # generate the path to save to and do any pre-save preparation:
        path = ""
        try:
            # Check to see if we are able to populate all context fields - if we aren't then
            # this may mean we need to create folders before trying to save!
            create_folders = False
            try:
                self._current_env.context.as_template_fields(self._current_env.work_template, 
                                                             validate=True)
            except TankError:
                # lets try creating folders for the current env!
                try:
                    SaveAsFileAction.create_folders(self._current_env.context)
                except TankError, e:
                    app.log_exception("File Save - failed to create folders for context '%s'!" 
                                       % self._current_env.context)
                    raise TankError("Failed to create folders for context '%s' - %s" 
                                    % (self._current_env.context, e))

            # get the name, version and extension from the UI:
            name = value_to_str(self._ui.name_edit.text())
            version = self._ui.version_spinner.value()
            use_next_version = self._ui.use_next_available_cb.isChecked()
            ext_idx = self._ui.file_type_menu.currentIndex() 
            ext = self._extension_choices[ext_idx] if ext_idx >= 0 else ""

            # now attempt to generate the path to save to:
            path_to_save = None
            version_to_save = None
            try:
                # try to generate a path from these details:
                result = self._generate_path(self._current_env, name, version, 
                                             use_next_version, ext, require_path=True)
                path_to_save = result.get("path")
                if not path_to_save:
                    raise TankError("Path generation returned an empty path!")
                version_to_save = result.get("version")
            except TankError, e:
                app.log_exception("File Save - failed to generate path to save to!")
                raise TankError("Failed to generate a path to save to - %s" % e)

            if (version_to_save is not None         # version is used in the path 
                and version_to_save != version):    # version in the path is different to the one in the UI!
                # check to see if the version has changed as a result of the 
                # preview generation - if it has then we should double check
                # the user still wants to save!
                #
                # Note, this should rarely happen - it's more a 'just-in-case'
                # scenario that can happen if the background loaded data takes
                # a while to filter through to the UI! 
                name_is_used = "name" in self._current_env.work_template.keys
                msg = ""
                if version_to_save == 1:
                    if name_is_used and name:
                        msg = ("We didn't find any existing versions of the file '%s' " % name)
                    else:
                        msg = "We didn't find any existing versions of this file "
                else:
                    if name_is_used and name:
                        msg = ("We found a more recent version (v%03d) of the file '%s' "
                               % (version_to_save-1, name))
                    else:
                        msg = ("We found a more recent version (v%03d) of this file "
                               % (version_to_save-1))
                msg += ("in the selected work area:\n\n  %s\n\n"
                        "Would you like to continue saving as v%03d, the next available version?" 
                        % (self._current_env.context, version_to_save))

                answer = QtGui.QMessageBox.question(self, "Save File as Version v%03d?" % version_to_save,
                                                    msg, QtGui.QMessageBox.Save | QtGui.QMessageBox.Cancel)
                if answer == QtGui.QMessageBox.Cancel:
                    return False

            # finally, make sure that the folder exists - this will handle any leaf folders that aren't
            # created during folder creation (e.g. a dynamic static folder that isn't part of the schema)
            dir = os.path.dirname(path_to_save)
            if dir and not os.path.exists(dir):
                app.ensure_folder_exists(dir)
        except TankError, e:
            # oops, looks like something went wrong!
            QtGui.QMessageBox.critical(self, "Failed to save file!", "Failed to save file!\n\n%s" % e)
            return
        except Exception, e:
            # also handle generic exception:
            QtGui.QMessageBox.critical(self, "Failed to save file!", "Failed to save file!\n\n%s" % e)
            app.log_exception("Failed to save file!")
            return

        # Build and execute the save action:
        action = SaveAsFileAction(path_to_save, self._current_env)
        file_saved = action.execute(self)

        if file_saved:
            # all good - lets close the dialog
            self._exit_code = QtGui.QDialog.Accepted
            self.close()





