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
import shutil
import urlparse
import urllib
        
import tank
from tank.platform.qt import QtCore, QtGui

from .file_list_view import FileListView
from .file_filter import FileFilter

shotgun_data = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")

class WorkFilesForm(QtGui.QWidget):
    """
    Primary work area UI
    """
    
    # signals - note, 'object' is used to avoid 
    # issues with PyQt when None is passed
    open_publish = QtCore.Signal(object, object, bool)#FileItem, FileItem, bool
    open_workfile = QtCore.Signal(object, object, bool)#FileItem, FileItem, bool
    open_previous_publish = QtCore.Signal(object)#FileItem
    open_previous_workfile = QtCore.Signal(object)#FileItem
    
    new_file = QtCore.Signal()
    
    show_in_fs = QtCore.Signal()
    show_in_shotgun = QtCore.Signal(object)#FileItem
    
    def __init__(self, app, handler, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._app = app
        self._handler = handler
        self._ignore_filter_changes = True

        # set up the UI
        from .ui.work_files_form import Ui_WorkFilesForm
        self._ui = Ui_WorkFilesForm()
        self._ui.setupUi(self)
        
        # patch up the lines to be the same colour as the font:
        clr = QtGui.QApplication.palette().color(QtGui.QPalette.Text)  
        rgb_str = "rgb(%d,%d,%d)" % (clr.red(), clr.green(), clr.blue())
        self._ui.project_line.setStyleSheet("#project_line{background-color: %s;}" % rgb_str)
        self._ui.entity_line.setStyleSheet("#entity_line{background-color: %s;}" % rgb_str)
        self._ui.task_line.setStyleSheet("#task_line{background-color: %s;}" % rgb_str)
       
        ss = "{font-size: 14pt; border-style: dashed; border-width: 2px; border-radius: 3px; border-color: %s;}" % rgb_str
        self._ui.no_project_label.setStyleSheet("#no_project_label %s" % ss)
        self._ui.no_task_label.setStyleSheet("#no_task_label %s" % ss)
        self._ui.no_entity_label.setStyleSheet("#no_entity_label %s" % ss)
        
        # set up the work area depending on if it's possible to change it:
        if self._handler.can_change_work_area():
            # update the style sheet for the work area form so it
            # becomes highlighted when hovering over it
            # test for lightness ahead of use to stay compatible with Qt 4.6.2
            if hasattr(clr, 'lightness'):
                clr = QtGui.QApplication.palette().color(QtGui.QPalette.Window)
                clr = clr.lighter() if clr.lightness() < 128 else clr.darker()
                ss = self._ui.work_area_frame.styleSheet()
                ss = "%s #work_area_frame:hover {background-color: rgb(%d,%d,%d);}" % (ss, clr.red(), clr.green(), clr.blue())
                self._ui.work_area_frame.setStyleSheet(ss)
            
            self._ui.work_area_frame.setCursor(QtCore.Qt.PointingHandCursor)
            self._ui.work_area_frame.setToolTip("Click to Change Work Area...")
            self._ui.no_change_frame.setVisible(False)
            
            self._ui.work_area_frame.mousePressEvent = self._on_work_area_mouse_press_event
        else:
            self._ui.work_area_frame.setCursor(QtCore.Qt.ArrowCursor)
            self._ui.work_area_frame.setToolTip("The Work Area is locked and cannot be changed")
            self._ui.no_change_frame.setVisible(True)
        
        # connect up controls:
        self._ui.show_in_fs_label.mousePressEvent = self._on_show_in_fs_mouse_press_event
            
        self._ui.filter_combo.currentIndexChanged.connect(self._on_filter_selection_changed)

        self._ui.open_file_btn.clicked.connect(self._on_open_file)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)
        
        self._ui.file_list.action_requested.connect(self._on_open_file)
        self._ui.file_list.selection_changed.connect(self._on_file_selection_changed)

        self._ui.file_list.set_app(self._app)
        self._ui.file_list.open_previous_workfile.connect(self._on_open_previous_workfile)
        self._ui.file_list.open_previous_publish.connect(self._on_open_previous_publish)
        self._ui.file_list.view_in_shotgun.connect(self._on_view_in_shotgun)

        # set up the work area:
        ctx = self._handler.get_current_work_area() 
        self._set_work_area(ctx)
        
        self._on_file_selection_changed()
        
    @property
    def filter(self):
        return self._get_current_filter()
        
    def _on_view_in_shotgun(self, file):
        self.show_in_shotgun.emit(file)
        
    def _on_show_in_fs_mouse_press_event(self, event):
        """
        Emit event when the user clicks the show in file system link:
        """
        self.show_in_fs.emit()
        
    def closeEvent(self, e):
        """
        Ensure everything is cleaned up when
        the widget is closed
        """
        self._ui.file_list.destroy()
        return QtGui.QWidget.closeEvent(self, e)
        
    def _on_open_file(self):
        """
        """
        # get the currently selected work file
        
        work_file = self._ui.file_list.selected_work_file
        published_file = self._ui.file_list.selected_published_file
                
        current_filter = self._get_current_filter()
        if not current_filter:
            return
        
        if current_filter.mode == FileFilter.WORKFILES_MODE:
            self.open_workfile.emit(work_file, published_file, False)            
        else: # current_filter.mode == FileFilter.PUBLISHES_MODE:
            self.open_publish.emit(published_file, work_file, False)

    def _on_open_previous_workfile(self, file):
        """
        """
        self.open_previous_workfile.emit(file)

    def _on_open_previous_publish(self, file):
        """
        """
        self.open_previous_publish.emit(file)

    def _on_new_file(self):
        """
        """
        self.new_file.emit()
        
    def _set_work_area(self, ctx):
        """
        Set the current work area to the specified context.
        """
        
        self._app.log_debug("Setting the work area in the File Manager UI")# to %s..." % ctx)
        
        # update work area info:
        self._app.log_debug(" - Updating Work Area")
        self._update_work_area(ctx)
        
        # update the filter menu being sure that this
        # doesn't trigger a file list refresh as this
        # would result in a double refresh!
        self._app.log_debug(" - Updating Filter menu")
        self._ignore_filter_changes = True
        try:
            self._update_filter_menu()
        finally:
            self._ignore_filter_changes = False    
        
        # finally, update file list:
        self._app.log_debug(" - Refreshing File List")
        self._refresh_file_list()
        
        # update new button enabled state
        can_do_new = self._handler.can_do_new_file()
        self._ui.new_file_btn.setEnabled(can_do_new)
        
        self._app.log_debug("Finished setting the work area in the File Manager UI!")
        
    def _on_work_area_mouse_press_event(self, event):
        """
        Event triggered when mouse is pressed in the work area
        form
        """
        new_ctx = self._handler.select_work_area()
        if new_ctx:
            self._set_work_area(new_ctx[0])
        
    def _refresh_file_list(self):
        """
        Refresh the file list based on the current filter
        """
        # get the file filter:
        filter = self._get_current_filter()
        if not filter:
            return
        
        # hide/show the show-in-filesystem link:
        self._ui.show_in_fs_label.setVisible(filter.show_in_file_system)
        
        # clear and reload list:
        self._ui.file_list.clear()
        self._ui.file_list.load({"handler":self._handler, "filter":filter})
        
        self._on_file_selection_changed()
        
    def _on_filter_selection_changed(self, idx):
        """
        Called when the filter is changed
        """
        if self._ignore_filter_changes:
            # ignore this change to the filter selection
            return

        self._refresh_file_list()
        
    def _on_file_selection_changed(self):
        """
        
        """
        something_selected = (self._ui.file_list.selected_published_file is not None 
                              or self._ui.file_list.selected_work_file is not None) 
        self._ui.open_file_btn.setEnabled(something_selected)
            
    def _update_filter_menu(self):
        """
        Update the list of users to display work files for
        """
        # get list of filters from handler:
        filters = self._handler.get_file_filters()
        
        # get selected filter:
        previous_filter = self._get_current_filter()
        
        # clear menu:
        self._ui.filter_combo.clear()
        
        # add back in filters:
        selected_idx = 0
        separator_count = 0
        for filter in filters:
            
            if filter == "separator":
                # special 'filter' signifying a separator should be added
                # - don't add it yet though in case there aren't any more
                # non separator items following!
                separator_count += 1
                continue
            
            if not filter.menu_label:
                # filter doesn't have a menu label - bad!
                continue

            # add any separators:
            while separator_count > 0:
                separator_count -= 1
                self._ui.filter_combo.insertSeparator(self._ui.filter_combo.count())
                
            # see if this is the previously selected filter:
            if filter == previous_filter:
                selected_idx = self._ui.filter_combo.count()

            # add filter:            
            self._ui.filter_combo.addItem(filter.menu_label, filter)

        # set the current index:
        self._ui.filter_combo.setCurrentIndex(selected_idx)
        
    def _get_current_filter(self):
        """
        Get the current filter
        """
        filter = None
        idx = self._ui.filter_combo.currentIndex()

        if idx >= 0:
            filter = self._ui.filter_combo.itemData(idx)
            
            # convert from QVariant object if itemData is returned as such
            if hasattr(QtCore, "QVariant") and isinstance(filter, QtCore.QVariant):
                filter = filter.toPyObject()
            
        return filter
        
    def _update_work_area(self, ctx):
        """
        A lot of this should be done in a worker thread!
        """
        if ctx and ctx.project:
            # context has a project - that's something at least!
            self._ui.project_pages.setCurrentWidget(self._ui.project_page)

            # get additional details:
            sg_details = {}
            try:
                sg_details = self._app.shotgun.find_one("Project", 
                                                        [["id", "is", ctx.project["id"]]], 
                                                        ["sg_description", "image", "code"])
            except:
                pass
            
            # header:
            project_name = ctx.project.get("name") or sg_details.get("code")
            self._ui.project_label.setText("Project: %s" % (project_name or "-"))
            self._ui.project_frame.setToolTip("%s" % (project_name or ""))
            
            # thumbnail:
            project_thumbnail = QtGui.QPixmap()
            project_img_url = sg_details.get("image")
            if project_img_url:
                thumbnail_path = self._download_thumbnail(project_img_url)
                if thumbnail_path:
                    project_thumbnail = QtGui.QPixmap(thumbnail_path)
            self._set_thumbnail(self._ui.project_thumbnail, project_thumbnail)
                                
            # description:
            desc = sg_details.get("sg_description") or "<i>No description was entered for this Project</i>"
            self._ui.project_description.setText(desc)
                
            if ctx.entity:
                # work area defined - yay!
                self._ui.entity_pages.setCurrentWidget(self._ui.entity_page)
                self._ui.entity_pages.setVisible(True)

                # get any extra fields that have been defined for this entity type.  This will be a dictionary
                # of label:field pairs for the current entity type:      
                extra_fields = self._app.get_setting("sg_entity_type_extra_display_fields", {}).get(ctx.entity["type"], {})
                
                # get additional details:
                sg_details = {}
                try:
                    sg_details = self._app.shotgun.find_one(ctx.entity["type"], 
                                                            [["project", "is", ctx.project], ["id", "is", ctx.entity["id"]]], 
                                                            ["description", "image", "code"] + extra_fields.values())
                except:
                    pass
    
                # header:
                entity_type_name = tank.util.get_entity_type_display_name(self._app.tank, ctx.entity.get("type"))
                entity_name = ctx.entity.get("name") or sg_details.get("code")
                self._ui.entity_label.setText("%s: %s" % (entity_type_name, entity_name or "-"))
                self._ui.entity_frame.setToolTip("%s" % (entity_name or ""))
                
                # thumbnail:
                entity_thumbnail = QtGui.QPixmap()
                entity_img_url = sg_details.get("image")
                if entity_img_url:
                    thumbnail_path = self._download_thumbnail(entity_img_url)
                    if thumbnail_path:
                        entity_thumbnail = QtGui.QPixmap(thumbnail_path)
                self._set_thumbnail(self._ui.entity_thumbnail, entity_thumbnail)
                                    
                # description including the display of extra fields:
                extra_info = ", ".join(["%s: %s" % (label, str(sg_details.get(field))) 
                                        for label, field in extra_fields.iteritems()])                
                desc = ""
                if extra_info:
                    desc += "(%s)<br>" % extra_info
                desc += sg_details.get("description") or ("<i>No description was entered for this %s</i>" % entity_type_name)
                self._ui.entity_description.setText(desc)
    
                # task:
                if ctx.task:
                    # have a task - double yay!!
                    self._ui.task_pages.setCurrentWidget(self._ui.task_page)
                    self._ui.task_pages.setVisible(True)
    
                    # get additional details:
                    sg_details = {}
                    try:
                        sg_details = self._app.shotgun.find_one("Task", 
                                                                [["project", "is", ctx.project], ["id", "is", ctx.task["id"]]], 
                                                                ["task_assignees", "step.Step.code", "content"])
                    except Exception, e:
                        pass
                    
                    # header:
                    task_name = ctx.task.get("name") or sg_details.get("content")
                    self._ui.task_label.setText("Task: %s" % (task_name or "-"))
                    self._ui.task_frame.setToolTip("%s" % (task_name or ""))
                    
                    # thumbnail:
                    task_thumbnail = QtGui.QPixmap()
                    task_assignees = sg_details.get("task_assignees", [])
                    if len(task_assignees) > 0:
                        user_id = task_assignees[0]["id"]
                        
                        sg_user_details = {}
                        try:
                            sg_user_details = self._app.shotgun.find_one("HumanUser", [["id", "is", user_id]], ["image"])
                        except Exception, e:
                            pass
                        
                        if sg_user_details:
                            img_url = sg_user_details.get("image")
                            if img_url:
                                thumbnail_path = self._download_thumbnail(img_url)
                                if thumbnail_path:
                                    task_thumbnail = QtGui.QPixmap(thumbnail_path)
                                
                    self._set_thumbnail(self._ui.task_thumbnail, task_thumbnail)
                    
                    # details
                    assignees = []
                    for assignee in sg_details.get("task_assignees", []):
                        name = assignee.get("name")
                        if name:
                            assignees.append(name)
                    assignees_str = ", ".join(assignees) if assignees else "-"
                    step_str = sg_details.get("step.Step.code")
                    if step_str is None:
                        step_str = "-"
                    self._ui.task_description.setText("Assigned to: %s<br>Pipeline Step: %s" % (assignees_str, step_str))
                    
                else:
                    # task not chosen
                    if not self._handler.can_change_work_area():
                        self._ui.task_pages.setVisible(False)
                    else:
                        self._ui.task_pages.setCurrentWidget(self._ui.no_task_page)
            else:
                # no entity defined!
                if not self._handler.can_change_work_area():
                    self._ui.entity_pages.setVisible(False)
                else:
                    self._ui.entity_pages.setCurrentWidget(self._ui.no_entity_page)
        else:
            # no project defined!
            self._ui.project_pages.setCurrentWidget(self._ui.no_project_page)
        
    def _set_thumbnail(self, ctrl, pm):
        """
        Set thumbnail on control resizing as required. 
        """
        geom = ctrl.geometry()
        scaled_pm = pm.scaled(geom.width(), geom.height(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
        ctrl.setPixmap(scaled_pm)

    def _download_thumbnail(self, url):
        """
        Download a thumbnail from the specified url
        
        :param url:    The url of the thumbnail to download
        :returns:      Path to the downloaded thumbnail on disk
        """
        try:
            path_to_cached_thumb = shotgun_data.ShotgunDataRetriever.download_thumbnail(url, self._app)
        except Exception, e:
            self._app.log_info("Could not get thumbnail for url '%s'. Error: %s" % (url, e))
            path_to_cached_thumb = None
        
        return path_to_cached_thumb
        
