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
        
import tank
from tank.platform.qt import QtCore, QtGui

shotgun_data = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")

class OpenFileForm(QtGui.QWidget):
    """
    UI for changing the version of the current work file
    """
    
    # the mode that the UI should operate in.
    OPEN_WORKFILE_MODE, OPEN_PUBLISH_MODE, OPEN_PUBLISH_NO_READONLY_MODE = range(3)
    
    # the result returned by the dialog (starts from 2 as the regular return codes are 0 or 1)
    OPEN_PUBLISH, OPEN_PUBLISH_READONLY, OPEN_WORKFILE = range(2,5)
    
    @property
    def exit_code(self):
        return self._exit_code    
    
    def __init__(self, app, work_file, publish_file, mode, next_version, publish_requires_copy=True, parent=None):
        """
        Construction

        :param app:                     The App bundle that this UI belongs to
        :param work_file:               The work file that can be opened
        :param publish_file:            The publish file that can be opened
        :param mode:                    The mode that the UI will be run in
        :param next_version:            The next available version number for a file being opened
        :param publish_requires_copy:   True if opening the published file requires copying it to the work area
        :param parent:                  The parent QWidget for this UI
        """
        QtGui.QWidget.__init__(self, parent)

        self._app = app
        self._work_file = work_file
        self._publish_file = publish_file
        self._exit_code = QtGui.QDialog.Rejected
        self._mode = mode
        self._next_version = next_version
        self._publish_requires_copy = publish_requires_copy
        
        # set up the UI
        from .ui.open_file_form import Ui_OpenFileForm
        self._ui = Ui_OpenFileForm()
        self._ui.setupUi(self)
        
        clr = QtGui.QApplication.palette().color(QtGui.QPalette.Window)
        bg_clr = clr.darker() if clr.lightness() < 128 else clr.lighter()
        hl_clr = clr.lighter() if clr.lightness() < 128 else clr.darker()
        
        ss = ("#%%s {"
              "background-color: rgb(%d,%d,%d,32);"
              "border-radius: 4px;"
              "border-style: Solid;"
              "border-width: 1px;"
              "border-color: rgb(%d,%d,%d,32);"
              "}" % (bg_clr.red(), bg_clr.green(), bg_clr.blue(), bg_clr.red(), bg_clr.green(), bg_clr.blue()))
        ss += ("#%%s:hover {"
              "background-color: rgb(%d,%d,%d,255);"
              "border-color: rgb(%d,%d,%d,255);"
              "}" % (hl_clr.red(), hl_clr.green(), hl_clr.blue(), hl_clr.red(), hl_clr.green(), hl_clr.blue()))
        ss += ("#%%s:focus {"
              "border-color: rgb(%d,%d,%d,255);"
              "}" % (hl_clr.red(), hl_clr.green(), hl_clr.blue()))
        self._ui.publish_frame.setStyleSheet(ss % ("publish_frame", "publish_frame", "publish_frame"))
        self._ui.publish_ro_frame.setStyleSheet(ss % ("publish_ro_frame", "publish_ro_frame", "publish_ro_frame"))
        self._ui.work_file_frame.setStyleSheet(ss % ("work_file_frame", "work_file_frame", "work_file_frame"))
               
        clr = QtGui.QApplication.palette().color(QtGui.QPalette.Text)  
        rgb_str = "rgb(%d,%d,%d)" % ((clr.red() * 0.75, clr.green() * 0.75, clr.blue() * 0.75))
        self._ui.break_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.break_line.setStyleSheet("#break_line{color: %s;}" % rgb_str)
        self._ui.publish_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.publish_line.setStyleSheet("#publish_line{color: %s;}" % rgb_str)
        self._ui.work_file_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.work_file_line.setStyleSheet("#work_file_line{color: %s;}" % rgb_str)
        self._ui.name_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.name_line.setStyleSheet("#name_line{color: %s;}" % rgb_str)
        self._ui.publish_ro_line.setFrameShadow(QtGui.QFrame.Plain)
        self._ui.publish_ro_line.setStyleSheet("#publish_ro_line{color: %s;}" % rgb_str)
               
        # update details:
        self._update_details()
               
        # connect up the buttons
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        
        self._ui.publish_frame.mousePressEvent = self._on_publish_mouse_press_event
        self._ui.work_file_frame.mousePressEvent = self._on_work_file_mouse_press_event
        self._ui.publish_ro_frame.mousePressEvent = self._on_publish_ro_mouse_press_event
        
    def _update_details(self):
        """
        Update the details for the publish and work file
        """
        # name
        self._ui.name_label.setText("<big><b>%s</b></big>" % self._publish_file.name)
        
        # title:
        title_str = ""
        if self._mode == OpenFileForm.OPEN_WORKFILE_MODE:
            title_str = "A more recent Published version of this file is available!"
        else:
            if self._work_file:
                title_str = "You have a more recent version of this file available in your Work Area!"
            else:
                title_str = "Open published file!"
        self._ui.title_label.setText("<big>%s</big>" % title_str)
        
        # work file details:
        if self._work_file:
            wf_title_str = ""
            wf_tooltip_str = ""
            if self._mode == OpenFileForm.OPEN_WORKFILE_MODE:
                wf_title_str = "Open the older Work File instead?"
                wf_tooltip_str = "Click to open the older Work File"
            else:
                wf_title_str = "Continue working from the latest Work File?"
                wf_tooltip_str = "Click to open the latest Work File"
            self._ui.work_file_title_label.setText("<big>%s</big>" % wf_title_str)
            self._ui.work_file_frame.setToolTip(wf_tooltip_str)
            
            wf_details = ("<b>Version v%03d</b>" % self._work_file.version)
            wf_details += "<br>" + self._work_file.format_modified_by_details()
            self._ui.work_file_details.setText(wf_details)

            if self._work_file.thumbnail:
                thumbnail_path = self._download_thumbnail(self._work_file.thumbnail)
                if thumbnail_path:
                    self._set_thumbnail(self._ui.work_file_thumbnail, QtGui.QPixmap(thumbnail_path))
        
        # publish details:
        pf_title_str = ""
        pf_tooltip_str = ""
        pf_ro_title_str = ""
        if self._mode == OpenFileForm.OPEN_WORKFILE_MODE:
            pf_title_str = "Continue working from the latest Publish?"
            pf_tooltip_str = "Click to open the latest Publish"
        else:
            if self._work_file:
                pf_title_str = "Open the older Publish instead?"
                pf_ro_title_str = "Open the older Publish read-only?"
                pf_tooltip_str = "Click to open the older Publish"
            else:
                pf_title_str = "Continue working from the Publish?"
                pf_ro_title_str = "Open the Publish read-only?"
                pf_tooltip_str = "Click to open the Publish"
        self._ui.publish_title_label.setText("<big>%s</big>" % pf_title_str)
        self._ui.publish_ro_title_label.setText("<big>%s</big>" % pf_ro_title_str)
        self._ui.publish_frame.setToolTip(pf_tooltip_str)
        self._ui.publish_ro_frame.setToolTip("%s read-only" % pf_tooltip_str)
        
        publish_details = ("<b>Version v%03d</b>" % self._publish_file.version)
        publish_details += "<br>" + self._publish_file.format_published_by_details()
        publish_details += "<br>"
        publish_details += "<br><b>Description:</b>"
        publish_details += "<br>" + self._publish_file.format_publish_description()
        self._ui.publish_details.setText(publish_details)
        
        if self._publish_requires_copy:
            self._ui.publish_note.setText("<small>(Note: The published file will be copied to "
                                          "your work area as version v%03d and then opened)</small>" % self._next_version)
        else:
            self._ui.publish_note.setText("")
        
        if self._publish_file.thumbnail:
            thumbnail_path = self._download_thumbnail(self._publish_file.thumbnail)
            if thumbnail_path:
                self._set_thumbnail(self._ui.publish_thumbnail, QtGui.QPixmap(thumbnail_path))
        
        # order widgets and set tab-order        
        self._ui.verticalLayout.setEnabled(False)
        try:
            ordered_widgets = []
            if self._mode == OpenFileForm.OPEN_PUBLISH_MODE:
                ordered_widgets = [self._ui.work_file_frame,
                                   self._ui.or_label_a,
                                   self._ui.publish_frame,
                                   self._ui.or_label_b,
                                   self._ui.publish_ro_frame]
                    
                self._ui.work_file_frame.setVisible(self._work_file is not None)
                self._ui.or_label_a.setVisible(self._work_file is not None)
                self._ui.or_label_b.setVisible(True)         
                self._ui.publish_ro_frame.setVisible(True)
                    
                QtGui.QWidget.setTabOrder(self._ui.work_file_frame, self._ui.publish_frame)
                QtGui.QWidget.setTabOrder(self._ui.publish_frame, self._ui.publish_ro_frame)
            elif self._mode == OpenFileForm.OPEN_PUBLISH_NO_READONLY_MODE:
                ordered_widgets = [self._ui.work_file_frame,
                                   self._ui.or_label_a,
                                   self._ui.publish_frame,
                                   self._ui.or_label_b,
                                   self._ui.publish_ro_frame]
                    
                self._ui.work_file_frame.setVisible(self._work_file is not None)
                self._ui.or_label_a.setVisible(self._work_file is not None)
                self._ui.or_label_b.setVisible(False)         
                self._ui.publish_ro_frame.setVisible(False)
                    
                QtGui.QWidget.setTabOrder(self._ui.work_file_frame, self._ui.publish_frame)
                QtGui.QWidget.setTabOrder(self._ui.publish_frame, self._ui.publish_ro_frame)                
            else:
                ordered_widgets = [self._ui.publish_frame,
                                   self._ui.or_label_a,
                                   self._ui.work_file_frame,
                                   self._ui.or_label_b,
                                   self._ui.publish_ro_frame]

                self._ui.work_file_frame.setVisible(True)
                self._ui.or_label_a.setVisible(True)
                self._ui.or_label_b.setVisible(False)         
                self._ui.publish_ro_frame.setVisible(False)
       
                QtGui.QWidget.setTabOrder(self._ui.publish_frame, self._ui.work_file_frame)
                QtGui.QWidget.setTabOrder(self._ui.work_file_frame, self._ui.publish_ro_frame)
            
            for widget in ordered_widgets:
                self._ui.verticalLayout.removeWidget(widget)
                self._ui.verticalLayout.addWidget(widget)
        finally:
            self._ui.verticalLayout.setEnabled(True)
        
    def _exit(self, exit_code):
        self._exit_code = exit_code
        self.close()
        
    def keyPressEvent(self, event):
        """
        
        """
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self._ui.publish_frame.hasFocus():
                self._exit(OpenFileForm.OPEN_PUBLISH)
            elif self._ui.work_file_frame.hasFocus():
                self._exit(OpenFileForm.OPEN_WORKFILE)
            elif self._ui.publish_ro_frame.hasFocus():
                self._exit(OpenFileForm.OPEN_PUBLISH_READONLY)

        QtGui.QWidget.keyPressEvent(self, event)
        
    def _on_publish_mouse_press_event(self, event):
        self._exit(OpenFileForm.OPEN_PUBLISH)
        
    def _on_publish_ro_mouse_press_event(self, event):
        self._exit(OpenFileForm.OPEN_PUBLISH_READONLY)
        
    def _on_work_file_mouse_press_event(self, event):
        self._exit(OpenFileForm.OPEN_WORKFILE)        
        
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit(QtGui.QDialog.Rejected)
        
    def _set_thumbnail(self, ctrl, pm):
        """
        Set thumbnail on control resizing as required. 
        """
        geom = ctrl.geometry()
        scaled_pm = pm.scaled(geom.width(), geom.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
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
                
        
        
        