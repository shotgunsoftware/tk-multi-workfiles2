import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.test_form import Ui_TestForm

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")
WidgetDelegate = shotgun_view.WidgetDelegate


from .file_tile import FileTile
from .group_header_widget import GroupHeaderWidget

class GroupListViewItemDelegate(WidgetDelegate):
    """
    """
    def __init__(self, view):
        """
        """
        WidgetDelegate.__init__(self, view)
        
        self._group_widget = None
        self._group_widget_size = None
        self._item_widget = None
        self._item_widget_size = None
    
    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
        
    def _create_group_widget(self, parent):
        """
        """
        raise NotImplementedError()
    
    def _create_item_widget(self, parent):
        """
        """
        raise NotImplementedError()
        
    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
        
    def _get_painter_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            # we need a group widget:
            if not self._group_widget:
                self._group_widget = self._create_group_widget(parent)
                self._group_widget_size = self._group_widget.size()
            return self._group_widget
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            # we need an item widget:
            if not self._item_widget:
                self._item_widget = self._create_item_widget(parent)
                self._item_widget_size = self._item_widget.size()
            return self._item_widget
    
    def _create_editor_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        
        #print "CREATING EDITOR WIDGET"
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            return self._create_group_widget(parent)
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            return self._create_item_widget(parent)
            
    def sizeHint(self, style_options, model_index):
        """
        """
        if not model_index.isValid():
            return QtCore.QSize()
        
        # ensure we have a painter widget for this model index:
        self._get_painter_widget(model_index, self.view)
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            return self._group_widget_size
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            return self._item_widget_size
        
        return QtCore.QSize()
        
        

class TestItemDelegate(GroupListViewItemDelegate):

    def __init__(self, view):
        GroupListViewItemDelegate.__init__(self, view)

    def _create_group_widget(self, parent):
        """
        """
        return GroupHeaderWidget(parent)
    
    def _create_item_widget(self, parent):
        """
        """
        return FileTile(parent)

    def _setup_widget(self, widget, model_index, style_options):
        """
        """
        if isinstance(widget, GroupHeaderWidget):
            # update group widget:
            widget.label = model_index.data()
        elif isinstance(widget, FileTile):
            # update item widget:
            widget.title = model_index.data()
            widget.selected = (style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected 

    def _on_before_paint(self, widget, model_index, style_options):
        """
        """
        self._setup_widget(widget, model_index, style_options) 

    def _on_before_selection(self, widget, model_index, style_options):
        """
        """
        self._setup_widget(widget, model_index, style_options)
        
    def setModelData(self, editor, model, model_index):
        pass

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
        
        item_delegate = TestItemDelegate(self._ui.listView)
        self._ui.listView.setItemDelegate(item_delegate)    
        
        item_delegate = TestItemDelegate(self._ui.treeView)
        self._ui.treeView.setItemDelegate(item_delegate)
        
        item_delegate = TestItemDelegate(self._ui.customView)
        self._ui.customView.setItemDelegate(item_delegate)
        
        self._ui.listView.setModel(self._model)        
        self._ui.treeView.setModel(self._model)
        self._ui.customView.setModel(self._model)
        
        for row in range(self._model.rowCount()):
            idx = self._model.index(row,0)
            self._expand_recursive(self._ui.treeView, idx)
            #self._expand_recursive(self._ui.customView, idx)
        
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
        
        
        