import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.test_form import Ui_FileTile

class FileTile(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileTile()
        self._ui.setupUi(self)