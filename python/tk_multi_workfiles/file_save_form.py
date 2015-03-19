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

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .file_operation_form import FileOperationForm
from .ui.file_save_form import Ui_FileSaveForm

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
        FileOperationForm.__init__(self, parent)

        self._exit_code = QtGui.QDialog.Rejected
        self._last_expanded_sz = QtCore.QSize(600, 600)
        
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
        
        # finally, execute the init callback:
        if init_callback:
            init_callback(self)
        
    def _on_browser_file_selected(self, file):
        """
        """
        pass
    
    def _on_browser_file_double_clicked(self, file):
        """
        """
        pass
    
    def _on_browser_context_menu_requested(self, file, pnt):
        """
        """
        pass
        
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
        self._exit_code = QtGui.QDialog.Accepted
        self.close()