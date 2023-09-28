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
from ..util import get_model_data, map_to_source, get_source_model
from ..framework_qtwidgets import ViewItemDelegate, SGQIcon

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

settings_fw = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


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
    file_selected = QtCore.Signal(object, object, int)  # file, env, selection mode

    # Signal emitted whenever a file is double-clicked
    file_double_clicked = QtCore.Signal(object, object)  # file, env

    # Signal emitted whenever a context menu is required for a file
    file_context_menu_requested = QtCore.Signal(
        object, object, QtCore.QPoint
    )  # file, env, pos

    # Settings keys
    VIEW_MODE_SETTING = "view_mode"
    ITEM_SIZE_SCALE_VALUE = "view_item_size_scale"
    # The settings key prefix to storing the value indicating if references are checked on
    # file open
    CHECK_REFS_USER_SETTING = "check_references_on_file_open"

    def __init__(
        self,
        parent,
        search_label,
        file_filters,
        show_work_files=True,
        show_publishes=False,
        show_item_context_menu=True,
    ):
        """
        Construction

        :param search_label:     The hint label to be displayed on the search control
        :show_work_files:        True if work files should be displayed in this control, otherwise False
        :show_publishes:         True if publishes should be displayed in this control, otherwise False
        :show_item_context_menu: True if items have a context menu to show, otherwise False
        :param parent:           The parent QWidget for this control
        """

        QtGui.QWidget.__init__(self, parent)

        self._app = sgtk.platform.current_bundle()

        # create a settings manager where we can pull and push prefs later
        # prefs in this manager are shared
        self._settings_manager = settings.UserSettings(self._app)

        # keep track of the file to select when/if it appears in the attached model
        self._file_to_select = None
        # and keep track of the currently selected item
        self._current_item_ref = None

        self._file_filters = file_filters
        if self._file_filters:
            self._file_filters.changed.connect(self._on_file_filters_changed)
            self._file_filters.available_users_changed.connect(
                self._on_file_filters_available_users_changed
            )

        self._show_work_files = show_work_files
        self._show_publishes = show_publishes
        self._show_item_context_menu = show_item_context_menu

        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)

        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        self._ui.search_ctrl.search_changed.connect(self._on_search_changed)

        self._ui.all_versions_cb.setChecked(file_filters.show_all_versions)
        self._ui.all_versions_cb.toggled.connect(self._on_show_all_versions_toggled)

        check_refs = self.retrieve_check_reference_setting(self._app)
        self._ui.check_refs_cb.setChecked(check_refs)
        self._ui.check_refs_cb.toggled.connect(
            lambda checked: self.store_check_reference_setting(self._app, checked)
        )

        self._ui.user_filter_btn.available_users = self._file_filters.available_users
        self._ui.user_filter_btn.selected_users = self._file_filters.users
        self._ui.user_filter_btn.users_selected.connect(
            self._on_user_filter_btn_users_selected
        )
        # user filter button is hidden until needed
        self.enable_user_filtering_widget(False)

        self._ui.file_list_view.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        if self._show_item_context_menu:
            self._ui.file_list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self._ui.file_list_view.customContextMenuRequested.connect(
                self._on_context_menu_requested
            )

        # we want to handle double-click on items but we only want double-clicks to work when using
        # the left mouse button.  To achieve this we connect to the doubleClicked slot but also install
        # an event filter that will swallow any non-left-mouse-button double-clicks.
        self._ui.file_list_view.doubleClicked.connect(self._on_item_double_clicked)
        self._ui.file_list_view.viewport().installEventFilter(self)

        # Note, we have to keep a handle to the item delegate to help GC
        file_item_delegate = self._setup_view_item_delegate(self._ui.file_list_view)

        # Set up the view modes
        self.view_modes = [
            {
                "button": self._ui.thumbnail_mode,
                "delegate": file_item_delegate,
                "width": None,  # No width hint, the item width is determined by the item's data
            },
            {
                "button": self._ui.list_mode,
                "delegate": file_item_delegate,
                "width": -1,  # Tell the delegate item widths should expand to the full viewport width
            },
        ]
        for i, view_mode in enumerate(self.view_modes):
            view_mode["button"].clicked.connect(
                lambda checked=False, mode=i: self._set_view_mode(mode)
            )

        # Set up icons for view mode buttons
        self._ui.thumbnail_mode.setIcon(SGQIcon.grid_view_mode())
        self._ui.list_mode.setIcon(SGQIcon.list_view_mode())

        # Set up the item size slider
        scale_val = self._settings_manager.retrieve(self.ITEM_SIZE_SCALE_VALUE, 25)
        self._ui.item_size_slider.setValue(scale_val)
        self._on_view_item_size_slider_change(scale_val)
        self._ui.item_size_slider.valueChanged.connect(
            self._on_view_item_size_slider_change
        )

        cur_view_mode = self._settings_manager.retrieve(self.VIEW_MODE_SETTING, 0)
        self._set_view_mode(cur_view_mode)

    def _setup_view_item_delegate(self, view):
        """Create and set up a :class:`ViewItemDelegate` object for the given view."""

        delegate = ViewItemDelegate(view)

        # Set the item data roles used by the delegate to render an item.
        delegate.header_role = FileModel.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = FileModel.VIEW_ITEM_SUBTITLE_ROLE
        delegate.text_role = FileModel.VIEW_ITEM_TEXT_ROLE
        delegate.icon_role = FileModel.VIEW_ITEM_ICON_ROLE
        delegate.expand_role = FileModel.VIEW_ITEM_EXPAND_ROLE
        delegate.width_role = FileModel.VIEW_ITEM_WIDTH_ROLE
        delegate.height_role = FileModel.VIEW_ITEM_HEIGHT_ROLE
        delegate.loading_role = FileModel.VIEW_ITEM_LOADING_ROLE
        delegate.separator_role = FileModel.VIEW_ITEM_SEPARATOR_ROLE

        # Set up delegate styling (e.g. margins, padding, etc.)
        delegate.text_rect_valign = ViewItemDelegate.CENTER
        delegate.text_padding = ViewItemDelegate.Padding(0, 0, 0, 8)
        delegate.item_padding = ViewItemDelegate.Padding(0, 0, 0, 0)
        delegate.thumbnail_padding = ViewItemDelegate.Padding(7, 0, 7, 7)
        delegate.thumbnail_uniform = True
        delegate.action_item_margin = 2

        # Do not highlight rows on loading
        delegate.loading_brush = QtCore.Qt.NoBrush

        # Set up actions
        # Add an expand action for group header items
        delegate.add_action(
            {
                "icon": SGQIcon.tree_arrow(),
                "show_always": True,
                "padding": 0,
                "padding-bottom": 4,
                "features": QtGui.QStyleOptionButton.Flat,
                "get_data": self._get_expand_action_data,
                "callback": lambda view, index, pos: view.toggle_expand(index),
            },
            ViewItemDelegate.LEFT,
        )
        # Add a menu button for actions
        if self._show_item_context_menu:
            delegate.add_action(
                {
                    "icon": SGQIcon.tree_arrow(),
                    "padding": 2,
                    "callback": self._actions_menu_requested,
                },
                ViewItemDelegate.TOP_RIGHT,
            )

        # Enable mouse tracking for the delegate to receive mouse events
        view.setMouseTracking(True)
        view.setItemDelegate(delegate)

        return delegate

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
            view_model = (
                self._ui.file_list_view.model() or self._ui.file_details_view.model()
            )
            if view_model:
                self._ui.file_list_view.setModel(None)
                self._ui.file_details_view.setModel(None)
                if isinstance(view_model, FileProxyModel):
                    view_model.setSourceModel(None)
                    view_model = None

            # detach and clean up the item delegate:
            self._ui.file_list_view.setItemDelegate(None)
            for view_mode in self.view_modes:
                delegate = view_mode.get("delegate")
                if delegate:
                    delegate.setParent(None)
                    delegate.deleteLater()
                    delegate = None

        finally:
            self.blockSignals(signals_blocked)

    @staticmethod
    def retrieve_check_reference_setting(app):
        """
        Retrieve the setting value for checking references.

        :param app: The Application used to store the setting value.
        :type app: Application
        :return: The setting value for checking references.
        :rtype: bool
        """

        # Check if there is a user setting stored for the 'check references' options
        manager = settings_fw.UserSettings(app)
        checked = manager.retrieve(FileListForm.CHECK_REFS_USER_SETTING, None)

        if checked is None:
            # No user setting defined, get the app setting value for the default value
            checked = app.get_setting(FileListForm.CHECK_REFS_USER_SETTING, False)

        return checked

    @staticmethod
    def store_check_reference_setting(app, value):
        """
        Store the setting value for checking references.
        :param app: The Application used to store the setting value.
        :type app: Application
        :param env: The environment used to store the setting value.
        :type env: WorkArea
        :param value: The check references setting value.
        :type value: bool
        """

        manager = settings_fw.UserSettings(app)
        manager.store(FileListForm.CHECK_REFS_USER_SETTING, value)

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
                selected_file = get_model_data(
                    selected_indexes[0], FileModel.FILE_ITEM_ROLE
                )
                env_details = get_model_data(
                    selected_indexes[0], FileModel.WORK_AREA_ROLE
                )

        return (selected_file, env_details)

    def enable_show_all_versions(self, enable):
        """ """
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
            self._ui.user_filter_btn.setToolTip(
                "Click to see the list of %ssandboxes available for this context."
                % sandbox_type
            )
        else:
            self._ui.user_filter_btn.setToolTip(
                "There are no %ssandboxes available for this context." % sandbox_type
            )

        self._ui.user_filter_btn.setEnabled(is_enabled)

    def show_check_references_on_open_widget(self, show):
        """
        Show the option to check references on file open.

        :param enable: True to turn on the functionality.
        :type enable: bool
        """

        self._ui.check_refs_cb.setVisible(show)

        if not show:
            # Set the user preference to not check for reference on file open, if the UI option
            # is not available. The scene operation checks for this user setting to determine
            # if it should check references on open.
            self.store_check_reference_setting(self._app, False)

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
            filter_model = FileProxyModel(
                self,
                filters=self._file_filters,
                show_work_files=self._show_work_files,
                show_publishes=self._show_publishes,
            )
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
            if (
                event.type() == QtCore.QEvent.MouseButtonDblClick
                and event.button() != QtCore.Qt.LeftButton
            ):
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
                if isinstance(
                    self._ui.file_list_view.model(), QtGui.QAbstractProxyModel
                ):
                    idx = self._ui.file_list_view.model().mapFromSource(idx)
                if idx.isValid():
                    # make sure the item is expanded and visible in the list:
                    self._ui.file_list_view.scrollTo(idx)

                    # select the item:
                    selection_flags = (
                        QtGui.QItemSelectionModel.Clear
                        | QtGui.QItemSelectionModel.SelectCurrent
                    )
                    self._ui.file_list_view.selectionModel().select(
                        idx, selection_flags
                    )
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
                    selected_file = get_model_data(
                        selected_item, FileModel.FILE_ITEM_ROLE
                    )
                    env_details = get_model_data(
                        selected_item, FileModel.WORK_AREA_ROLE
                    )

                # emit the signal
                self.file_selected.emit(
                    selected_file, env_details, FileListForm.SYSTEM_SELECTED
                )

    def _on_file_filters_changed(self):
        """
        Slot triggered whenever the file filters emits the changed signal.
        """
        # update UI based on the new filter settings:
        self._ui.all_versions_cb.setChecked(self._file_filters.show_all_versions)
        self._ui.search_ctrl.search_text = (
            self._file_filters.filter_reg_exp.pattern()
            if self._file_filters.filter_reg_exp
            else ""
        )

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
        Slot triggered when a context menu has been requested from one of the file views. This will
        call the method to show the context menu at the given position.

        :param pnt: The position for the context menu relative to the source widget
        """

        idx = self._ui.file_list_view.indexAt(pnt)
        self._show_context_menu(self.sender(), idx, pnt)

    def _show_context_menu(self, widget, index, pos):
        """
        Show a context menu for the index at the given position. This will collect information about
        the index and emit a file_context_menu_requested signal.

        :param widget: The source widge (e.g. the view the index belongs to)
        :param index: The index to display the menu for.
        :param pos: The position for the context menu relative to the source widget
        """

        if not index or not index.isValid():
            return

        # get the file from the index:
        file_item = get_model_data(index, FileModel.FILE_ITEM_ROLE)
        if not file_item:
            return

        # ...and the env details:
        env_details = get_model_data(index, FileModel.WORK_AREA_ROLE)

        # remap the point from the source widget:
        pnt = widget.mapTo(self, pos)

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
            filter_reg_exp = QtCore.QRegExp(
                search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString
            )
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

    def _set_view_mode(self, mode_index):
        """
        Set the view mode for the main view.

        :param mode_index: The mode to set the view to.
        :type mode_index: int

        :return: None
        """

        assert 0 <= mode_index < len(self.view_modes), "Undefined view mode"

        # Clear any selection on changing the view mode.
        if self._ui.file_list_view.selectionModel():
            self._ui.file_list_view.selectionModel().clear()

        for i, view_mode in enumerate(self.view_modes):
            is_cur_mode = i == mode_index
            view_mode["button"].setChecked(is_cur_mode)
            if is_cur_mode:
                delegate = view_mode["delegate"]
                delegate.item_width = view_mode.get("width")
                self._ui.file_list_view.setItemDelegate(delegate)

        self._ui.file_list_view._update_all_item_info = True
        self._ui.file_list_view.viewport().update()

        self._settings_manager.store(self.VIEW_MODE_SETTING, mode_index)

    def _on_view_item_size_slider_change(self, value):
        """
        Slot triggered on the view item size slider value changed.

        :param value: The value of the slider.
        :return: None
        """

        for view_mode in self.view_modes:
            if isinstance(view_mode.get("delegate"), ViewItemDelegate):
                view_mode["delegate"].item_height = value

        self._ui.file_list_view._update_all_item_info = True
        self._ui.file_list_view.viewport().update()

        self._settings_manager.store(self.ITEM_SIZE_SCALE_VALUE, value)

    def _get_expand_action_data(self, parent, index):
        """
        Return the action data for the group header expand action, and for the given index.

        This data will determine how the action is displayed for the index.

        :param parent: This is the parent of the :class:`ViewItemDelegate`, which is the file view.
        :type parent: :class:`GroupItemView`
        :param index: The index the action is for.
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :return: The data for the action and index.
        :rtype: dict, e.g.:
            {
                "visible": bool  # Flag indicating whether the action is displayed or not
                "state": :class:`sgtk.platform.qt.QtGui.QStyle.StateFlag`  # Flag indicating state of the icon
                                                                        # e.g. enabled/disabled, on/off, etc.
                "name": str # Override the default action name for this index
            }
        """

        # Show the expand action for group header indexes
        visible = not index.parent().isValid()

        # The expand action is turned on if the group has children (else cannot click to
        # expand since there is nothing to show in the group).
        if index.model().rowCount(index) > 0:
            state = QtGui.QStyle.State_Active | QtGui.QStyle.State_Enabled
        else:
            state = ~QtGui.QStyle.State_Active & ~QtGui.QStyle.State_Enabled

        # Toggle the expand icon based on if the group is expanded or not.
        if parent.is_expanded(index):
            state |= QtGui.QStyle.State_Off
        else:
            state |= QtGui.QStyle.State_On

        return {"visible": visible, "state": state}

    def _actions_menu_requested(self, view, index, pos):
        """
        Callback triggered when a view item's action menu is requested to be shown.
        This will clear and select the given index, and show the item's actions menu.

        :param view: The view the item belongs to.
        :type view: :class:`GroupItemView`
        :param index: The index of the item.
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The position that the menu should be displayed at.
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`

        :return: None
        """

        selection_model = view.selectionModel()
        if selection_model:
            view.selectionModel().select(
                index, QtGui.QItemSelectionModel.ClearAndSelect
            )

        self._show_context_menu(view, index, pos)
