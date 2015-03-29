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

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .file_operation_form import FileOperationForm
from .ui.file_save_form import Ui_FileSaveForm

from .runnable_task import RunnableTask

from .environment_details import EnvironmentDetails

class SaveAsPathGenerator(QtCore.QObject):
    """
    """
    def __init__(self, current_path, parent):
        QtCore.QObject.__init__(self, parent)

        self._current_path = current_path
        
        app = sgtk.platform.current_bundle()
        self._current_work_template = app.get_template("template_work")
        self._current_publish_template = app.get_template("template_publish")

        self._cached_files = {}
        self._cache_lock = threading.Lock()
        
        self._running_task = None

    def async_update(self, name, extension, version, entity, step, task):
        """
        """
        # stop previous preview update:
        if self._running_task:
            self._running_task.stop()
            self._running_task = None
        
        # start new preview generation:
        get_env_task = RunnableTask(self._get_env_task, 
                                    upstream_tasks = None, 
                                    entity = entity, 
                                    step = step, 
                                    task = task)
        
        gen_task = RunnableTask(self._generate_path_task,
                                upstream_tasks =[get_env_task],
                                name = name,
                                extension = extension,
                                version = version)
        
        gen_task.completed.connect(self._on_path_generation_completed)
        gen_task.failed.connect(self._on_path_generation_failed)
        
        gen_task.start()
        
    
    # -----------------------------------------------------------------------------
    
    def _get_env_task(self, entity, step, task, **kwargs):
        """
        """
        return {"environment":None}
    
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
        
    def _on_path_generation_failed(self, task, msg):
        """
        """
        if task != self._running_task:
            return
        self._running_task = None

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
        base_template = self._current_publish_template if current_is_publish else self._current_work_template
        if current_path and base_template.validate(current_path):
            template_fields = base_template.get_fields(self._current_path)
            fields = dict(chain(template_fields.iteritems(), fields.iteritems()))
        else:
            if has_version_field:
                # just make sure there is a version
                fields["version"] = 1

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
                                           self.__version_compare_ignore_fields + ["version"])

        # find the max work file and publish versions:        
        work_versions = [f.version for f in existing_files if f.is_local and f.key == file_key]
        max_work_version = max(work_versions) if work_versions else 0
        publish_versions = [f.version for f in existing_files if f.is_published and f.key == file_key]
        max_publish_version = max(publish_versions) if publish_versions else 0
        max_version = max(max_work_version, max_publish_version)
        
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
    #def __init__(self, name, file_types, version, init_callback, parent=None):
        """
        Construction
        """
        app = sgtk.platform.current_bundle()
        
        FileOperationForm.__init__(self, parent)

        self._exit_code = QtGui.QDialog.Rejected
        self._last_expanded_sz = QtCore.QSize(600, 600)

        self._current_env = EnvironmentDetails(app.context)
        self._selected_file = None
        
        # set up the UI
        self._ui = Ui_FileSaveForm()
        self._ui.setupUi(self)

        # define which controls are visible before initial show:        
        self._ui.nav_stacked_widget.setCurrentWidget(self._ui.location_page)
        self._ui.browser.hide()
        
        # resize to minimum:
        self.window().resize(self.minimumSizeHint())
        self._collapsed_size = None
        
        # hook up all other controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.save_btn.clicked.connect(self._on_save)
        self._ui.expand_checkbox.toggled.connect(self._on_expand_toggled)

        # initialize the browser widget:
        self._ui.browser.set_models(self._my_tasks_model, self._entity_models, self._file_model)
        self._ui.browser.create_new_task.connect(self._on_create_new_task)
        self._ui.browser.file_selected.connect(self._on_browser_file_selected)
        self._ui.browser.file_double_clicked.connect(self._on_browser_file_double_clicked)
        self._ui.browser.file_context_menu_requested.connect(self._on_browser_context_menu_requested)
        self._ui.browser.work_area_changed.connect(self._on_browser_work_area_changed)
        
        self._on_selected_file_changed()
        
        # finally, execute the init callback:
        if init_callback:
            init_callback(self)
        
    def _on_browser_work_area_changed(self, entity, step, task):
        """
        """
        # 1. disable the input area
        
        # 2. figure out the context & templates
        # (can do this in the background)
        
        # 3. update input area and re-enable 
        pass
        
    def _on_work_area_changed(self):
        """
        """
        can_save = self._current_env.work_template is not None
        
        self._ui.save_btn.setEnabled(can_save)
        self._ui.name_edit.setEnabled(can_save)
        self._ui.file_type_menu.setEnabled(can_save)
        self._ui.version_spinner.setEnabled(can_save)
        
        # use the new work area to update the UI:
        if can_save:
            # can save :)

            # update visibility and default value of the name field:
            name_is_used = "name" in self._current_env.work_template.keys
            name_is_optional = name_is_used and self._current_env.work_template.is_optional("name")
            self._ui.name_label.setVisible(name_is_used)
            self._ui.name_edit.setVisible(name_is_used)
            
            

            ext_is_used = "extension" in self._current_env.work_template.keys
            self._ui.file_type_label.setVisible(ext_is_used)
            self._ui.file_type_menu.setVisible(ext_is_used)

            version_is_used = "version" in self._current_env.work_template.keys            
            self._ui.version_label.setVisible(version_is_used)
            self._ui.version_spinner.setVisible(version_is_used)
        
        
    def _on_browser_file_selected(self, file, env):
        """
        """
        self._selected_file = file
        self._current_env = env
        self._on_work_area_changed()
        self._on_selected_file_changed()
        
    
    def _on_browser_file_double_clicked(self, file, env):
        """
        """
        self._selected_file = file
        self._current_env = env
        self._on_work_area_changed()
        self._on_selected_file_changed()
        self._on_save()
    
    def _on_browser_context_menu_requested(self, file, env, pnt):
        """
        """
        pass
    
    def _on_selected_file_changed(self):
        """
        """
        if self._selected_file and self._current_env:
            file_name = None
            
            # update the details based off the currently selected file:
            file_versions = self._file_model.get_file_versions(self._selected_file.key, self._current_env)
                
            #if "name" in self.
            
            # figure out the file name, version, etc.
            if self._selected_file.is_local:
                # selected file is actually local which is good!
                fields = self._current_env.work_template.get_fields(self._selected_file.path)
                file_name = fields.get("name")
            elif self._selected_file.is_published:
                # try to pull the name from the pubish template instead:
                fields = self._current_env.publish_template.get_fields(self._selected_file.published_path)
                file_name = fields.get("name")
            
            # update the UI with any additional details we obtained:    
            if file_name:
                self._ui.name_edit.setText(file_name)
            #
            self._ui.save_btn.setEnabled(True)
        else:
            self._ui.save_btn.setEnabled(False)
    
        
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
            print self._last_expanded_sz
            
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
        if not self._selected_file:
            return
        
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
        
"""
Probably not needed...

# name + version + type
|      Name: |[name]     | Version #: |[version]|
| File Type: |[file_type]|            |         |

# name + version
|      Name: |[name]     | Version #: |[version]|

# name + type
|      Name: |[name]                            |
| File Type: |[file_type]                       |

# type + version
| File Type: |[file_type]| Version #: |[version]|

# name
|      Name: |[name]                            |

# version
|   Version: |[version]                         |

# type
| File Type: |[file_type]                       |

control_placement = []
if name_is_used:
    if version_is_used:
        if ext_is_used:
            control_placement = [[self._ui.name_label, self._ui.name_edit, self._ui.version_label, self._ui.version_spinner],
                                 [self._ui.file_type_label, self._ui.file_type_menu]]
        else:
            control_placement = [[self._ui.name_label, self._ui.name_edit, self._ui.version_label, self._ui.version_spinner]]
    else:
        if ext_is_used:
            control_placement = [[self._ui.name_label, self._ui.name_edit],
                                 [self._ui.file_type_label, self._ui.file_type_menu]]
        else:
            control_placement = [[self._ui.name_label, self._ui.name_edit]]
else:
    if version_is_used:
        if ext_is_used:
            control_placement = [[self._ui.file_type_label, self._ui.file_type_menu, self._ui.version_label, self._ui.version_spinner]]
        else:
            control_placement = [[self._ui.version_label, self._ui.version_spinner]]
    else:
        if ext_is_used:
            control_placement = [[self._ui.file_type_label, self._ui.file_type_menu]]
        else:
            control_placement = []
"""        
        
        