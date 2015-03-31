# Copyright (c) 2014 Shotgun Software Inc.
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

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .file_operation_form import FileOperationForm
from .ui.file_save_form import Ui_FileSaveForm

from .runnable_task import RunnableTask
from .scene_operation import get_current_path, save_file, SAVE_FILE_AS_ACTION
from .environment_details import EnvironmentDetails
from .file_item import FileItem
from .find_files import FileFinder

class SaveAsPreviewGenerator(QtCore.QObject):
    """
    """
    generation_completed = QtCore.Signal(str, str)
    
    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)

        self._current_path = None
        
        app = sgtk.platform.current_bundle()
        self._current_work_template = app.get_template("template_work")
        self._current_publish_template = app.get_template("template_publish")

        self._cached_files = {}
        self._cache_lock = threading.Lock()
        
        self._running_task = None

    def update(self, env, name, extension, version):
        """
        """
        # stop previous preview update:
        if self._running_task:
            self._running_task.stop()
            self._running_task = None
        
        # start new preview generation:
        gen_task = RunnableTask(self._generate_path_task,
                                upstream_tasks = [],
                                environment = env,
                                name = name,
                                extension = extension,
                                version = version)
        
        gen_task.completed.connect(self._on_path_generation_completed)
        gen_task.failed.connect(self._on_path_generation_failed)

        self._running_task = gen_task
        
        gen_task.start()
        
    
    # -----------------------------------------------------------------------------
    
    def _generate_path_task(self, environment, name, extension, version):
        """
        """
        result = self._generate_path(environment, name, extension, version)
        return result
    
    # -----------------------------------------------------------------------------
    
    def _on_path_generation_completed(self, task, result):
        """
        """
        if task != self._running_task:
            return
        self._running_task = None
        
        self.generation_completed.emit(result.get("path", ""), result.get("message", ""))
        
    def _on_path_generation_failed(self, task, msg):
        """
        """
        if task != self._running_task:
            return
        self._running_task = None
        
        self.generation_completed.emit("", msg)

    def _find_files(self, environment):
        """
        """
        entity = None
        if environment.context.entity:
            entity = (environment.context.entity["type"], environment.context.entity["id"])
        step = None
        if environment.context.step:
            step = (environment.context.step["type"], environment.context.step["id"])
        task = None
        if environment.context.task:
            task = (environment.context.task["type"], environment.context.task["id"])
        cache_key = (entity, step, task)
        
        files = None
        self._cache_lock.acquire()
        try:
            files = self._cached_files.get(cache_key)
        finally:
            self._cache_lock.release()
            
        if files != None:
            return files
        
        finder = FileFinder()
        files = finder.find_files(environment.work_template, environment.publish_template, environment.context) or []

        self._cache_lock.acquire()
        try:
            if not cache_key in self._cached_files:
                self._cached_files[cache_key] = files
            else:
                files = self._cached_files[cache_key]
        finally:
            self._cache_lock.release()
            
        return files

    def _generate_path(self, environment, new_name, new_extension, version):
        """
        """
        new_work_path = ""
        msg = None
        can_reset_version = False

        has_name_field = "name" in environment.work_template.keys
        has_version_field = "version" in environment.work_template.keys
        has_extension_field = "extension" in environment.work_template.keys

        # validate name:
        if has_name_field:
            if not environment.work_template.is_optional("name") and not new_name:
                msg = "You must enter a name!"
                return {"message":msg}

            if new_name and not environment.work_template.keys["name"].validate(new_name):
                msg = "Your filename contains illegal characters!"
                return {"message":msg}
            
        if has_extension_field:
            if not environment.work_template.is_optional("extension") and not new_extension:
                msg = "You must select a file extension!"
                return {"message":msg}

            if new_extension and not environment.work_template.keys["extension"].validate(new_extension):
                msg = "Your selected extension is not legal!"
                return {"message":msg}

        # build fields dictionary to use for the new path:
        fields = {}

        # start with fields from context:
        fields = environment.context.as_template_fields(environment.work_template)

        # add in any additional fields from current path:
        #base_template = self._current_publish_template if current_is_publish else self._current_work_template
        #if current_path and base_template.validate(current_path):
        #    template_fields = base_template.get_fields(self._current_path)
        #    fields = dict(chain(template_fields.iteritems(), fields.iteritems()))
        #else:
        if has_version_field:
            # just make sure there is a version
            fields["version"] = version

        # keep track of the current name:
        current_name = fields.get("name")
        current_ext = fields.get("extension")

        # update 'name' field:
        if new_name:
            fields["name"] = new_name
        else:
            # clear the current name - it might be optional!:
            if "name" in fields:
                del fields["name"]

        # update 'ext' field:
        if new_extension:
            fields["extension"] = new_extension
        else:
            # clear the current extension - it might be optional!:
            if "extension" in fields:
                del fields["extension"]

        # if we haven't cached the file list already, do it now - note that this will be per-context/environment:
        existing_files = self._find_files(environment)

        # construct a file key that represents all versions of this publish/work file:
        file_key = FileItem.build_file_key(fields, environment.work_template, 
                                           environment.version_compare_ignore_fields + ["version"])

        # find the max work file and publish versions:        
        work_versions = [f.version for f in existing_files if f.is_local and f.key == file_key]
        max_work_version = max(work_versions) if work_versions else 0
        publish_versions = [f.version for f in existing_files if f.is_published and f.key == file_key]
        max_publish_version = max(publish_versions) if publish_versions else 0
        max_version = max(max_work_version, max_publish_version)
        
        current_is_publish = False
        reset_version = False
        
        if has_version_field:
            # get the current version:
            current_version = fields.get("version")
            
            # now depending on what the source was 
            # and if the name has been changed:
            new_version = None
            if (current_is_publish 
                and ((not has_name_field) or new_name == current_name)
                and ((not has_ext_field) or new_extension == current_ext)
                ):
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
        new_work_path = environment.work_template.apply_fields(fields)
        
        return {"path":new_work_path, "message":msg, "can_reset_version":can_reset_version}


class FileSaveForm(FileOperationForm):
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
        
        FileOperationForm.__init__(self, parent)

        self._exit_code = QtGui.QDialog.Rejected
        self._last_expanded_sz = QtCore.QSize(600, 600)
        self._current_env = None
        self._do_update = True
        self._extension_choices = []
        
        try:
            self._init(init_callback)
        except:
            app.log_exception("Unhandled exception during File Save Form construction!")
        
    def _init(self, init_callback):
        """
        """
        app = sgtk.platform.current_bundle()

        # set up the UI
        self._ui = Ui_FileSaveForm()
        self._ui.setupUi(self)

        # temp
        self._ui.history_btns.hide()
        self._ui.breadcrumbs.hide()
        self._ui.location_label.hide()

        # define which controls are visible before initial show:        
        self._ui.nav_stacked_widget.setCurrentWidget(self._ui.location_page)
        self._ui.browser.hide()
        
        # resize to minimum:
        self.window().resize(self.minimumSizeHint())
        self._collapsed_size = None

        # default state for the version controls is to use the next available version:
        self._ui.use_next_available_cb.setChecked(True)

        # initialize the browser:
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        ctx_entity = app.context.task or app.context.step or app.context.entity or {}
        self._ui.browser.select_entity(ctx_entity.get("type"), ctx_entity.get("id"))
        # file:

        # setup for first run:
        env = EnvironmentDetails(app.context)
        current_file = self._get_current_file(env)
        self._on_work_area_changed(env)
        self._on_selected_file_changed(current_file)
        self._update()

        # execute the init callback:
        if init_callback:
            init_callback(self)

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

    def _on_name_edited(self, txt):
        """
        """
        self._update()

    def _on_name_return_pressed(self):
        #self._on_continue()
        pass
    
    def _on_version_value_changed(self, value):
        self._update()
        
    def _on_extension_current_index_changed(self, value):
        self._update()
        #self._update_preview()

    def _on_use_next_available_version_toggled(self, checked):
        """
        """
        #self._ui.version_spinner.setEnabled(not checked)
        self._update()
        
        #self._on_name_changed()
        
    def _update(self):
        """
        """
        if not self._do_update:
            return
        
        # avoid recursive updates!
        self._do_update = False
        try:
            error_msg = None
            path = None
            # if we don't have a valid environment then we can't do anything!
            if not self._current_env or not self._current_env.context:
                error_msg = "No work area selected"
            elif not self._current_env.work_template:
                error_msg = "Unable to save into this work area!"
            else:
                # got this far so we have a valid work area to save into.  
                # Now lets update everything else.
        
                # get the name, version and extension from the UI:
                name = self._ui.name_edit.text()
                version = self._ui.version_spinner.value()
                ext_idx = self._ui.file_type_menu.currentIndex() 
                ext = self._extension_choices[ext_idx] if ext_idx >= 0 else ""
                
                # build the fields dictionary from the environment:
                fields = self._current_env.context.as_template_fields(self._current_env.work_template)
                
                name_is_used = "name" in self._current_env.work_template.keys
                if name_is_used and name:
                    fields["name"] = name
                
                ext_is_used = "extension" in self._current_env.work_template.keys
                if ext_is_used and ext != None:
                    fields["extension"] = ext
        
                version_is_used = "version" in self._current_env.work_template.keys
                if version_is_used:
                    
                    # need a file key to find all versions so lets build it:
                    file_key = FileItem.build_file_key(fields, self._current_env.work_template, 
                                                       self._current_env.version_compare_ignore_fields + ["version"])
                    
                    # figure out the max version and if needed update the current version:
                    use_next_available = self._ui.use_next_available_cb.isChecked()
                    
                    file_versions = self._file_model.get_file_versions(file_key, self._current_env)
                    if file_versions == None:
                        # fall back to finding the files manually.  
                        # TODO, this should be replaced by an access into the model!
                        finder = FileFinder()
                        files = finder.find_files(self._current_env.work_template, 
                                                  self._current_env.publish_template, 
                                                  self._current_env.context,
                                                  file_key) or []
                        file_versions = [f.version for f in files]
                    max_version = max(file_versions or [0])
                    next_version = max_version + 1
        
                    # update the current version if needed:
                    if version < next_version or use_next_available:
                        version = next_version

                    # update the spinner:
                    self._ui.version_spinner.setEnabled(not use_next_available)
                    self._update_version_spinner(version, next_version)
                    
                    fields["version"] = version
        
                # see if we can build a valid path from the fields:
                try:
                    path = self._current_env.work_template.apply_fields(fields)
                except:
                    error_msg = "Failed to build path"
        
            # and update preview:
            can_save = True
            if path:
                path_preview, name_preview = os.path.split(path)
                self._ui.file_name_preview.setText(name_preview)
                self._ui.work_area_preview.setText(path_preview)
            else:
                # update error message:
                can_save = False
                print error_msg
    
            # enable/disable controls:
            self._ui.save_btn.setEnabled(can_save)
        finally:
            self._do_update = True

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

    def _populate_extension_menu(self, extensions, labels, block_signals=True):
        """
        """
        signals_blocked = self._ui.file_type_menu.blockSignals(block_signals)
        try:
            self._ui.file_type_menu.clear()
            for label in labels:
                self._ui.file_type_menu.addItem(label)
            self._extension_choices = extensions
        finally:
            self._ui.file_type_menu.blockSignals(signals_blocked)
        
    def _get_current_file(self, env):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # get the current file path:
        try:
            current_path = get_current_path(app, SAVE_FILE_AS_ACTION, env.context)
        except Exception, e:
            return None
        
        if not current_path:
            return None
        
        # figure out if it's a publish or a work file:
        is_publish = ((not env.work_template or env.work_template.validate(current_path))
                      and env.publish_template != env.work_template
                      and env.publish_template and env.publish_template.validate(current_path))

        # build fields dictionary and construct key: 
        fields = env.context.as_template_fields(env.work_template)
        base_template = env.publish_template if is_publish else env.work_template
        if base_template.validate(current_path):
            template_fields = base_template.get_fields(current_path)
            fields = dict(chain(template_fields.iteritems(), fields.iteritems()))

        file_key = FileItem.build_file_key(fields, env.work_template, 
                                           env.version_compare_ignore_fields + ["version"])

        # extract details from the fields:
        details = {}
        for key_name in ["name", "version"]:
            if key_name in fields:
                details[key_name] = fields[key_name]

        # build the file item (note that this will be a very minimal FileItem instance)!
        file_item = FileItem(path = current_path if not is_publish else None,
                             publish_path = current_path if is_publish else None,
                             is_local = not is_publish,
                             is_published = is_publish,
                             details = fields,
                             key = file_key)
        
        return file_item

        
    def _on_browser_file_selected(self, file, env):
        """
        """
        self._do_update = False
        try:
            self._on_work_area_changed(env)
            self._on_selected_file_changed(file)
        finally:
            self._do_update = True
        self._update()
    
    def _on_browser_file_double_clicked(self, file, env):
        """
        """
        self._on_browser_file_selected(file, env)
        self._on_save()

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
        if not file.is_local and file.is_published:
            if self._current_env.publish_template:
                fields = self._current_env.publish_template.get_fields(file.publish_path)
        else:
            if self._current_env.work_template:
                fields = self._current_env.work_template.get_fields(file.path)

        # pull the current name/extension from the file:
        if name_is_used:
            name = fields.get("name", "")
            name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
            if not name and not name_is_optional:
                # need to use either the current name if we have it or the default if we don't!
                current_name = self._ui.name_edit.text()
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



    def _on_browser_work_area_changed(self, entity, step, task):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # build context:
        if ((task and not (step and entity))
            or (step and not entity)):
            # use full context from entity method (slow as it will likely perform a Shotgun
            # query!
            context_entity = task or step or entity 
            context = app.sgtk.context_from_entity(context_entity["type"], context_entity["id"])
        else:
            context = app.sgtk.context_from_entities(project = app.context.project, 
                                                     entity = entity,
                                                     step = step,
                                                     task = task)
        
        self._do_update = False
        try:
            env = EnvironmentDetails(context)
            self._on_work_area_changed(env)
        finally:
            self._do_update = True
            
        self._update()

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
                name = self._ui.name_edit.text()
                name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
                if not name and not name_is_optional:
                    name = self._current_env.save_as_default_name or "scene"
                self._ui.name_edit.setText(name)

            self._ui.name_label.setVisible(name_is_used)
            self._ui.name_edit.setVisible(name_is_used)

            # update the visibility and available/default values of the extension menu:
            ext_is_used = "extension" in self._current_env.work_template.keys
            if ext_is_used:
                ext_key = self._current_env.work_template.keys["extension"]
                ext_choices = ext_key.choices
                ext_labels = ext_key.choice_labels
                ext = ext_key.default
                
                current_ext_idx = self._ui.file_type_menu.currentIndex()
                current_ext = ""
                if current_ext_idx >= 0 and current_ext_idx < len(self._extension_choices):
                    current_ext = self._extension_choices[current_ext_idx]
                if current_ext in ext_choices:
                    ext = current_ext

                self._populate_extension_menu(ext_choices, ext_labels)
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
            if self._collapsed_size == None or not self._collapsed_size.isValid():
                self._collapsed_size = self.size()
                
            #self._ui.browser_stacked_widget.setCurrentWidget(self._ui.browser_page)
            self._ui.nav_stacked_widget.setCurrentWidget(self._ui.history_nav_page)
            self._ui.browser.show()
            
            if self._last_expanded_sz == self._collapsed_size:
                self._last_expanded_sz = QtCore.QSize(800, 800)

            # (AD) - this doesn't currently work - it appears to be resizing to the
            # current minimum size!            
            self.window().resize(self._last_expanded_sz)
        else:
            self._last_expanded_sz = self.window().size()
            #print self._last_expanded_sz
            
            self._ui.browser.hide()
            #self._ui.browser_stacked_widget.setCurrentWidget(self._ui.line_page)
            self._ui.nav_stacked_widget.setCurrentWidget(self._ui.location_page)
            
            # resize to minimum:
            min_size = self.minimumSizeHint()
            self.window().resize(min_size)
        
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
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
