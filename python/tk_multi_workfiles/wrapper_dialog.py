# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys

import sgtk
from sgtk.platform.qt import QtCore, QtGui 

class WrapperDialog(QtGui.QDialog):

    @staticmethod
    def show_modal(widget, parent, title=None, fixed_size=None):
        dlg = WrapperDialog(widget, parent, title, fixed_size)
        try:
            return dlg.exec_()
        finally:
            dlg.clean_up()
    
    def __init__(self, widget, parent, title=None, fixed_size=None):
        QtGui.QDialog.__init__(self, parent)
        
        self._widget = widget
        self._widget.closeEvent = lambda event, dh=widget.closeEvent: self._handle_widget_close(event, dh)
      
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._widget)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        
        if title:
            self.setWindowTitle(title)
        if fixed_size:
            self.setFixedSize(fixed_size)
    
    def clean_up(self):
        # ensure that dialog is safey cleaned up when running nuke on a Mac
        if sys.platform == "darwin" and sgtk.platform.current_engine().name == "tk-nuke":
            self.deleteLater()
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.clean_up()
         
    
    def _handle_widget_close(self, event, default_handler):
        """
        Callback from the hosted widget's closeEvent.
        Make sure that when a close() is issued for the hosted widget,
        the parent widget is closed too.
        """
        # execute default handler and stop if not accepted:
        if default_handler:
            default_handler(event)
            if not event.isAccepted():
                return
        else:
            event.accept()
        
        # use accepted as the default exit code
        exit_code = QtGui.QDialog.Accepted    

        # look if the hosted widget has an exit_code we should pick up
        if hasattr(self._widget, "exit_code"):
            exit_code = self._widget.exit_code
        
        self.done(exit_code)