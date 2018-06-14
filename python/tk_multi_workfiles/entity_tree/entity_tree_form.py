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
Implementation of the entity tree widget consisting of a tree view that displays the
contents of a Shotgun Data Model, a text search and a filter control.
"""
import weakref

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..ui.entity_tree_form import Ui_EntityTreeForm
from .entity_tree_proxy_model import EntityTreeProxyModel
from ..framework_qtwidgets import Breadcrumb, overlay_widget
from ..util import get_model_str, map_to_source, get_source_model, monitor_qobject_lifetime
from ..util import get_sg_entity_name_field
from ..entity_models import ShotgunDeferredEntityModel


class EntityTreeForm(QtGui.QWidget):
    """
    A tree view for a list of Entities, with a search field.
    """

    class _EntityBreadcrumb(Breadcrumb):
        """
        Breadcrumb for a single model item.
        """

        def __init__(self, label, entity):
            """
            Constructor.

            :param label: Text label for the breabcrumb.
            :param entity: Entity associated with this breadcrumb.
            """
            Breadcrumb.__init__(self, label)
            self.entity = entity

    # Signal emitted when an entity is selected in the tree.
    entity_selected = QtCore.Signal(object, object)# selection details, breadcrumbs

    # Signal emitted when the 'New Task' button is clicked.
    create_new_task = QtCore.Signal(object, object)# entity, step

    def __init__(self, entity_model, search_label, allow_task_creation, extra_fields, parent, step_entity_filter=None):
        """
        Instantiate a new `EntityTreeForm`.

        Step filtering can be enable with the `step_entity_filter` parameter. If
        it is `None`, step filtering is disabled, if it is `Task` all existing
        steps will be offered as filters, if another Entity type (e.g. 'Shot') is
        given, only Steps linked to this Entity type will be offered as filters.

        :param entity_model:        The Shotgun Model this widget should connect to
        :param search_label:        The hint label to be displayed on the search control
        :param allow_task_creation: Indicates if the form is allowed by the app settings to show the
                                    create Task button.
        :param extra_fields:        Extra fields to use when comparing model entries.
        :param parent:              The parent QWidget for this control
        :param step_entity_filter:  An Entity type as a string or None defining
                                    the primary Entity to use when offering Step
                                    filtering.
        """
        QtGui.QWidget.__init__(self, parent)

        # control if step->tasks in the entity hierarchy should be collapsed when building
        # the search details.
        self._collapse_steps_with_tasks = True

        self._step_entity_filter = step_entity_filter
        # keep track of the entity to select when the model is updated:
        self._entity_to_select = None
        # keep track of the currently selected item:
        self._current_item_ref = None

        # Loose reference to expanded/selected entities used when the model is
        # reset to re-expand the tree from the SG entities.
        self._expanded_item_values = []
        self._selected_item_value = []


        # load the setting that states whether the first level of the tree should be auto expanded
        app = sgtk.platform.current_bundle()
        self._auto_expand_tree = app.get_setting("auto_expand_tree")

        # set up the UI
        self._ui = Ui_EntityTreeForm()
        self._ui.setupUi(self)

        # An overlay widget we can hide and show when the model is being refreshed.
        # This is mainly used as a workaround for 3ds 2016 refresh problems: by
        # hiding the widget when the data is refreshed, the UI is properly refreshed.
        self._refresh_overlay_widget = overlay_widget.ShotgunOverlayWidget(self._ui.entity_tree)
        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        self._ui.search_ctrl.setToolTip("Press enter to complete the search")

        # Hide the my-tasks-only checkbox if we are showing tasks, or if the entity
        # model is making use of deferred queries. In the latter case, we don't
        # have the data queried up front that's needed to properly filter the
        # tree down to "my tasks", so the checkbox won't function properly.
        #
        # We're also hiding it if we're working with script-key auth and no
        # named user was determined in SG.
        represents_tasks = entity_model.represents_tasks
        if not represents_tasks or isinstance(entity_model, ShotgunDeferredEntityModel) or app.context.user is None:
            self._ui.my_tasks_cb.hide()

        # enable/hide the new task button if we have tasks and task creation is allowed:
        if represents_tasks and allow_task_creation:
            # enable and connect the new task button
            self._ui.new_task_btn.clicked.connect(self._on_new_task)
            self._ui.new_task_btn.setEnabled(False)
        else:
            self._ui.new_task_btn.hide()

        self._ui.entity_tree.expanded.connect(self._on_item_expanded)
        self._ui.entity_tree.collapsed.connect(self._on_item_collapsed)

        self._is_resetting_model = False

        if entity_model:
            # Every time the model is refreshed with data from Shotgun, we'll need to re-expand nodes
            # that were expanded and reapply the current selection.
            entity_model.data_refreshed.connect(self._on_data_refreshed)

            if True:
                # Create a filter proxy model between the source model and the task tree view:
                # For Tasks we allow matching by the Task name and the name of the
                # Entity it is linked to. For the other Entities, we match with
                # the model item name and the Shotgun Entity field name, although
                # in most (if not all) cases the item name will match without the
                # need to check the Entity field.
                filter_model = EntityTreeProxyModel(
                    self, [
                        get_sg_entity_name_field(entity_model.get_entity_type()),
                        {"entity": "name"}
                    ] + extra_fields
                )
                monitor_qobject_lifetime(filter_model, "%s entity filter model" % search_label)
                filter_model.setSourceModel(entity_model)
                self._ui.entity_tree.setModel(filter_model)

                # connect up the filter controls:
                self._ui.search_ctrl.search_changed.connect(self._on_search_changed)
                self._ui.my_tasks_cb.toggled.connect(self._on_my_tasks_only_toggled)
                filter_model.modelAboutToBeReset.connect(self._model_about_to_reset)
                filter_model.modelReset.connect(self._model_reset)
            else:
                entity_model.modelAboutToBeReset.connect(self._model_about_to_reset)
                entity_model.modelReset.connect(self._model_reset)
                self._ui.entity_tree.setModel(entity_model)

        self._expand_root_rows()

        # connect to the selection model for the tree view:
        selection_model = self._ui.entity_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    @property
    def step_entity_filter(self):
        """
        :returns: The primary Entity type to use for Step filtering or None.
        """
        if not self.entity_model.supports_step_filtering:
            return None
        return self._step_entity_filter

    def _model_about_to_reset(self):
        """
        Slot called when the underlying model is about to be reset.
        """
        # Show that something heavy is going on by showing the spinning overlay
        # widget.
        self._refresh_overlay_widget.start_spin()
        entity_model = get_source_model(self._ui.entity_tree.model())
        # _entity_to_select is used to define a pre-selection before the model is
        # fully build. Reset it if the model is reset, and capture a path to the
        # selected item which will allow us to retrieve it in the updated model.
        self._entity_to_select = None
        if self._current_item_ref:
            item = self._current_item_ref()
            if item:
                # We only set `_selected_item_value` if there is a valid selection
                # this allows us to preserve a selection across filtering changes
                # if the expected item is not available with the current filter.
                self._selected_item_value = entity_model.get_item_field_value_path(item)
        self._is_resetting_model = True

    def _model_reset(self):
        """
        Called when the model was reset.
        """
        # Please note that this is called on shutdown, and in that case the
        # model is None.
        self._is_resetting_model = False
        if isinstance(self._ui.entity_tree.model(), QtGui.QAbstractProxyModel):
            # Reset the search filter: brute force solution to not have to deal with
            # current selection.
            self._ui.search_ctrl._set_search_text("")
            self._ui.entity_tree.model().setFilterRegExp("")
            # Toggle off the show "My Tasks" checkbox, trying to get it to behave
            # seems complicated.
            self._ui.my_tasks_cb.setChecked(False)
            self._ui.entity_tree.model().only_show_my_tasks = False
            # Tell connected objects that the current selection is gone.
            self.entity_selected.emit(None, [])

    def shut_down(self):
        """
        Clean up as much as we can to help the gc once the widget is finished with.
        """
        signals_blocked = self.blockSignals(True)
        try:
            # clear any references:
            self._entity_to_select = None
            self._expanded_item_values = []

            # clear the selection:
            if self._ui.entity_tree.selectionModel():
                self._ui.entity_tree.selectionModel().clear()

            # detach the filter model from the view:
            view_model = self._ui.entity_tree.model()
            if view_model:
                self._ui.entity_tree.setModel(None)
                if isinstance(view_model, EntityTreeProxyModel):
                    view_model.setSourceModel(None)
        finally:
            self.blockSignals(signals_blocked)

    def ensure_data_for_context(self, context):
        """
        Ensure the data for the given context is loaded in the model this view
        is attached to.

        This is typically used to load data for the current Toolkit context and
        select a matching item in the tree.

        :param context: A Toolkit context.
        """
        self.entity_model.ensure_data_for_context(context)

    def select_entity(self, entity_type, entity_id):
        """
        Select the specified entity in the tree.

        If the tree is still being populated then the selection will happen when
        an item representing the entity appears in the model.

        Note that this doesn't emit an entity_selected signal.

        :param entity_type: The type of the entity to select
        :param entity_id:   The id of the entity to select
        """
        # track the selected entity - this allows the entity to be selected when
        # it appears in the model even if the model hasn't been fully populated yet:
        self._entity_to_select = {"type": entity_type, "id": entity_id}
        # reset the current selection without emitting a signal:
        prev_selected_item = self._reset_selection()
        self._current_item_ref = None

        self._update_ui()

        # try to update the selection to reflect the change:
        self._update_selection(prev_selected_item)

    def get_selection(self):
        """
        Get the currently selected item as well as the breadcrumb trail that represents
        the path for the selection.

        :returns:   A Tuple containing the details and breadcrumb trail of the current selection:
                        (selection_details, breadcrumb_trail)

                    - selection_details is a dictionary containing:
                      {"label":label, "entity":entity, "children":[children]}
                    - breadcrumb_trail is a list of Breadcrumb instances
        """
        selection_details = {}
        breadcrumb_trail = []

        # get the currently selected index:
        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) == 1:
            selection_details = self._get_entity_details(selected_indexes[0])
            breadcrumb_trail = self._build_breadcrumb_trail(selected_indexes[0])

        return (selection_details, breadcrumb_trail)

    def navigate_to(self, breadcrumb_trail):
        """
        Update the selection to match the specified breadcrumb trail

        :param breadcrumb_trail:    A list of Breadcrumb instances that represent
                                    an item in the tree.
        """
        tree_model = self._ui.entity_tree.model()
        entity_model = get_source_model(tree_model)
        if not entity_model:
            return

        # figure out the item in the tree to select from the breadcrumb trail:
        current_item = entity_model.invisibleRootItem()
        for crumb in breadcrumb_trail:
            # look for an item under the current item that this breadcrumb represents:
            found_item = None
            if isinstance(crumb, EntityTreeForm._EntityBreadcrumb):
                # look for a child item that represents the entity:
                for row in range(current_item.rowCount()):
                    child_item = current_item.child(row)
                    sg_entity = entity_model.get_entity(child_item)
                    if (sg_entity["type"] == crumb.entity["type"]
                        and sg_entity["id"] == crumb.entity["id"]):
                        found_item = child_item
                        break
            else:
                # look for a child item that has the same label:
                for row in range(current_item.rowCount()):
                    child_item = current_item.child(row)
                    if get_model_str(child_item) == crumb.label:
                        found_item = child_item
                        break

            if not found_item:
                # stop traversal!
                break

            if isinstance(tree_model, QtGui.QAbstractProxyModel):
                # check to see if the item is visible in the current filtered model:
                filtered_idx = tree_model.mapFromSource(found_item.index())
                if not filtered_idx.isValid():
                    # stop traversal as the item isn't in the filtered model!
                    break

            # iterate down to the next level:
            current_item = found_item

        # finally, select the item in the tree:
        idx_to_select = current_item.index()
        if isinstance(tree_model, QtGui.QAbstractProxyModel):
            idx_to_select = tree_model.mapFromSource(current_item.index())
        self._ui.entity_tree.selectionModel().setCurrentIndex(idx_to_select, QtGui.QItemSelectionModel.SelectCurrent)

    @property
    def entity_model(self):
        """
        :returns: The :class:`ShotgunEntityModel` this widget is attached to.
        """
        return get_source_model(self._ui.entity_tree.model())

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    def _get_selected_item(self):
        """
        Get the currently selected item.

        :returns:   The currently selected model item if any
        """
        item = None
        indexes = self._ui.entity_tree.selectionModel().selectedIndexes()

        if len(indexes) == 1:
            item = self._item_from_index(indexes[0])
        return item

    def _reset_selection(self):
        """
        Reset the current selection, returning the currently selected item if any.  This
        doesn't result in any signals being emitted by the current selection model.

        :returns:   The selected item before the selection was reset if any
        """
        prev_selected_item = self._get_selected_item()
        # reset the current selection without emitting any signals:
        self._ui.entity_tree.selectionModel().reset()
        self._update_ui()
        return prev_selected_item

    def _get_entity_details(self, idx):
        """
        Get entity details for the specified model index.  If steps are being collapsed into tasks
        then these details will reflect that and will not be a 1-1 representation of the tree itself.

        :param idx: The QModelIndex of the item to get the entity details for.
        :returns:   A dictionary containing entity information about the specified index containing the
                    following information:

                        {"label":label, "entity":entity, "children":[children]}

                    - label:      The label of the corresponding item
                    - entity:     The entity dictionary for the corresponding item
                    - children:   A list of immediate children for the corresponding item - each item in
                                  the list is a dictionary containing 'label' and 'entity'.
        """
        if not idx.isValid():
            return {}

        # first, ensure that all child data has been loaded
        idx.model().ensure_data_is_loaded(idx)

        item = self._item_from_index(idx)
        entity_model = get_source_model(idx.model())
        if not item or not entity_model:
            return {}

        # get details for this item:
        label = get_model_str(item)
        entity = entity_model.get_entity(item)

        # get details for children:
        children = []
        collapsed_children = []

        view_model = self._ui.entity_tree.model()
        for row in range(view_model.rowCount(idx)):
            child_idx = view_model.index(row, 0, idx)
            child_item = self._item_from_index(child_idx)
            if not child_item:
                continue

            child_label = get_model_str(child_item)
            child_entity = entity_model.get_entity(child_item)
            children.append({"label":child_label, "entity":child_entity})

            if self._collapse_steps_with_tasks and child_entity and child_entity["type"] == "Step":
                # see if grand-child is actually a task:
                for child_row in range(view_model.rowCount(child_idx)):
                    grandchild_idx = view_model.index(child_row, 0, child_idx)
                    grandchild_item = self._item_from_index(grandchild_idx)
                    if not grandchild_item:
                        continue

                    grandchild_label = get_model_str(grandchild_item)
                    grandchild_entity = entity_model.get_entity(grandchild_item)
                    if grandchild_entity and grandchild_entity["type"] == "Task":
                        # found a task under a step so we can safely collapse tasks to steps!
                        collapsed_child_label = "%s - %s" % (child_label, grandchild_label)
                        collapsed_children.append({"label":collapsed_child_label, "entity":grandchild_entity})

        if collapsed_children:
            # prefer collapsed children instead of children if we have them
            children = collapsed_children
        elif self._collapse_steps_with_tasks and entity and entity["type"] == "Step":
            # it's possible that entity is actually a Step and the Children are all tasks - if this is
            # the case then update the child entities to be 'collapsed' and clear the entity on the Step
            # item:
            for child in children:
                child_label = child["label"]
                child_entity = child["entity"]
                if child_entity and child_entity["type"] == "Task":
                    collapsed_child_label = "%s - %s" % (label, child_label)
                    collapsed_children.append({"label":collapsed_child_label, "entity":child_entity})

            if collapsed_children:
                entity = None
                children = collapsed_children

        return {"label":label, "entity":entity, "children":children}

    def _on_search_changed(self, search_text):
        """
        Slot triggered when the search text has been changed.

        :param search_text: The new search text
        """
        # reset the current selection without emitting any signals:
        prev_selected_item = self._reset_selection()
        try:
            # update the proxy filter search text:
            filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
            self._ui.entity_tree.model().setFilterRegExp(filter_reg_exp)
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)
        self._fix_expanded_rows()

    def _on_my_tasks_only_toggled(self, checked):
        """
        Slot triggered when the show-my-tasks checkbox is toggled

        :param checked: True if the checkbox has been checked, otherwise False
        """
        # reset the current selection without emitting any signals:
        prev_selected_item = self._reset_selection()
        try:
            self._ui.entity_tree.model().only_show_my_tasks = checked
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)
        self._fix_expanded_rows()

    def _update_selection(self, prev_selected_item, data_changed=False):
        """
        Update the selection to either the to-be-selected entity if set or the current item if known.  The
        current item is the item that was last selected but which may no longer be visible in the view due
        to filtering.  This allows it to be tracked so that the selection state is correctly restored when
        it becomes visible again.
        """
        entity_model = get_source_model(self._ui.entity_tree.model())
        if not entity_model:
            return

        # we want to make sure we don't emit any signals whilst we are
        # manipulating the selection:
        signals_blocked = self.blockSignals(True)
        try:
            # try to get the item to select:
            item = None
            if self._entity_to_select:
                item = entity_model.item_from_entity(
                    self._entity_to_select["type"],
                    self._entity_to_select["id"]
                )
            elif self._current_item_ref:
                # no item to select but we do know about a current item:
                item = self._current_item_ref()

            if item:
                idx = item.index()
                if isinstance(self._ui.entity_tree.model(), QtGui.QAbstractProxyModel):
                    # map the index to the proxy model:
                    idx = self._ui.entity_tree.model().mapFromSource(idx)

                if idx.isValid():
                    # make sure the item is expanded and visible in the tree:
                    self._ui.entity_tree.scrollTo(idx)

                    # select the item:
                    self._ui.entity_tree.selectionModel().setCurrentIndex(idx, QtGui.QItemSelectionModel.SelectCurrent)

        finally:
            self.blockSignals(signals_blocked)
            # Emitting the entity_selected signal has two effects:
            # - it tells other tabs that they should check their current selection.
            # - it tells the file finder for the current tab to refresh itself.
            # So we only emit the signal in two cases:
            # - The selection has changed.
            # - The selection didn't change, but the data did and there is something
            #   selected.
            selected_item = self._get_selected_item()
            if (data_changed and selected_item) or id(selected_item) != id(prev_selected_item):
                # Get the selected entity details:
                selection_details, breadcrumbs = self.get_selection()
                # Emit a selection changed signal:
                self.entity_selected.emit(selection_details, breadcrumbs)

    def _update_ui(self):
        """
        Update the UI to reflect the current selection, etc.
        """
        enable_new_tasks = False

        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) == 1:
            item = self._item_from_index(selected_indexes[0])
            entity_model = get_source_model(selected_indexes[0].model())
            if item and entity_model:
                entity = entity_model.get_entity(item)
                if entity and entity["type"] != "Step":
                    if entity["type"] == "Task":
                        if entity.get("entity"):
                            enable_new_tasks = True
                    else:
                        enable_new_tasks = True

        self._ui.new_task_btn.setEnabled(enable_new_tasks)

    def _on_selection_changed(self, selected, deselected):
        """
        Slot triggered when the selection changes due to user action

        :param selected:    QItemSelection containing any newly selected indexes
        :param deselected:  QItemSelection containing any newly deselected indexes
        """
        # As the model is being reset, the selection is getting updated constantly,
        # so ignore these selection changes.
        if self._is_resetting_model:
            return

        # our tree is single-selection so extract the newly selected item from the
        # list of indexes:
        selection_details = {}
        breadcrumbs = []
        item = None
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            selection_details = self._get_entity_details(selected_indexes[0])
            breadcrumbs = self._build_breadcrumb_trail(selected_indexes[0])
            item = self._item_from_index(selected_indexes[0])

        # update the UI
        self._update_ui()

        # keep track of the current item:
        self._current_item_ref = weakref.ref(item) if item else None

        if self._current_item_ref:
            # clear the entity-to-select as the current item now takes precedence
            self._entity_to_select = None

        # emit selection_changed signal:
        self.entity_selected.emit(selection_details, breadcrumbs)

    def _on_data_refreshed(self, modifications_made):
        """
        Slot triggered when the data in the model has been refreshed.

        :param bool modifications_made: Whether or not changes were made.
        """
        entity_model = get_source_model(self._ui.entity_tree.model())
        # If something was selected on model reset, restore the selection, if
        # possible.
        if self._selected_item_value:
            item = entity_model.item_from_field_value_path(self._selected_item_value)
            if item:
                self._current_item_ref = weakref.ref(item)
        if not modifications_made:
            return

        # expand any new root rows:
        self._expand_root_rows()
        self._fix_expanded_rows()
        # try to select the current entity from the new items in the model:
        prev_selected_item = self._reset_selection()
        self._update_selection(prev_selected_item, True)
        # Hide the overlay widget
        self._refresh_overlay_widget.hide()

    def _expand_root_rows(self):
        """
        Expand all root rows in the Tree if they have never been expanded
        """
        view_model = self._ui.entity_tree.model()
        if not view_model:
            return

        # check if we should automatically expand the root level of the tree
        if not self._auto_expand_tree:
            return

        # disable widget paint updates whilst we update the expanded state of the tree:
        self._ui.entity_tree.setUpdatesEnabled(False)
        # and block signals so that the expanded signal doesn't fire during item expansion!
        signals_blocked = self._ui.entity_tree.blockSignals(True)
        try:
            for row in range(view_model.rowCount()):
                idx = view_model.index(row, 0)
                item = self._item_from_index(idx)
                if not item:
                    continue

                path = item.model().get_item_field_value_path(item)
                if path in self._expanded_item_values:
                    # we already processed this item
                    continue

                # expand item:
                self._ui.entity_tree.expand(idx)
                self._expanded_item_values.append(
                    path
                )
        finally:
            self._ui.entity_tree.blockSignals(signals_blocked)
            # re-enable updates to allow painting to continue
            self._ui.entity_tree.setUpdatesEnabled(True)

    def _fix_expanded_rows(self):
        """
        Update all items that have previously been expanded to be expanded.

        Filtering resets the expanded state of items so this is used to re-expand
        them correctly when previously expanded items re-appear in the model.
        """
        view_model = self._ui.entity_tree.model()
        if not view_model:
            return

        # Disable widget paint updates whilst we update the expanded state of the tree:
        self._ui.entity_tree.setUpdatesEnabled(False)
        # Block signals so that the expanded signal doesn't fire during item expansion!
        signals_blocked = self._ui.entity_tree.blockSignals(True)
        try:
            for item_value in self._expanded_item_values:
                item = self.entity_model.item_from_field_value_path(item_value)
                if item:
                    idx = item.index()
                    if isinstance(view_model, QtGui.QAbstractProxyModel):
                        idx = self._ui.entity_tree.model().mapFromSource(idx)
                        if not idx.isValid():
                            continue
                    # If the item isn't expanded then expand it:
                    if not self._ui.entity_tree.isExpanded(idx):
                        self._ui.entity_tree.expand(idx)
        finally:
            # Re-enable what we disabled
            self._ui.entity_tree.blockSignals(signals_blocked)
            self._ui.entity_tree.setUpdatesEnabled(True)

    def _item_from_index(self, idx):
        """
        Find the corresponding model item from the specified index.  This handles
        the indirection introduced by the filter model.

        :param idx: The model index to find the item for
        :returns:   The item in the model represented by the index
        """
        src_idx = map_to_source(idx)
        return src_idx.model().itemFromIndex(src_idx)

    def _on_item_expanded(self, idx):
        """
        Slot triggered when an item in the tree is expanded - used to track expanded
        state for all items.

        :param idx: The index of the item in the tree being expanded
        """
        item = self._item_from_index(idx)
        if not item:
            return
        self._expanded_item_values.append(
            item.model().get_item_field_value_path(item)
        )

    def _on_item_collapsed(self, idx):
        """
        Slot triggered when an item in the tree is collapsed - used to track expanded
        state for all items.

        :param idx: The index of the item in the tree being collapsed
        """
        item = self._item_from_index(idx)
        if not item:
            return
        path = item.model().get_item_field_value_path(item)
        if path in self._expanded_item_values:
            self._expanded_item_values.remove(path)

    def _on_new_task(self):
        """
        Slot triggered when the new task button is clicked.  Extracts the necessary
        information from the widget and raises a uniform signal for containing code
        """
        # get the currently selected index:
        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return

        # extract the selected model index from the selection:
        src_index = map_to_source(selected_indexes[0])

        # determine the currently selected entity:
        entity_model = src_index.model()
        entity_item = entity_model.itemFromIndex(src_index)
        entity = entity_model.get_entity(entity_item)
        if not entity:
            return

        if entity["type"] == "Step":
            # can't create tasks on steps as we don't have an entity!
            return

        step = None
        if entity["type"] == "Task":
            step = entity.get("step")
            entity = entity.get("entity")
            if not entity:
                return

        # and emit the signal for this entity:
        self.create_new_task.emit(entity, step)

    def _build_breadcrumb_trail(self, idx):
        """
        Builds the breadcrumb trail for the selected model index.

        :param idx: Index of an item in the selection model.

        :returns: List of _EntityBreadcrumb for each item in the hierarchy.
        """
        if not idx.isValid():
            return []

        # walk up the tree starting with the specified index:
        breadcrumbs = []
        src_index = map_to_source(idx)
        entity_model = src_index.model()
        while src_index.isValid():
            entity = entity_model.get_entity(entity_model.itemFromIndex(src_index))
            if entity:
                name_token = get_sg_entity_name_field(entity["type"])
                # In some cases the name is not stored in under regular entity field
                # name, but under the "name" key, e.g. if the Entity was retrieved
                # from a TK context or using a nested SG query. So check if the
                # expected key is present, use "name" if not.
                if name_token not in entity:
                    name_token = "name"
                label = "<b>%s</b> %s" % (entity["type"], entity.get(name_token))
                breadcrumbs.append(EntityTreeForm._EntityBreadcrumb(label, entity))
            else:
                label = get_model_str(src_index)
                breadcrumbs.append(Breadcrumb(label))

            src_index = src_index.parent()

        # return reversed list:
        return breadcrumbs[::-1]
