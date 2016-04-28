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
Custom widget that can display a list of work files/publishes in a couple of
different views with options to show all versions or just the latest.
"""
import weakref

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..file_model import FileModel
from ..ui.file_list_form import Ui_FileListForm
from .file_proxy_model import FileProxyModel
from .file_list_item_delegate import FileListItemDelegate
from ..util import get_model_data, map_to_source, get_source_model

class FileListForm(QtGui.QWidget):
    """
    Main file list form class
    """
    # Selection mode.
    # - USER_SELECTED:   The user manually changed the selected file by clicking or navigating
    #                    using the mouse.
    # - SYSTEM_SELECTED: The system changed the selection, either because of a filter change, an
    #                    asyncronous data load, etc.
    (USER_SELECTED, SYSTEM_SELECTED) = range(2)

    # Signal emitted whenever the selected file changes in one of the file views
    file_selected = QtCore.Signal(object, object, int)# file, env, selection mode

    # Signal emitted whenever a file is double-clicked
    file_double_clicked = QtCore.Signal(object, object)# file, env

    # Signal emitted whenever a context menu is required for a file
    file_context_menu_requested = QtCore.Signal(object, object, QtCore.QPoint)# file, env, pos

    def __init__(self, parent, search_label, file_filters, show_work_files=True, show_publishes=False):
        """
        Construction
        
        :param search_label:    The hint label to be displayed on the search control
        :show_work_files:       True if work files should be displayed in this control, otherwise False
        :show_publishes:        True if publishes should be displayed in this control, otherwise False
        :param parent:          The parent QWidget for this control
        """
        QtGui.QWidget.__init__(self, parent)

        # keep track of the file to select when/if it appears in the attached model
        self._file_to_select = None
        # and keep track of the currently selected item
        self._current_item_ref = None

        self._file_filters = file_filters
        if self._file_filters:
            self._file_filters.changed.connect(self._on_file_filters_changed)
            self._file_filters.available_users_changed.connect(self._on_file_filters_available_users_changed)

        self._show_work_files = show_work_files
        self._show_publishes = show_publishes

        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)

        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)

        self._ui.all_versions_cb.setChecked(file_filters.show_all_versions)
        self._ui.all_versions_cb.toggled.connect(self._on_show_all_versions_toggled)

        self._ui.user_filter_btn.available_users = self._file_filters.available_users
        self._ui.user_filter_btn.selected_users = self._file_filters.users
        self._ui.user_filter_btn.users_selected.connect(self._on_user_filter_btn_users_selected)
        # user filter button is hidden until needed
        self.enable_user_filtering_widget(False)

        self._ui.file_list_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self._ui.file_list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ui.file_list_view.customContextMenuRequested.connect(self._on_context_menu_requested)

        # we want to handle double-click on items but we only want double-clicks to work when using
        # the left mouse button.  To achieve this we connect to the doubleClicked slot but also install
        # an event filter that will swallow any non-left-mouse-button double-clicks.
        self._ui.file_list_view.doubleClicked.connect(self._on_item_double_clicked)
        self._ui.file_list_view.viewport().installEventFilter(self)

        # Note, we have to keep a handle to the item delegate to help GC
        self._item_delegate = FileListItemDelegate(self._ui.file_list_view)
        self._ui.file_list_view.setItemDelegate(self._item_delegate)

    def shut_down(self):
        """
        Clean up as much as we can to help the gc once the widget is finished with.
        """
        signals_blocked = self.blockSignals(True)
        try:
            # clear any references:
            self._file_to_select = None
            self._current_item_ref = None
            self._file_filters = None

            # clear the selection:
            if self._ui.file_list_view.selectionModel():
                self._ui.file_list_view.selectionModel().clear()

            # detach the filter model from the views.  Note, this code assumes the same filter view
            # has been applied to both the list and the details view - if this isn't the case then
            # this code will need updating.
            view_model = self._ui.file_list_view.model() or self._ui.file_details_view.model()
            if view_model:
                self._ui.file_list_view.setModel(None)
                self._ui.file_details_view.setModel(None)
                if isinstance(view_model, FileProxyModel):
                    view_model.setSourceModel(None)
                    view_model = None

            # detach and clean up the item delegate:
            self._ui.file_list_view.setItemDelegate(None)
            if self._item_delegate:
                self._item_delegate.setParent(None)
                self._item_delegate.deleteLater()
                self._item_delegate = None

        finally:
            self.blockSignals(signals_blocked)

    @property
    def work_files_visible(self):
        """
        Property to use to inspect if work files are visible in the current view or not

        :returns:   True if work files are visible, otherwise False
        """
        return self._show_work_files

    @property
    def publishes_visible(self):
        """
        Property to use to inspect if publishes are visible in the current view or not

        :returns:   True if publishes are visible, otherwise False
        """
        return self._show_publishes

    @property
    def selected_file(self):
        """
        Property to use to query the file and the environment details for that file 
        that are currently selected in the control.

        :returns:   A tuple containing (FileItem, WorkArea) or (None, None)
                    if nothing is selected.
        """
        selected_file = None
        env_details = None

        selection_model = self._ui.file_list_view.selectionModel()
        if selection_model:
            selected_indexes = selection_model.selectedIndexes()
            if len(selected_indexes) == 1:
                selected_file = get_model_data(selected_indexes[0], FileModel.FILE_ITEM_ROLE)
                env_details = get_model_data(selected_indexes[0], FileModel.WORK_AREA_ROLE)

        return (selected_file, env_details)

    def enable_show_all_versions(self, enable):
        """
        """
        if enable:
            self._ui.all_versions_cb.show()
            self._on_show_all_versions_toggled(self._ui.all_versions_cb.isChecked())
        else:
            self._ui.all_versions_cb.hide()
            self._on_show_all_versions_toggled(False)

    def show_user_filtering_widget(self, is_visible):
        """
        Displays or hides the user filtering widget.

        :param is_visible: If True, the user filtering widget will be shown.
        """
        self._ui.user_filter_btn.setVisible(is_visible)

    def enable_user_filtering_widget(self, is_enabled):
        """
        Displays or hides the user filtering widget.

        :param is_visible: If True, the user filtering widget will be shown.
        """
        if self._show_publishes and not self._show_work_files:
            sandbox_type = "publish "
        elif not self._show_publishes and self._show_work_files:
            sandbox_type = "work file "
        else:
            sandbox_type = ""

        if is_enabled:
            self._ui.user_filter_btn.setToolTip("Click to see the list of %ssandboxes available for this context." % sandbox_type)
        else:
            self._ui.user_filter_btn.setToolTip("There are no %ssandboxes available for this context." % sandbox_type)

        self._ui.user_filter_btn.setEnabled(is_enabled)

    def select_file(self, file_item, context):
        """
        Select the specified file in the control views if possible.

        :param file_item:   The file to select
        :param context:     The work area the file to select should be found in
        """
        # reset the current selection and get the previously selected item:
        prev_selected_item = self._reset_selection()

        # update the internal tracking info:
        self._file_to_select = (file_item, context)
        self._current_item_ref = None

        # update the selection - this will emit a file_selected signal if
        # the selection is changed as a result of the overall call to select_file
        self._update_selection(prev_selected_item)

    def set_model(self, model):
        """
        Set the current file model for the control

        :param model:    The FileModel model to attach to the control to
        """
        if True:
            # create a filter model around the source model:
            filter_model = FileProxyModel(self,
                                          filters = self._file_filters,
                                          show_work_files=self._show_work_files,
                                          show_publishes=self._show_publishes)
            filter_model.rowsInserted.connect(self._on_filter_model_rows_inserted)
            filter_model.setSourceModel(model)
    
            # set automatic sorting on the model:
            filter_model.sort(0, QtCore.Qt.DescendingOrder)
            filter_model.setDynamicSortFilter(True)
    
            # connect the views to the filtered model:        
            self._ui.file_list_view.setModel(filter_model)
            self._ui.file_details_view.setModel(filter_model)
        else:
            # connect the views to the model:
            self._ui.file_list_view.setModel(model)
            self._ui.file_details_view.setModel(model)

        # connect to the selection model:
        selection_model = self._ui.file_list_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    def eventFilter(self, obj, event):
        """
        Overriden from base class - filters events on QObjects that this instance is installed as 
        an event filter for.  Used to swallow non-left-mouse-button double-clicks in the file list 
        view.

        :param obj:     The QObject that events are being filtered for
        :param event:   The QEvent to filter
        :returns:       True if the event should be consumed and blocked for further use otherwise
                        False if this method ignores the event 
        """
        if obj == self._ui.file_list_view.viewport():
            if (event.type() == QtCore.QEvent.MouseButtonDblClick
                and event.button() != QtCore.Qt.LeftButton):
                # supress double-clicks that aren't from the left mouse button as this
                # can feel very odd to the user!
                return True
        # we ignore all other events
        return False

    def _update_selection(self, prev_selected_item=None):
        """
        Update the selection to either the to-be-selected file if set or the current item if known.  The 
        current item is the item that was last selected but which may no longer be visible in the view due 
        to filtering.  This allows it to be tracked so that the selection state is correctly restored when 
        it becomes visible again.

        :param prev_selected_item:  The item that was previously selected (if any).  If, at the end of this
                                    method the selection is different then a file_selected signal will be
                                    emitted
        """
        # we want to make sure we don't emit any signals whilst we are 
        # manipulating the selection:
        signals_blocked = self.blockSignals(True)
        try:
            # try to get the item to select:
            item = None
            if self._file_to_select:
                # we know about a file we should try to select:
                src_model = get_source_model(self._ui.file_list_view.model())
                file_item, _ = self._file_to_select
                items = src_model.items_from_file(file_item)
                item = items[0] if items else None
            elif self._current_item_ref:
                # no item to select but we do know about a current item:
                item = self._current_item_ref()

            if item:
                idx = item.index()
                if isinstance(self._ui.file_list_view.model(), QtGui.QAbstractProxyModel):
                    idx = self._ui.file_list_view.model().mapFromSource(idx)
                if idx.isValid():
                    # make sure the item is expanded and visible in the list:
                    self._ui.file_list_view.scrollTo(idx)

                    # select the item:
                    selection_flags = QtGui.QItemSelectionModel.Clear | QtGui.QItemSelectionModel.SelectCurrent 
                    self._ui.file_list_view.selectionModel().select(idx, selection_flags)
        finally:
            self.blockSignals(signals_blocked)

            # if the selection is different to the previously selected item then we
            # will emit a file_selected signal:
            selected_item = self._get_selected_item()
            if id(selected_item) != id(prev_selected_item):
                # emit a selection changed signal:
                selected_file = None
                env_details = None
                if selected_item:
                    # extract the file item from the index:
                    selected_file = get_model_data(selected_item, FileModel.FILE_ITEM_ROLE)
                    env_details = get_model_data(selected_item, FileModel.WORK_AREA_ROLE)

                # emit the signal
                self.file_selected.emit(selected_file, env_details, FileListForm.SYSTEM_SELECTED)

    def _on_file_filters_changed(self):
        """
        Slot triggered whenever the file filters emits the changed signal.
        """
        # update UI based on the new filter settings:
        self._ui.all_versions_cb.setChecked(self._file_filters.show_all_versions)
        self._ui.search_ctrl.search_text = (self._file_filters.filter_reg_exp.pattern() 
                                                if self._file_filters.filter_reg_exp else "")

        self._ui.user_filter_btn.selected_users = self._file_filters.users

    def _on_file_filters_available_users_changed(self, users):
        """
        Slot triggered when the list of available users in the file filters change.

        :param users:   The new list of available users
        """
        # update user filter button
        self._ui.user_filter_btn.available_users = users

    def _on_context_menu_requested(self, pnt):
        """
        Slot triggered when a context menu has been requested from one of the file views.  This
        will collect information about the item under the cursor and emit a file_context_menu_requested
        signal.

        :param pnt: The position for the context menu relative to the source widget
        """
        # get the item under the point:
        idx = self._ui.file_list_view.indexAt(pnt)
        if not idx or not idx.isValid():
            return

        # get the file from the index:
        file_item = get_model_data(idx, FileModel.FILE_ITEM_ROLE)
        if not file_item:
            return

        # ...and the env details:
        env_details = get_model_data(idx, FileModel.WORK_AREA_ROLE)

        # remap the point from the source widget:
        pnt = self.sender().mapTo(self, pnt)

        # emit a more specific signal:
        self.file_context_menu_requested.emit(file_item, env_details, pnt)

    def _get_selected_item(self):
        """
        Get the currently selected item.

        :returns:   The currently selected model item if any
        """
        item = None
        selection_model = self._ui.file_list_view.selectionModel()
        if selection_model:
            indexes = selection_model.selectedIndexes()
            if len(indexes) == 1:
                src_idx = map_to_source(indexes[0])
                item = src_idx.model().itemFromIndex(src_idx)
        return item

    def _reset_selection(self):
        """
        Reset the current selection, returning the currently selected item if any.  This
        doesn't result in any signals being emitted by the current selection model.

        :returns:   The selected item before the selection was reset if any
        """
        selection_model = self._ui.file_list_view.selectionModel()
        if not selection_model:
            return None

        prev_selected_item = self._get_selected_item()
        # reset the current selection without emitting any signals:
        selection_model.reset()

        return prev_selected_item

    def _on_filter_model_rows_inserted(self, parent, first, last):
        """
        Slot triggered when new rows are inserted into the filter model.  This allows us
        to update the selection if a new row matches the task-to-select.

        :param parent_idx:  The parent model index of the rows that were inserted
        :param first:       The first row id inserted
        :param last:        The last row id inserted
        """
        # try to select the current file from the new items in the model:
        prev_selected_item = self._get_selected_item()
        self._update_selection(prev_selected_item)

    def _on_search_changed(self, search_text):
        """
        Slot triggered when the search text has been changed.

        :param search_text: The new search text
        """
        # reset the current selection and get the previously selected item:
        prev_selected_item = self._reset_selection()
        try:
            # update the proxy filter search text:
            filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
            self._file_filters.filter_reg_exp = filter_reg_exp
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)

    def _on_show_all_versions_toggled(self, checked):
        """
        Slot triggered when the show-all-versions checkbox is checked.

        :param checked: True if the checkbox has been checked, otherwise False
        """
        # reset the current selection and get the previously selected item:
        prev_selected_item = self._reset_selection()
        try:
            # update the filter model:
            self._file_filters.show_all_versions = checked
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)

    def _on_user_filter_btn_users_selected(self, users):
        """
        Slot triggered when the selected users in the users menu change.

        :param users:   The new list of selected users
        """
        # reset the current selection and get the previously selected item:
        prev_selected_item = self._reset_selection()
        try:
            # update the filter model:
            self._file_filters.users = users
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)

    def _on_item_double_clicked(self, idx):
        """
        Slot triggered when an item has been double-clicked in a view.  This will
        emit a signal appropriate to the item that was double-clicked.

        :param idx:    The model index of the item that was double-clicked
        """
        item_type = get_model_data(idx, FileModel.NODE_TYPE_ROLE)
        if item_type == FileModel.FOLDER_NODE_TYPE:
            # selection is a folder/child so move into it
            # TODO
            pass
        elif item_type == FileModel.FILE_NODE_TYPE:
            # this is a file so perform the default action for the file
            selected_file = get_model_data(idx, FileModel.FILE_ITEM_ROLE)
            env_details = get_model_data(idx, FileModel.WORK_AREA_ROLE)
            self.file_double_clicked.emit(selected_file, env_details)

    def _on_selection_changed(self, selected, deselected):
        """
        Slot triggered when the selection changes

        :param selected:    QItemSelection containing any newly selected indexes
        :param deselected:  QItemSelection containing any newly deselected indexes
        """
        # get the item that was selected:
        item = None
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            selected_index = map_to_source(selected_indexes[0])
            if selected_index and selected_index.isValid():
                item = selected_index.model().itemFromIndex(selected_index)

        # get the file and env details for this item:
        selected_file = None
        env_details = None
        if item:
            # extract the file item from the index:
            selected_file = get_model_data(item, FileModel.FILE_ITEM_ROLE)
            env_details = get_model_data(item, FileModel.WORK_AREA_ROLE)

        self._current_item_ref = weakref.ref(item) if item else None
        if self._current_item_ref:
            # clear the file-to-select as the current item now takes precedence
            self._file_to_select = None

        # emit file selected signal:
        self.file_selected.emit(selected_file, env_details, FileListForm.USER_SELECTED)

