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
    
    def __init__(self, current_version, new_version, parent = None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
    
        self._exit_code = QtGui.QDialog.Rejected
        
        # set up the UI
        from .ui.change_version_form import Ui_ChangeVersionForm
        self._ui = Ui_ChangeVersionForm()
        self._ui.setupUi(self)
        
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.change_version_btn.clicked.connect(self._on_change_version)

        self._ui.new_version_edit.setValidator(QtGui.QIntValidator(0, 99999, self))

        self._ui.current_version_label.setText("v%03d" % current_version)
        self._ui.new_version_edit.setText("%d" % new_version)
        
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
    
    
    
    
    
    