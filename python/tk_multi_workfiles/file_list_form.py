# Copyright (c) 2015 Shotgun Software Inc.
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
from .file_proxy_model import FileProxyModel

from .spinner_widget import SpinnerWidget


class FileGroupWidget(GroupWidgetBase):
    """
    """
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileGroupWidget()
        self._ui.setupUi(self)
        
        self._ui.expand_check_box.stateChanged.connect(self._on_expand_checkbox_state_changed)
        
        # replace the spinner widget with our SpinnerWidget widget:
        proxy_widget = self._ui.spinner
        proxy_size = proxy_widget.geometry()
        proxy_min_size = proxy_widget.minimumSize()
        
        spinner_widget = SpinnerWidget(self)
        spinner_widget.setMinimumSize(proxy_min_size)
        spinner_widget.setGeometry(proxy_size)        

        layout = self._ui.horizontalLayout
        idx = layout.indexOf(proxy_widget)
        layout.removeWidget(proxy_widget)
        layout.insertWidget(idx, spinner_widget)
        
        self._ui.spinner.setParent(None)
        self._ui.spinner.deleteLater()
        self._ui.spinner = spinner_widget
        
        self._show_msg = False

    def set_item(self, model_idx):
        """
        """
        label = model_idx.data()
        self._ui.expand_check_box.setText(label)
        
        # update if the spinner should be visible or not:
        search_status = model_idx.data(FileModel.SEARCH_STATUS_ROLE)
        if search_status == None:
            search_status = FileModel.SEARCH_COMPLETED
            
        # show the spinner if needed:
        self._ui.spinner.setVisible(search_status == FileModel.SEARCHING)
        
        search_msg = ""
        if search_status == FileModel.SEARCHING:
            search_msg = "Searching for files..."
        elif search_status == FileModel.SEARCH_COMPLETED:
            if not model_idx.model().hasChildren(model_idx):
                search_msg = "No files found!"
        elif search_status == FileModel.SEARCH_FAILED:
            search_msg = model_idx.data(FileModel.SEARCH_MSG_ROLE) or ""
        self._ui.msg_label.setText(search_msg)
                        
        self._show_msg = bool(search_msg)
                        
        show_msg = self._show_msg and self._ui.expand_check_box.checkState() == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)

    def set_expanded(self, expand=True):
        """
        """
        if (self._ui.expand_check_box.checkState() == QtCore.Qt.Checked) != expand:
            self._ui.expand_check_box.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)

    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        show_msg = self._show_msg and state == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)
        
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
        if not isinstance(widget, FileTile):
            return
        
        label = ""
        icon = None
        
        file_item = model_index.data(FileModel.FILE_ITEM_ROLE)
        if file_item:
            # build label:
            label = "<b>%s, v%03d</b>" % (file_item.name, file_item.version)
            if file_item.is_published:
                label += "<br>%s" % file_item.format_published_by_details()
            elif file_item.is_local:
                label += "<br>%s" % file_item.format_modified_by_details()

            # retrieve the icon:                
            icon = file_item.thumbnail
            #icon = model_index.data(QtCore.Qt.DecorationRole)
            
            #if not icon:
            #    # look for the most recent file that does have an icon:
            #    file_model = model_index.model()
            #    while isinstance(file_model, QtGui.QSortFilterProxyModel):
            #        file_model = file_model.sourceModel()
            #        
            #    if isinstance(file_model, FileModel):
            #        all_versions = file_model.get_file_versions(file_item.key)
            #        versions = sorted(all_versions.keys(), reverse=True)
            #        for v in versions:
            #            if file_item.version < v:
            #                continue
            #            
            #            if file_item.thumbnail_path:
            #                icon = QtGui.QIcon(file_item.thumbnail_path)
            #                break
        else:
            label = model_index.data()
            icon = model_index.data(QtCore.Qt.DecorationRole)

        # update widget:
        widget.title = label
        widget.set_thumbnail(icon)
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
    
    file_selected = QtCore.Signal(object)
    
    def __init__(self, search_label, show_work_files=True, show_publishes=False, show_all_versions=False, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._show_work_files = show_work_files
        self._show_publishes = show_publishes
        self._filter_model = None
        
        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
        
        self._ui.details_radio_btn.setEnabled(False) # (AD) - temp
        self._ui.details_radio_btn.toggled.connect(self._on_view_toggled)

        self._ui.all_versions_cb.setChecked(show_all_versions)
        self._ui.all_versions_cb.toggled.connect(self._on_show_all_versions_toggled)
        
        self._ui.file_list_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        
        item_delegate = TestItemDelegate(self._ui.file_list_view)
        self._ui.file_list_view.setItemDelegate(item_delegate)

    def set_model(self, model):
        """
        """
        show_all_versions = self._ui.all_versions_cb.isChecked()
        
        # create a filter model around the source model:
        self._filter_model = FileProxyModel(show_work_files=self._show_work_files, 
                                            show_publishes=self._show_publishes,
                                            show_all_versions = show_all_versions,
                                            parent=self)
        self._filter_model.setSourceModel(model)

        # set automatic sorting on the model:
        self._filter_model.sort(0, QtCore.Qt.DescendingOrder)
        self._filter_model.setDynamicSortFilter(True)

        # connect the views to the filtered model:        
        self._ui.file_list_view.setModel(self._filter_model)
        self._ui.file_details_view.setModel(self._filter_model)
        
        # connect to the selection model:
        selection_model = self._ui.file_list_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
        
    def _on_search_changed(self, search_text):
        """
        """
        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)
                
    def _on_view_toggled(self, checked):
        """
        """
        if self._ui.details_radio_btn.isChecked():
            self._ui.view_pages.setCurrentWidget(self._ui.details_page)
        else:
            self._ui.view_pages.setCurrentWidget(self._ui.list_page)
            
    def _on_show_all_versions_toggled(self, checked):
        """
        """
        self._filter_model.show_all_versions = checked
        
    def _on_selection_changed(self, selected, deselected):
        """
        """
        selected_index = None
        
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            selected_index = self._filter_model.mapToSource(selected_indexes[0])
            
        # emit selection_changed signal:            
        self.file_selected.emit(selected_index)        
        
        
        
        