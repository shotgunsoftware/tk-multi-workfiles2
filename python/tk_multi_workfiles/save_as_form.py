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
        
        # set up the UI
        from .ui.save_as_form import Ui_SaveAsForm
        self._ui = Ui_SaveAsForm()
        self._ui.setupUi(self)
        
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.continue_btn.clicked.connect(self._on_continue)
        self._ui.name_edit.textEdited.connect(self._on_name_edited)
        self._ui.name_edit.returnPressed.connect(self._on_name_return_pressed)
        self._ui.reset_version_cb.stateChanged.connect(self._on_reset_version_changed)
        
        header_txt = ""
        if is_publish:
            header_txt = ("You are currently working on a file that has already been published!  "
                          "By clicking continue, the file will be copied into your work area and "
                          "you can continue your work there.")
        else:
            header_txt = ("You are basing your new file on the contents of the current scene.  "
                          "The scene will be saved with the file name you specify below.")
        self._ui.header_label.setText(header_txt)
        self._ui.name_edit.setText(name)
        self._ui.name_edit.setFocus()
        self._ui.name_edit.selectAll()
        self._ui.msg_frame.hide()
        self._ui.filename_preview_label.setText("")
        self._ui.path_preview_edit.setText("")
        self._ui.reset_version_cb.setChecked(self._reset_version)
            
        self._update_preview_info()
        
    def showEvent(self, e):
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
        
        path_preview = ""
        name_preview = ""
        if path:
            path_preview, name_preview = os.path.split(path)
            
        self._ui.filename_preview_label.setText(name_preview)
        self._ui.path_preview_edit.setText(path_preview)
        
        if msg:
            #msg = "<p style='color:rgb(200, 200, 50)'><b>Info:</b>  <i>%s</i></p>" % msg
            self._ui.warning_label.setText(msg)
            self._ui.msg_frame.show()
        else:
            self._ui.msg_frame.hide()
            
        if can_reset_version:
            self._ui.reset_version_cb.setChecked(self._reset_version)
            self._ui.reset_version_cb.setEnabled(True)
        else:
            self._ui.reset_version_cb.setEnabled(False)
            self._ui.reset_version_cb.setChecked(False)
        
        
        
    