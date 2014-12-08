import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.test_form import Ui_TestForm


class TestModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        
        
        

class TestForm(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_TestForm()
        self._ui.setupUi(self)
        
        # set up the model:
        self._model = self._init_model()
        
        # set up the list view:
        self._ui.listView.setModel(self._model)
        
        self._ui.treeView.setModel(self._model)
        
        for row in range(self._model.rowCount()):
            idx = self._model.index(row,0)
            self._expand_recursive(self._ui.treeView, idx)
        
    def _init_model(self):
        model = TestModel(self)
        
        items = {
            "Headmasters":["Brainstorm", "Chromedome", "Hardhead"],
            "Targetmasters":["Kup", "Hot-rod", "Blur"],
            "Primes":["Optimus", "Omega", "Nova"],
            "Lost Light":["Rodimus", "Fort Max"]
        }
        
        for name, group in items.iteritems():
            header_item = QtGui.QStandardItem(name)
            model.appendRow(header_item)
            
            for tf in group:
                header_item.appendRow(QtGui.QStandardItem(tf))
        
        return model
        
    def _expand_recursive(self, view, idx, expand=True):
        
        model = idx.model()
        
        if not model.hasChildren(idx):
            return
        
        view.setExpanded(idx, expand)
        
        for row in range(model.rowCount(idx)):
            child_idx = idx.child(row, 0)
            self._expand_recursive(view, child_idx, expand)
        
        
        