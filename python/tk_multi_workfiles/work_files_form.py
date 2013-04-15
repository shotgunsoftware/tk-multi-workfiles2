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
    change_work_area = QtCore.Signal()
    
    open_file = QtCore.Signal(WorkFile)
    open_publish = QtCore.Signal(WorkFile)
    new_file = QtCore.Signal()
    
    def __init__(self, app, handler, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._app = app
        self._handler = handler

        self._current_ctx = None
    
        # set up the UI
        from .ui.work_files_form import Ui_WorkFilesForm
        self._ui = Ui_WorkFilesForm()
        self._ui.setupUi(self)
        
        # connect up controls:
        self._ui.change_work_area_btn.clicked.connect(self._on_change_work_area)
        self._ui.filter_combo.currentIndexChanged.connect(self._on_filter_selection_changed)

        self._ui.open_file_btn.clicked.connect(self._on_open_file)
        self._ui.new_file_btn.clicked.connect(self._on_new_file)
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        
        self._ui.file_list.action_requested.connect(self._on_open_file)

        self._ui.file_list.set_app(self._app)
        
        
    def closeEvent(self, e):
        """
        Ensure everything is cleaned up when
        the widget is closed
        """
        self._ui.file_list.destroy()
        return QtGui.QWidget.closeEvent(self, e)
        
    def set_work_area(self, ctx):
        """
        Set the current work area to the specified context.
        """
        # update work area info:
        self._update_work_area(ctx)
        
        # update the filter menu:
        self._update_filter_menu()
        
        # finally, update file list:
        self._refresh_file_list()
        
    def _on_open_file(self):
        # get the currently selected work file
        selected_file = self._ui.file_list.selected_file
        self.open_file.emit(selected_file)

    def _on_new_file(self):
        self.new_file.emit()
        
    def _on_cancel(self):
        """
        Just close window
        """
        self.close()
        
    def _on_change_work_area(self):
        self.change_work_area.emit()
        
    def _refresh_file_list(self):
        """
        Refresh the file list based on the current filter
        """
        # get the file filter:
        filter = self._get_current_filter()
        
        # clear and reload list:
        self._ui.file_list.clear()
        self._ui.file_list.load({"handler":self._handler, "user":filter.get("user"), "publishes":filter.get("publishes", False)})
        
    def _on_filter_selection_changed(self, idx):
        """
        Called when the filter is changed
        """
        self._refresh_file_list()
        
    def _update_filter_menu(self):
        """
        Update the list of users to display work files for
        """
        users = self._handler.get_usersandbox_users()
        
        current_user = tank.util.get_shotgun_user(self._app.shotgun)
        
        # get selected filter:
        previous_filter = self._get_current_filter()
        
        filter_compare = lambda f1, f2: f1.get("user") == f2.get("user") and f1.get("publishes") == f2.get("publishes")        
        
        # clear menu:
        self._ui.filter_combo.clear()
        
        # add user work files item:
        self._ui.filter_combo.addItem("My Work Files", {"user":current_user, "publishes":False})
        selected_idx = 0
        
        # add publishes item:
        publishes_filter = {"publishes":True}
        self._ui.filter_combo.addItem("Published Files", publishes_filter)
        if filter_compare(previous_filter, publishes_filter):
            selected_idx = 1
        
        # add some separators!
        self._ui.filter_combo.insertSeparator(2)
        self._ui.filter_combo.insertSeparator(3)
        
        # add rest of users
        if users:
            for user in users:
                if user["id"] == current_user["id"]:
                    # already added
                    continue
            
                filter = {"user":user}
            
                if filter_compare(previous_filter, filter):
                    selected_idx = self._ui.filter_combo.count()
                
                self._ui.filter_combo.addItem("Work Files for %s" % user["name"], filter)
                
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
        return filter
        
    def _update_work_area(self, ctx):
        """
        A lot of this should be done in a worker thread!
        """
        self._current_ctx = ctx
        
        # load and update entity & task details:
        entity_details = "<big>Entity: -</big>"
        entity_thumbnail = QtGui.QPixmap(":/res/thumb_empty.png")
        task_details = "<big>Task: -</big>"
        task_thumbnail = QtGui.QPixmap(":/res/thumb_empty.png")
                    
        if ctx:
            if ctx.entity:
                entity_type_name = tank.util.get_entity_type_display_name(self._app.tank, ctx.entity.get("type"))
                entity_details = "<big>%s: %s</big>" % (entity_type_name, ctx.entity.get("name"))
                
                # get additional details:
                sg_details = {}
                try:
                    sg_details = self._app.shotgun.find_one(ctx.entity["type"], [["project", "is", ctx.project], ["id", "is", ctx.entity["id"]]], ["description", "image"])
                except:
                    pass
                entity_desc = sg_details.get("description")
                if entity_desc:
                    entity_details += "<br>%s" % entity_desc
                
                entity_img_url = sg_details.get("image")
                if entity_img_url:
                    thumbnail_path = self._download_thumbnail(entity_img_url)
                    if thumbnail_path:
                        entity_thumbnail = QtGui.QPixmap(thumbnail_path)
    
            if ctx.task:
                task_details = "<big>Task: %s</big>" % (ctx.task["name"])
                
                sg_details = {}
                try:
                    sg_details = self._app.shotgun.find_one("Task", [["project", "is", ctx.project], ["id", "is", ctx.task["id"]]], ["task_assignees", "sg_status_list"])
                except Exception, e:
                    pass
                
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
                
        self._ui.entity_details.setText(entity_details)
        self._set_thumbnail(self._ui.entity_thumbnail, entity_thumbnail)

        self._ui.task_details.setText(task_details)
        self._set_thumbnail(self._ui.task_thumbnail, task_thumbnail)
        
        # update work area details:
        work_area_path = self._handler.get_work_area_path()
        publish_area_path = self._handler.get_publish_area_path()
        work_area_details = "<b>Work Area:</b><br>%s<br><br><b>Publish Area:</b><br>%s<br>" % (work_area_path if work_area_path else "<i>Unknown</i>", 
                                                                                     publish_area_path if publish_area_path else "<i>Unknown</i>")
        self._ui.work_area_details.setText(work_area_details)

    def _set_thumbnail(self, ctrl, pm):
        """
        Set thumbnail on control resizing as required. 
        """
        geom = ctrl.geometry()
        scaled_pm = pm.scaled(geom.width(), geom.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
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
