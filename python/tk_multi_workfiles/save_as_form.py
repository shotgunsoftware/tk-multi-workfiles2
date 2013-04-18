"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
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
    
    def __init__(self, preview_updater, is_publish, name, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._preview_updater = preview_updater
        if self._preview_updater:
            self._preview_updater.work_done.connect(self._preview_info_updated)
        
        self._reset_version = False
        self._launched_from_publish = is_publish
        
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
        if not self._launched_from_publish:
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
        return self._ui.name_edit.text().strip()
    
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
            header_txt = "<p style='color:rgb(226, 146, 0)'>Warning: %s</p>" % msg
        else:
            if self._launched_from_publish:
                header_txt = ("You are currently working on a file that has already been published!  "
                              "By clicking continue, the file will be copied into your work area and "
                              "you can continue your work there.")
            else:
                header_txt = ("Type in a name below and Tank will save the current scene")
        self._ui.header_label.setText(header_txt)
            
        # update reset version check box:
        if can_reset_version:
            self._ui.reset_version_cb.setChecked(self._reset_version)
            self._ui.reset_version_cb.setEnabled(True)
        else:
            self._ui.reset_version_cb.setEnabled(False)
            self._ui.reset_version_cb.setChecked(False)
        
        
    