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

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupedListView = views.GroupedListView

from ..file_model import FileModel
from ..ui.file_list_form import Ui_FileListForm
#from .group_header_widget import GroupHeaderWidget
from .file_proxy_model import FileProxyModel
from .file_list_item_delegate import FileListItemDelegate

from ..util import get_model_data

class FileListForm(QtGui.QWidget):
    """
    """
    
    file_selected = QtCore.Signal(object, object)
    file_double_clicked = QtCore.Signal(object, object)
    file_context_menu_requested = QtCore.Signal(object, object, QtCore.QPoint)
    
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
        self._ui.file_list_view.doubleClicked.connect(self._on_item_double_clicked)
        
        self._ui.file_list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ui.file_list_view.customContextMenuRequested.connect(self._on_context_menu_requested)
        
        item_delegate = FileListItemDelegate(self._ui.file_list_view)
        self._ui.file_list_view.setItemDelegate(item_delegate)

    @property
    def work_files_visible(self):
        """
        """
        return self._show_work_files

    @property
    def publishes_visible(self):
        """
        """
        return self._show_publishes

    @property
    def selected_file(self):
        """
        """
        selection_model = self._ui.file_list_view.selectionModel()
        if not selection_model:
            return None
        
        selected_indexes = selection_model.selectedIndexes()
        if len(selected_indexes) != 1:
            return None
                
        file = get_model_data(selected_indexes[0], FileModel.FILE_ITEM_ROLE)

        return file

    @property
    def selected_file_environment(self):
        """
        """
        selection_model = self._ui.file_list_view.selectionModel()
        if not selection_model:
            return None
        
        selected_indexes = selection_model.selectedIndexes()
        if len(selected_indexes) != 1:
            return None
                
        env = get_model_data(selected_indexes[0], FileModel.ENVIRONMENT_ROLE)

        return env

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

    def _on_context_menu_requested(self, pnt):
        """
        """
        # get the item under the point:
        idx = self._ui.file_list_view.indexAt(pnt)
        if not idx or not idx.isValid():
            return
        
        # get the file from the index:
        file = get_model_data(idx, FileModel.FILE_ITEM_ROLE)
        if not file:
            return

        env = get_model_data(idx, FileModel.ENVIRONMENT_ROLE)

        # remap the point from the source widget:
        pnt = self.sender().mapTo(self, pnt)
        
        # emit a more specific signal:
        self.file_context_menu_requested.emit(file, env, pnt)
        
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
        
    def _on_item_double_clicked(self, idx):
        """
        """
        item_type = get_model_data(idx, FileModel.NODE_TYPE_ROLE)
        if item_type == FileModel.FOLDER_NODE_TYPE:
            # selection is a folder so move into that folder
            # TODO
            pass
        elif item_type == FileModel.FILE_NODE_TYPE:
            # this is a file so perform the default action for the file
            selected_file = get_model_data(idx, FileModel.FILE_ITEM_ROLE)
            env = get_model_data(idx, FileModel.ENVIRONMENT_ROLE)
            self.file_double_clicked.emit(selected_file, env)        
        
    def _on_selection_changed(self, selected, deselected):
        """
        """
        selected_index = None
        
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            selected_index = self._filter_model.mapToSource(selected_indexes[0])
            
        selected_file = None
        env = None
        if selected_index:
            # extract the file item from the index:
            selected_file = get_model_data(selected_index, FileModel.FILE_ITEM_ROLE)
            env = get_model_data(selected_index, FileModel.ENVIRONMENT_ROLE)

        self.file_selected.emit(selected_file, env)
        
        
        
        