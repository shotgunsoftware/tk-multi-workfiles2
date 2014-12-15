import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.group_header_widget import Ui_GroupHeaderWidget

class GroupHeaderWidget(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_GroupHeaderWidget()
        self._ui.setupUi(self)
        
        