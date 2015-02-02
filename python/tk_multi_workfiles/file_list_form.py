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

"""

import time
import math

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .file_model import FileModel
from .file_model_overlay_widget import FileModelOverlayWidget

from .ui.file_list_form import Ui_FileListForm

from .file_tile import FileTile
from .group_header_widget import GroupHeaderWidget

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")
WidgetDelegate = shotgun_view.WidgetDelegate

from .grouped_list_view import GroupListViewItemDelegate, GroupWidgetBase


from .ui.file_group_widget import Ui_FileGroupWidget
from .file_model import FileModel

class FileGroupWidget(GroupWidgetBase):
    """
    """
    _SPINNER_FPS = 20
    _SPINNER_LINE_WIDTH = 2
    _SPINNER_BORDER = 2
    _SPINNER_ARC_LENGTH = 280 * 16
    _SECONDS_PER_SPIN = 3
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileGroupWidget()
        self._ui.setupUi(self)
        
        self._ui.expand_check_box.stateChanged.connect(self._on_expand_checkbox_state_changed)
        
        self._show_spinner = False
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_animation)

    def _on_animation(self):
        """
        Spinner async callback to help animate the progress spinner.
        """
        # just force a repaint:    
        self.repaint()

    def paintEvent(self, event):
        """
        Render the UI.
        """
        if self._show_spinner:
            self._paint_spinner()

        GroupWidgetBase.paintEvent(self, event)
            
    def _paint_spinner(self):
        """
        """
        
        # calculate the spin angle as a function of the current time so that all spinners appear in sync!
        t = time.time()
        whole_seconds = int(t)
        p = (whole_seconds % FileGroupWidget._SECONDS_PER_SPIN) + (t - whole_seconds)
        angle = int((360 * p)/FileGroupWidget._SECONDS_PER_SPIN)

        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
            pen.setWidth(FileGroupWidget._SPINNER_LINE_WIDTH)
            painter.setPen(pen)
            
            border = FileGroupWidget._SPINNER_BORDER + int(math.ceil(FileGroupWidget._SPINNER_LINE_WIDTH / 2.0))
            r = self._ui.spinner.geometry()
            #painter.fillRect(r, QtGui.QColor("#000000"))
            r = r.adjusted(border, border, -border, -border)
            
            start_angle = -angle * 16
            painter.drawArc(r, start_angle, FileGroupWidget._SPINNER_ARC_LENGTH)
            
        finally:
            painter.end()

    def _toggle_spinner(self, show=True):
        """
        """
        self._show_spinner = show
        if self._show_spinner and self.isVisible():
            if not self._timer.isActive():
                self._timer.start(1000 / FileGroupWidget._SPINNER_FPS)
        else:
            if self._timer.isActive():
                self._timer.stop()
        
        
    def showEvent(self, event):
        self._toggle_spinner(self._show_spinner)
        #self._timer.start(1000 / FileGroupWidget._SPINNER_FPS)
        GroupWidgetBase.showEvent(self, event)
        
    def hideEvent(self, event):
        self._timer.stop()
        GroupWidgetBase.hideEvent(self, event)

    def set_item(self, model_idx):
        """
        """
        label = model_idx.data()
        self._ui.expand_check_box.setText(label)
        
        # update if the spinner should be visible or not:
        search_status = model_idx.data(FileModel.SEARCH_STATUS_ROLE)
        if search_status == None:
            search_status = FileModel.SEARCH_COMPLETED
            
        self._toggle_spinner(search_status == FileModel.SEARCHING)
        
        search_msg = ""
        if search_status == FileModel.SEARCHING:
            search_msg = "Searching for files..."
        elif search_status == FileModel.SEARCH_COMPLETED:
            if not model_idx.model().hasChildren(model_idx):
                search_msg = "No files found!"
        elif search_status == FileModel.SEARCH_FAILED:
            search_msg = model_idx.data(FileModel.SEARCH_MSG_ROLE) or ""
        self._ui.msg_label.setText(search_msg)
                        
        show_msg = bool(search_msg) and self._ui.expand_check_box.checkState() == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)
        

    def set_expanded(self, expand=True):
        """
        """
        self._ui.expand_check_box.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)

    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        self.toggle_expanded.emit(state != QtCore.Qt.Unchecked)        

class TestItemDelegate(GroupListViewItemDelegate):

    def __init__(self, view):
        GroupListViewItemDelegate.__init__(self, view)
        
        self._item_widget = None

    def create_group_widget(self, parent):
        return FileGroupWidget(parent)

    def _get_painter_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        return self._get_item_widget(parent)

    def _get_item_widget(self, parent):
        """
        """
        if not self._item_widget:
            self._item_widget = FileTile(parent)
        return self._item_widget

    def _setup_widget(self, widget, model_index, style_options):
        """
        """
        if isinstance(widget, FileTile):
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

    def sizeHint(self, style_options, model_index):
        """
        """
        if not model_index.isValid():
            return QtCore.QSize()
        
        if model_index.parent() != self.view.rootIndex():
            return self._get_item_widget(self.view).size()
        else:
            return GroupListViewItemDelegate.sizeHint(self, style_options, model_index)
        
    #def setModelData(self, editor, model, model_index):
    #    pass

class FileListForm(QtGui.QWidget):
    """
    """
    
    def __init__(self, search_label, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        
        #self._overlay_widget = FileModelOverlayWidget(parent = self._ui.view_pages)
        
        self._ui.details_radio_btn.setEnabled(False) # (AD) - temp
        self._ui.details_radio_btn.toggled.connect(self._on_view_toggled)
        
        item_delegate = TestItemDelegate(self._ui.file_list_view)
        self._ui.file_list_view.setItemDelegate(item_delegate)
        
                
    def _on_view_toggled(self, checked):
        """
        """
        if self._ui.details_radio_btn.isChecked():
            self._ui.view_pages.setCurrentWidget(self._ui.details_page)
        else:
            self._ui.view_pages.setCurrentWidget(self._ui.list_page)
            
    def set_model(self, model):
        """
        """
        self._ui.file_list_view.setModel(model)
        self._ui.file_details_view.setModel(model)
        #self._overlay_widget.set_model(model)
        
    def get_selection_model(self):
        """
        """
        return self._ui.file_list_view.selectionModel() 
        
        
        
        