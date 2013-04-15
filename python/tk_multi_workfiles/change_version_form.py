"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

import tank
from tank.platform.qt import QtCore, QtGui

class ChangeVersionForm(QtGui.QWidget):
    """
    UI for changing the version of the current work file
    """
    
    @property
    def exit_code(self):
        return self._exit_code
    
    def __init__(self, checker, current_version, new_version, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
    
        self._exit_code = QtGui.QDialog.Rejected
        
        # set up the availability checker background worker
        self._availability_checker = checker
        if self._availability_checker:
            self._availability_checker.work_done.connect(self._version_availability_updated)
        
        # set up the UI
        from .ui.change_version_form import Ui_ChangeVersionForm
        self._ui = Ui_ChangeVersionForm()
        self._ui.setupUi(self)
        
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.change_version_btn.clicked.connect(self._on_change_version)

        self._ui.new_version_edit.setValidator(QtGui.QIntValidator(0, 99999, self))
        self._ui.new_version_edit.textEdited.connect(self._on_new_version_changed)

        self._ui.current_version_label.setText("v%03d" % current_version)
        self._ui.new_version_edit.setText("%d" % new_version)

        # make sure UI is up-to-date:        
        self._on_new_version_changed("")
        
    @property
    def new_version(self):
        """
        Get the new version
        """
        return self._get_new_version()
    
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()

    def _on_change_version(self):
        """
        Called when the change version button is clicked
        """
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
    
    def _on_new_version_changed(self, txt):
        """
        Called when the new version is changed
        """
        if self._availability_checker:
            self._ui.warning_label.setText("")#"Updating...")
            self._availability_checker.do(self._get_new_version())
        
    def _version_availability_updated(self, version, msg):
        """
        Triggered when the availability checker has finished
        checking a version
        """
        
        # make sure that the version matches the current
        # new version
        new_version = self._get_new_version()
        if new_version != version:
            return

        # update message:
        if msg:
            msg = "<font color='orange'>Warning: %s</font>" % msg
            
        self._ui.warning_label.setText(msg)
    
    def _get_new_version(self):
        """
        Get the new version from the UI
        """
        new_version = -1
        try:
            new_version = int(self._ui.new_version_edit.text())
        except ValueError:
            pass
        return new_version    
    
    
    
    
    
    