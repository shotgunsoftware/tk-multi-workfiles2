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

import tank
from tank.platform.qt import QtCore, QtGui

class SaveAsForm(QtGui.QWidget):
    """
    UI for saving the current tank work file
    """
    
    @property
    def exit_code(self):
        return self._exit_code
    
    def __init__(self, preview_updater, is_publish, name_is_used, name, version_is_used, parent = None):
        """
        Construction
        
        :param preview_updater:    Thread used to update the preview fields when something is changed in the UI
        :param is_publish:         True if the scene being saved is a published file
        :param name_is_used:       True if the name is used in the work template and needs to be entered
        :param name:               Initial value for name field
        :param version_is_used:    True if version is used in the work template and can be set
        :param parent:             The parent QWisget for this UI
        """
        QtGui.QWidget.__init__(self, parent)

        self._exit_code = QtGui.QDialog.Rejected

        self._preview_updater = preview_updater
        if self._preview_updater:
            self._preview_updater.work_done.connect(self._preview_info_updated)
        
        self._reset_version = False
        self._launched_from_publish = is_publish
        self._name_is_used = name_is_used
        self._version_is_used = version_is_used
        
        # set up the UI
        from .ui.save_as_form import Ui_SaveAsForm
        self._ui = Ui_SaveAsForm()
        self._ui.setupUi(self)
        
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.continue_btn.clicked.connect(self._on_continue)
        self._ui.name_edit.textEdited.connect(self._on_name_edited)
        self._ui.name_edit.returnPressed.connect(self._on_name_return_pressed)
        self._ui.reset_version_cb.stateChanged.connect(self._on_reset_version_changed)

        self._ui.name_edit.setText(name)
        
        if not self._name_is_used:
            self._ui.name_label.hide()
            self._ui.name_edit.hide()
            
        if not self._name_is_used or not self._version_is_used:
            self._ui.reset_version_cb.hide()
            
        if self._name_is_used and not self._launched_from_publish:
            # make sure text in name edit is selected ready to edit:
            self._ui.name_edit.setFocus()
            self._ui.name_edit.selectAll()
            
        # initialize the preview info:
        self._preview_info_updated({}, {})
            
        # initialize line to be plain and the same colour as the text:        
        self._ui.break_line.setFrameShadow(QtGui.QFrame.Plain)
        clr = QtGui.QApplication.palette().text().color()
        self._ui.break_line.setStyleSheet("#break_line{color: rgb(%d,%d,%d);}" % (clr.red() * 0.75, clr.green() * 0.75, clr.blue() * 0.75))

        # finally, start preview info update in background            
        self._update_preview_info()
        
    def showEvent(self, e):
        """
        On first show, make sure that the name edit is focused:
        """
        self._ui.name_edit.setFocus()
        self._ui.name_edit.selectAll()
        QtGui.QWidget.showEvent(self, e)
        
    @property
    def name(self):
        """
        Get and set the name
        """
        return self._get_new_name()
    
    @property
    def reset_version(self):
        """
        Get and set if the version number should be reset
        """
        return self._should_reset_version()
    
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()
    
    def _on_continue(self):
        """
        Called when the continue button is clicked
        """
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
    
    def _on_name_edited(self, txt):
        self._update_preview_info()
        
    def _on_name_return_pressed(self):
        self._on_continue()
        
    def _on_reset_version_changed(self, state):
        if self._ui.reset_version_cb.isEnabled():
            self._reset_version = self._ui.reset_version_cb.isChecked()
        self._update_preview_info()
    
    def _get_new_name(self):
        name_str = self._ui.name_edit.text() or ""
        return self._safe_to_str(name_str).strip()
    
    def _safe_to_str(self, value):
        """
        safely convert the value to a string - handles
        QtCore.QString if usign PyQt
        """
        if isinstance(value, unicode):
            # encode to str utf-8
            return value.encode("utf-8")
        
        elif isinstance(value, str):
            # it's a string anyway so just return
            return value
        
        elif hasattr(QtCore, "QString"):
            # running PyQt!
            if isinstance(value, QtCore.QString):
                # QtCore.QString inherits from str but supports 
                # unicode, go figure!  Lets play safe and return
                # a utf-8 string
                return str(value.toUtf8())
        
        # For everything else, just return as string
        return str(value)
    
    def _should_reset_version(self):
        return self._reset_version
    
    def _update_preview_info(self):
        """
        
        """
        if self._preview_updater:
            self._preview_updater.do({"name":self._get_new_name(), "reset_version":self._should_reset_version()})
            
    def _preview_info_updated(self, details, result):
        """
        
        """
        path = result.get("path")
        msg = result.get("message")
        can_reset_version = result.get("can_reset_version")
        
        # update name and work area previews:
        path_preview = ""
        name_preview = ""
        if path:
            path_preview, name_preview = os.path.split(path)
        self._ui.filename_preview_label.setText(name_preview)
        self._ui.path_preview_edit.setText(path_preview)
        
        # update header:
        header_txt = ""
        if msg:
            if self._name_is_used:
                header_txt = "<p style='color:rgb(226, 146, 0)'>Warning: %s</p>" % msg
            else:
                header_txt = msg
        else:
            if self._launched_from_publish:
                header_txt = ("You are currently working on a file that has already been published!  "
                              "By clicking 'Save', the file will be copied into your work area as the "
                              "latest version and you can continue your work there.")
            else:
                if self._name_is_used:
                    header_txt = ("Type in a name below and Shotgun will save the current scene")
                else:
                    header_txt = ("Would you like Shotgun to save the current scene in your work area?")
        self._ui.header_label.setText(header_txt)
            
        # update reset version check box:
        if can_reset_version:
            self._ui.reset_version_cb.setChecked(self._reset_version)
            self._ui.reset_version_cb.setEnabled(True)
        else:
            self._ui.reset_version_cb.setEnabled(False)
            self._ui.reset_version_cb.setChecked(False)
        
        
    