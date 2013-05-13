"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

import os
import shutil
import urlparse
import urllib
        
import tank
from tank.platform.qt import QtCore, QtGui

from .work_file import WorkFile

class WorkFilesForm(QtGui.QWidget):
    """
    Primary work area UI
    """
    
    # signals
    open_file = QtCore.Signal(WorkFile)
    new_file = QtCore.Signal()
    show_in_fs = QtCore.Signal(bool, dict)
    
    def __init__(self, app, handler, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._app = app
        self._handler = handler

        # set up the UI
        from .ui.work_files_form import Ui_WorkFilesForm
        self._ui = Ui_WorkFilesForm()
        self._ui.setupUi(self)
        
        # patch up the lines to be the same colour as the font:
        clr = QtGui.QApplication.palette().color(QtGui.QPalette.Text)  
        rgb_str = "rgb(%d,%d,%d)" % (clr.red(), clr.green(), clr.blue())
          
        self._ui.entity_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.entity_line.setStyleSheet("#entity_line{color: %s;}" % rgb_str)
        self._ui.task_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.task_line.setStyleSheet("#task_line{color: %s;}" % rgb_str)
        
        ss = "{font-size: 14pt; border-style: dashed; border-width: 2px; border-radius: 3px; border-color: %s;}" % rgb_str
        self._ui.no_task_label.setStyleSheet("#no_task_label %s" % ss)
        self._ui.no_entity_label.setStyleSheet("#no_task_label %s" % ss)
        
        self._ui.show_in_fs_label.mousePressEvent = self._on_show_in_fs_mouse_press_event
        
        # update the style sheet for the work area form so it
        # becomes highlighted when hovering over it
        clr = QtGui.QApplication.palette().color(QtGui.QPalette.Window)
        clr = clr.lighter() if clr.lightness() < 128 else clr.darker()
        ss = self._ui.work_area_frame.styleSheet()
        ss = "%s #work_area_frame:hover {background-color: rgb(%d,%d,%d);}" % (ss, clr.red(), clr.green(), clr.blue())
        self._ui.work_area_frame.setStyleSheet(ss)
        
        # connect up controls:
        self._ui.work_area_frame.mousePressEvent = self._on_work_area_mouse_press_event
        self._ui.filter_combo.currentIndexChanged.connect(self._on_filter_selection_changed)

        self._ui.open_file_btn.clicked.connect(self._on_open_file)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)
        
        self._ui.file_list.action_requested.connect(self._on_open_file)
        self._ui.file_list.selection_changed.connect(self._on_file_selection_changed)

        self._ui.file_list.set_app(self._app)
        self._ui.file_list.open_previous_version.connect(self._on_open_previous_version)

        # set up the work area:
        ctx = self._handler.get_current_work_area() 
        self._set_work_area(ctx)
        
        self._on_file_selection_changed()
        
    def _on_show_in_fs_mouse_press_event(self, event):
        """
        
        """
        current_filter = self._get_current_filter()
        self.show_in_fs.emit(current_filter.get("show_local", False), current_filter.get("user"))
        
    def closeEvent(self, e):
        """
        Ensure everything is cleaned up when
        the widget is closed
        """
        self._ui.file_list.destroy()
        return QtGui.QWidget.closeEvent(self, e)
        
    def _on_open_file(self):
        # get the currently selected work file
        selected_file = self._ui.file_list.selected_file
        self.open_file.emit(selected_file)

    def _on_open_previous_version(self, file):
        self.open_file.emit(file)

    def _on_new_file(self):
        self.new_file.emit()
        
    def _set_work_area(self, ctx):
        """
        Set the current work area to the specified context.
        """
        # update work area info:
        self._update_work_area(ctx)
        
        # update the filter menu:
        self._update_filter_menu()
        
        # finally, update file list:
        self._refresh_file_list()
        
        # update new button enabled state
        can_do_new = self._handler.can_do_new_file()
        self._ui.new_file_btn.setEnabled(can_do_new)
        
    def _on_work_area_mouse_press_event(self, event):
        """
        Event triggered when mouse is pressed in the work area
        form
        """
        new_ctx = self._handler.change_work_area()
        if new_ctx:
            self._set_work_area(new_ctx)
        
    def _refresh_file_list(self):
        """
        Refresh the file list based on the current filter
        """
        # get the file filter:
        filter = self._get_current_filter()
        
        # clear and reload list:
        self._ui.file_list.clear()
        self._ui.file_list.load({"handler":self._handler, 
                                "user":filter.get("user"), 
                                "show_local":filter.get("show_local", False),
                                "show_publishes":filter.get("show_publishes", False)})
        
        self._on_file_selection_changed()
        
    def _on_filter_selection_changed(self, idx):
        """
        Called when the filter is changed
        """
        self._refresh_file_list()
        
    def _on_file_selection_changed(self):
        """
        
        """
        selected_file = self._ui.file_list.selected_file
        self._ui.open_file_btn.setEnabled(selected_file is not None)
            
    def _update_filter_menu(self):
        """
        Update the list of users to display work files for
        """
        users = self._handler.get_usersandbox_users()
        
        current_user = tank.util.get_shotgun_user(self._app.shotgun)
        
        # get selected filter:
        previous_filter = self._get_current_filter()
        
        filter_compare = lambda f1, f2: (f1.get("user", {}).get("id") == f2.get("user", {}).get("id")
                            and f1.get("show_local", False) == f2.get("show_local", False)
                            and f1.get("show_publishes", False) == f2.get("show_publishes", False))
        
        # clear menu:
        self._ui.filter_combo.clear()
        
        # add user work files item:
        self._ui.filter_combo.addItem("Show Files in my Work Area", ({"user":current_user, "show_local":True, "show_publishes":False}, ))
        selected_idx = 0
        
        # add publishes item:
        publishes_filter = {"show_local":False, "show_publishes":True}
        self._ui.filter_combo.addItem("Show Files in the Publish Area", (publishes_filter, ))
        if filter_compare(previous_filter, publishes_filter):
            selected_idx = 1
        
        # add rest of users
        if users:
            # add some separators!
            self._ui.filter_combo.insertSeparator(2)
        
            for user in users:
                if current_user is not None and user["id"] == current_user["id"]:
                    # already added
                    continue
            
                filter = {"user":user, "show_local":True, "show_publishes":False}
            
                if filter_compare(previous_filter, filter):
                    selected_idx = self._ui.filter_combo.count()
                
                self._ui.filter_combo.addItem("Show Files in %s's Work Area" % user["name"], (filter, ))
                
        # set the current index:
        self._ui.filter_combo.setCurrentIndex(selected_idx)
        
    def _get_current_filter(self):
        """
        Get the current filter
        """
        filter = {}
        idx = self._ui.filter_combo.currentIndex()
        if idx >= 0:
            filter = self._ui.filter_combo.itemData(idx)
            
            # convert from QVariant object if itemData is returned as such
            if hasattr(QtCore, "QVariant") and isinstance(filter, QtCore.QVariant):
                filter = filter.toPyObject()
            
            # filter is also a tuple ({}, ) to avoid PyQt QString conversion fun!
            filter = filter[0]
        
        return filter
        
    def _update_work_area(self, ctx):
        """
        A lot of this should be done in a worker thread!
        """
        # load and update entity & task details:
        task_header = "Task: -"
        task_details = ""
        task_thumbnail = QtGui.QPixmap()#":/res/thumb_empty.png")
                    
        if ctx and ctx.entity:
            # work area defined - yay!
            self._ui.entity_pages.setCurrentWidget(self._ui.entity_page)
            
            # header:
            entity_type_name = tank.util.get_entity_type_display_name(self._app.tank, ctx.entity.get("type"))
            self._ui.entity_label.setText("%s: %s" % (entity_type_name, ctx.entity.get("name") or "-"))
            self._ui.entity_label.setToolTip("%s" % ctx.entity.get("name", ""))
            
            # get additional details:
            sg_details = {}
            try:
                sg_details = self._app.shotgun.find_one(ctx.entity["type"], [["project", "is", ctx.project], ["id", "is", ctx.entity["id"]]], ["description", "image"])
            except:
                pass
            
            # thumbnail:
            entity_thumbnail = QtGui.QPixmap()
            entity_img_url = sg_details.get("image")
            if entity_img_url:
                thumbnail_path = self._download_thumbnail(entity_img_url)
                if thumbnail_path:
                    entity_thumbnail = QtGui.QPixmap(thumbnail_path)
            self._set_thumbnail(self._ui.entity_thumbnail, entity_thumbnail)
                                
            # description:
            self._ui.entity_description.setText(sg_details.get("description"))

            # task:
            if ctx.task:
                # have a task - double yay!!
                self._ui.task_pages.setCurrentWidget(self._ui.task_page)
                
                # header:
                self._ui.task_label.setText("Task: %s" % (ctx.task.get("name") or "-"))
                self._ui.task_label.setToolTip("%s" % ctx.task.get("name", ""))
                
                # get additional details:
                sg_details = {}
                try:
                    sg_details = self._app.shotgun.find_one("Task", [["project", "is", ctx.project], ["id", "is", ctx.task["id"]]], ["task_assignees", "sg_status_list"])
                except Exception, e:
                    pass
                
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
                self._ui.task_details.setText("Status: %s<br>Assigned to: %s" % (sg_details.get("sg_status_list"), ", ".join(assignees) if assignees else "-"))
                
            else:
                # task not chosen
                self._ui.task_pages.setCurrentWidget(self._ui.no_task_page)         
        else:
            # no work area defined!
            self._ui.entity_pages.setCurrentWidget(self._ui.no_entity_page)
        
    def _set_thumbnail(self, ctrl, pm):
        """
        Set thumbnail on control resizing as required. 
        """
        geom = ctrl.geometry()
        scaled_pm = pm.scaled(geom.width(), geom.height(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
        ctrl.setPixmap(scaled_pm)

    def _download_thumbnail(self, url):
        """
        Copied from browser widget...
        """
        # first check in our thumbnail cache
        url_obj = urlparse.urlparse(url)
        url_path = url_obj.path
        path_chunks = url_path.split("/")
        
        path_chunks.insert(0, self._app.cache_location)
        # now have something like ["/studio/proj/tank/cache/tk-framework-widget", "", "thumbs", "1", "2", "2.jpg"]
        
        # treat the list of path chunks as an arg list
        path_to_cached_thumb = os.path.join(*path_chunks)
        
        if os.path.exists(path_to_cached_thumb):
            # cached! sweet!
            return path_to_cached_thumb
        
        # ok so the thumbnail was not in the cache. Get it.
        try:
            (temp_file, stuff) = urllib.urlretrieve(url)
        except Exception, e:
            print "Could not download data from the url '%s'. Error: %s" % (url, e)
            return None

        # now try to cache it
        try:
            self._app.ensure_folder_exists(os.path.dirname(path_to_cached_thumb))
            shutil.copy(temp_file, path_to_cached_thumb)
            # as a tmp file downloaded by urlretrieve, permissions are super strict
            # modify the permissions of the file so it's writeable by others
            os.chmod(path_to_cached_thumb, 0666)
           
        except Exception, e:
            print "Could not cache thumbnail %s in %s. Error: %s" % (url, path_to_cached_thumb, e)
            return temp_file

        return path_to_cached_thumb
