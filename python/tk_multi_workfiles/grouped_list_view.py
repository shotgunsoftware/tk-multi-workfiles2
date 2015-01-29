
import time
import math

import sgtk
from sgtk.platform.qt import QtCore, QtGui

GroupedListBase = QtGui.QAbstractItemView#QtGui.QTreeView

class GroupWidgetBase(QtGui.QWidget):
    """
    """
    toggle_expanded = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        """
        """
        QtGui.QWidget.__init__(self, parent)

        self._cb = QtGui.QCheckBox(self)
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self._cb)
        self.setLayout(layout)
        
        self._cb.stateChanged.connect(self._on_expand_checkbox_state_changed)
        
    def set_item(self, model_idx):
        """
        """
        label = model_idx.data()
        self._cb.setText(label)
        
        rect = self.geometry()
        if model_idx.row() == 1:
            rect.setHeight(80)
        else:
            rect.setHeight(30)
        self.setGeometry(rect)
            
        
    def set_expanded(self, expand=True):
        """
        """
        self._cb.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)
        
    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        self.toggle_expanded.emit(state != QtCore.Qt.Unchecked)
        
from .ui.file_group_widget import Ui_FileGroupWidget

from .file_model import FileModel

class FileGroupWidget(GroupWidgetBase):
    """
    """
    _SPINNER_FPS = 20
    _SPINNER_LINE_WIDTH = 2
    _SPINNER_BORDER = 4
    _SPINNER_ARC_LENGTH = 320 * 16
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
        
        # and update the content and visibility of the message
        msg = model_idx.data(FileModel.SEARCH_MSG_ROLE)
        if msg:
            self._ui.msg_label.setText(msg)
            self._ui.msg_label.show()
        else:
            self._ui.msg_label.hide()
        

    def set_expanded(self, expand=True):
        """
        """
        self._ui.expand_check_box.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)

    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        self.toggle_expanded.emit(state != QtCore.Qt.Unchecked)


class GroupedListView(GroupedListBase):
    """
    """
    class ItemInfo(object):
        def __init__(self):
            self.rect = QtCore.QRect()              # relative item rect for group header
            self.is_group = True                    # True if item is a group, otherwise False
            self.dirty = True                       # True if data in group or children has changed
            self.collapsed = True                   # True if the group is currently collapsed
            self.child_rects = []                   # List of sizes for all child items relative to the group
            self.child_area_rect = QtCore.QRect()   # total size of child area
            
        def __repr__(self):
            return "Dirty: %s, Collapsed: %s" % (self.dirty, self.collapsed)    
    
    def __init__(self, parent=None):
        """
        Construction
        """
        GroupedListBase.__init__(self, parent)
        
        self._item_spacing = QtCore.QSize(2, 2)
        
        self._item_info = []
        self._update_all_item_info = True
        self._update_some_item_info = False
        self._max_width = 0
        self._non_group_area_rect = QtCore.QRect()
        
        self.setEditTriggers(self.CurrentChanged)

        self._calc_group_widget = None # should this be some kind of delegate?
        self._group_widgets = []
        self._group_widget_rows = {}

        self._prev_viewport_sz = QtCore.QSize()

        
    def create_group_widget(self, parent):
        """
        """
        return GroupWidgetBase(parent)
        
    def edit(self, idx, trigger, event):
        """
        """
        if idx.parent() == self.rootIndex():
            # we don't want to allow the regular editing of groups
            # needs to be driven by role though!
            return False
        return GroupedListBase.edit(self, idx, trigger, event)
        
    def set_expanded(self, index, expand):
        """
        """
        if not index.isValid() or index.parent != self.rootIndex():
            # can only expand valid root indexes!
            return 
    
        row = index.row()
        if row < len(self._item_info):
            self._item_info[row].collapsed = not expand
            self.viewport().update()
    
    def is_expanded(self, index):
        """
        """
        if not index.isValid() or index.parent != self.rootIndex():
            return False

        row = index.row()
        if row < len(self._item_info):
            return not self._item_info[row].collapsed
        else:
            return False

        
    def setModel(self, model):
        """
        Set the model the view will use
        """
        self._update_all_item_info = True
        GroupedListBase.setModel(self, model)
        
    def dataChanged(self, top_left, bottom_right):
        """
        Called when data in the model has been changed
        """
        print "DATA CHANGED [%s] %s -> %s" % (top_left.parent().row(), top_left.row(), bottom_right.row())
        
        if top_left.parent() == self.rootIndex():
            # data has changed for top-level rows:
            for row in range(top_left.row(), bottom_right.row()+1):
                self._item_info[row].dirty = True
                self._update_some_item_info = True
        elif top_left.parent().parent() == self.rootIndex():
            # this assumes that all rows from top-left to bottom-right have 
            # the same parent!
            row = top_left.parent().row()
            self._item_info[row].dirty = True
            self._update_some_item_info = True
        else:
            self._update_all_item_info = True
                
        # make sure we schedule a viewport update so that everything gets updated correctly!
        self.viewport().update()
        GroupedListBase.dataChanged(self, top_left, bottom_right)
                
    def rowsInserted(self, parent_index, start, end):
        """
        Called when rows have been inserted into the model
        """
        print "ROWS INSERTED [%s] %s -> %s" % (parent_index.row(), start, end)
        
        if not self._update_all_item_info:
            if parent_index == self.rootIndex():
                # inserting root level rows:
                new_rows = [GroupedListView.ItemInfo() for x in range(end+1-start)]
                self._item_info = self._item_info[:start] + new_rows + self._item_info[start:]
                self._update_some_item_info = True
            elif parent_index.parent() == self.rootIndex():
                # inserting group level rows:
                parent_row = parent_index.row()
                if parent_row < len(self._item_info):
                    self._item_info[parent_row].dirty = True
                    self._update_some_item_info = True
                else:
                    self._update_all_item_info = True
            else:
                # something went wrong!
                self._update_all_item_info = True
                    
        # make sure we schedule a viewport update so that everything gets updated correctly!
        self.viewport().update()
        GroupedListBase.rowsInserted(self, parent_index, start, end)
        
    def rowsAboutToBeRemoved(self, parent_index, start, end):
        """
        Called just before rows are going to be removed from the model
        """
        print "ROWS REMOVED [%s] %s -> %s" % (parent_index.row(), start, end)
        
        if not self._update_all_item_info:
            if parent_index == self.rootIndex():
                # removing root level rows:
                self._item_info = self._item_info[:start] + self._item_info[end+1:]
                self._update_some_item_info = True
            elif parent_index.parent() == self.rootIndex():
                # inserting group level rows:
                parent_row = parent_index.row()
                if parent_row < len(self._item_info):
                    self._item_info[parent_row].dirty = True
                    self._update_some_item_info = True
                else:
                    self._update_all_item_info = True
            else:
                # something went wrong!
                self._update_all_item_info = True        
            
        # make sure we schedule a viewport update so that everything gets updated correctly!
        self.viewport().update()
        GroupedListBase.rowsAboutToBeRemoved(self, parent_index, start, end)        
        
    def visualRect(self, index):
        """
        Return the rectangle occupied by the item for the given 
        index in the viewport
        """
        rect = QtCore.QRect()
        if index.isValid():
            rect = self._get_item_rect(index)
            rect = rect.translated(-self.horizontalOffset(), -self.verticalOffset())
        return rect
    
    def isIndexHidden(self, index):
        """
        Return true if the specified index is hidden (e.g. a collapsed child
        in a tree view)
        """
        if not index.isValid():
            return False
        
        parent_index = index.parent() 
        if parent_index == self.rootIndex():
            # root items are never hidden:
            return False
        
        if parent_index.parent() != self.rootIndex():
            # grandchildren are always hidden:
            return True
        
        row = parent_index.row()
        if row < len(self._item_info):
            if self._item_info[row].collapsed:
                # parent is collapsed so item is hidden
                return True
            
        # default is to show the index:
        return False
    
    def scrollTo(self, index, scroll_hint):
        """
        Scroll to the specified index in the viewport
        """
        viewport_rect = self.viewport().rect()
        
        item_rect = self._get_item_rect(index)
        item_rect = item_rect.translated(-self.horizontalOffset(), -self.verticalOffset())

        dx = 0
        if item_rect.left() < viewport_rect.left():
            dx = item_rect.left() - viewport_rect.left()
        elif item_rect.right() > viewport_rect.right():
            dx = min(item_rect.right() - viewport_rect.right(),
                     item_rect.left() - viewport_rect.left())
        if dx != 0:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + dx)

        dy = 0
        if item_rect.top() < viewport_rect.top():
            dy = item_rect.top() - viewport_rect.top()
        elif item_rect.bottom() > viewport_rect.bottom():
            dy = min(item_rect.bottom() - viewport_rect.bottom(),
                     item_rect.top() - viewport_rect.top())
        if dy != 0:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + dy)
                         
        self.viewport().update()        
        
    def indexAt(self, point):
        """
        Return the index for the specified point in the viewport
        """
        # convert viewport relative point to global point:
        point = point + QtCore.QPoint(self.horizontalOffset(), self.verticalOffset())
        
        num_rows = len(self._item_info)
        if num_rows != self.model().rowCount():
            # just in case!
            return QtCore.QModelIndex()
        
        y_offset = 0
        for row, item_info in enumerate(self._item_info):
            
            # get point in local space:
            local_point = point + QtCore.QPoint(0, -y_offset)
            
            if local_point.y() < item_info.rect.y():
                # point definitely isn't on an item as we'd have found it by now!
                break

            # ok, we'll need an index for this row:
            index = self.model().index(row, 0)

            # check if the point is within this item:
            if item_info.rect.contains(local_point):
                return index 

            # update y-offset:
            y_offset += item_info.rect.height()
            
            if item_info.collapsed:
                # move on to next item:
                continue
            
            # now check children:
            local_point = point + QtCore.QPoint(0, -y_offset)
            for child_row, child_rect in enumerate(item_info.child_rects):
                if child_rect.contains(local_point):
                    # found a hit on a child item
                    return self.model().index(child_row, 0, index)

            # update y-offset                
            y_offset += item_info.child_area_rect.height()
        
        # no match so return model index
        return QtCore.QModelIndex()

    def moveCursor(self, cursor_action, keyboard_modifiers):
        """
        Return the index for the item that the specified cursor action will 
        move to
        """
        index = self.currentIndex()
        # ...
        return index
    
    def horizontalOffset(self):
        """
        Return the X offset of the viewport within the ideal sized widget
        """
        return self.horizontalScrollBar().value()
    
    def verticalOffset(self):
        """
        Return the Y offset of the viewport within the ideal sized widget
        """
        return self.verticalScrollBar().value()    

    def scrollContentsBy(self, dx, dy):
        """
        Not sure if this is needed!
        """
        self.scrollDirtyRegion(dx, dy)
        self.viewport().scroll(dx, dy)
        self.viewport().update()

    def setSelection(self, selection_rect, flags):
        """
        Set the selection given the selection rectangle and flags
        """
        # convert viewport relative rect to global rect:
        selection_rect = selection_rect.translated(self.horizontalOffset(), self.verticalOffset())
        
        # now find which item rectangles intersect this rectangle:
        selection = QtGui.QItemSelection()

        num_rows = len(self._item_info)
        if num_rows != self.model().rowCount():
            # just in case!
            return
        
        # first look through non-group items:
        y_offset = 0
        local_selection_rect = selection_rect.translated(0, -y_offset)
        if self._non_group_area_rect.intersects(local_selection_rect):
            for row, item_info in enumerate(self._item_info):
                if item_info.is_group:
                    continue
                if item_info.rect.intersects(local_selection_rect):
                    index = self.model().index(row, 0)
                    selection.select(index, index)

        y_offset += self._non_group_area_rect.height()
        
        # now look through groups:
        for row, item_info in enumerate(self._item_info):
            
            if not item_info.is_group:
                continue
            
            # we only allow selection of child items so we can skip testing the group/top level:
            y_offset += item_info.rect.height()
            
            if item_info.collapsed:
                # skip collapsed items:
                continue
            
            # check to see if the selection rect intersects the child area:
            local_selection_rect = selection_rect.translated(0, -y_offset)
            
            if local_selection_rect.intersects(item_info.child_area_rect):
                # we'll need an index for this row:
                index = self.model().index(row, 0)
                
                # need to iterate through and check all child items:
                top_left = bottom_right = None
                for child_row, child_rect in enumerate(item_info.child_rects):
                    
                    if child_rect.intersects(local_selection_rect):
                        child_index = self.model().index(child_row, 0, index)
                        top_left = top_left or child_index
                        bottom_right = child_index
                    else:
                        if top_left:
                            selection.select(top_left, bottom_right)
                            top_left = bottom_right = None
                    
                if top_left:
                    selection.select(top_left, bottom_right)
            elif local_selection_rect.bottom() > item_info.child_area_rect.top():
                # no need to look any further!
                pass
                    
            # update y-offset
            y_offset += item_info.child_area_rect.height()
        
        # update the selection model:
        self.selectionModel().select(selection, flags)
        

    def visualRegionForSelection(self, selection):
        """
        Return the region in the viewport encompasing all the selected items
        """
        
        viewport_offset = (-self.horizontalOffset(), -self.verticalOffset())        
        
        region = QtGui.QRegion()
        for index_range in selection:
            for row in range(index_range.top(), index_range.bottom()+1):
                index = self.model().index(row, 0, index_range.parent())
                rect = self._get_item_rect(index)
                rect = rect.translated(viewport_offset[0], viewport_offset[1])
                region += rect

        #print "REGION: %s" % region.boundingRect()

        return region        
    
    def paintEvent(self, event):
        """
        """
        # make sure item rects are up to date:
        self._update_item_info()
        
        if self.model().rowCount() != len(self._item_info):
            # this shouldn't ever happen but just incase it does then 
            # we shouldn't paint anything as it'll probably be wrong!
            return
        
        self._group_widget_rows = {}
        next_group_widget_idx = 0
                
        viewport_rect = self.viewport().rect()
        viewport_offset = (-self.horizontalOffset(), -self.verticalOffset())
        
        painter = QtGui.QPainter(self.viewport())
        try:
            painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
            
            # keep track of the y-offset as we go:
            y_offset = 0
            
            # first draw non-group items - these are always at the top:
            for row, item_info in enumerate(self._item_info):
                if item_info.is_group:
                    continue
                
                # get the rectangle and translate into the correct relative location:
                rect = item_info.rect.translated(viewport_offset[0], viewport_offset[1] + y_offset)
                if not rect.isValid or not rect.intersects(viewport_rect):
                    # no need to draw!
                    continue                

                # get valid model index:
                index = self.model().index(row, 0, self.rootIndex())
                
                # set up the rendering options:
                option = self.viewOptions()
                option.rect = rect
                if self.selectionModel().isSelected(index):
                    option.state |= QtGui.QStyle.State_Selected
                if index == self.currentIndex():
                    option.state |= QtGui.QStyle.State_HasFocus                
            
                # draw the widget using the item delegate
                self.itemDelegate().paint(painter, option, index)
                
            y_offset += self._non_group_area_rect.height()         
            
            # now draw all group items and any expanded children:
            for row, item_info in enumerate(self._item_info):
                
                if not item_info.is_group:
                    continue
                
                # get valid model index:
                index = self.model().index(row, 0, self.rootIndex())
                
                # get the rectangle and translate into the correct relative location:
                rect = item_info.rect.translated(viewport_offset[0], viewport_offset[1] + y_offset)
                
                # test to see if the rectangle exists within the viewport:
                if rect.isValid and rect.intersects(viewport_rect):
                    # the group widget is visible:
                    grp_widget = None
                    if next_group_widget_idx < len(self._group_widgets):
                        grp_widget = self._group_widgets[next_group_widget_idx]
                    else:
                        # need to create a new group widget and hook up the signals:
                        grp_widget = self.create_group_widget(self.viewport())
                        if grp_widget:
                            self._group_widgets.append(grp_widget)
                            grp_widget.toggle_expanded.connect(self._on_group_expanded_toggled)
                    next_group_widget_idx += 1
                    
                    if grp_widget:
                        # set up this widget for this index:
                        grp_widget.setGeometry(rect)
                        grp_widget.set_item(index)
                        grp_widget.set_expanded(not item_info.collapsed)
                        grp_widget.show()
                        self._group_widget_rows[grp_widget] = row

                # add the groupd rectangle height to the y-offset
                y_offset += rect.height()
                    
                if item_info.collapsed:
                    # don't need to draw children!
                    continue
                
                # draw children:
                num_child_rows = self.model().rowCount(index)
                if len(item_info.child_rects) == num_child_rows:
                    # draw all children
                    for child_row, child_rect in enumerate(item_info.child_rects):
                        # figure out index and update rect:
                        child_index = self.model().index(child_row, 0, index)
                        child_rect = child_rect.translated(viewport_offset[0], viewport_offset[1] + y_offset)
    
                        if not child_rect.isValid or not child_rect.intersects(viewport_rect):
                            # no need to draw!
                            continue
                         
                        # set up the rendering options:
                        option = self.viewOptions()
                        option.rect = child_rect
                        if self.selectionModel().isSelected(child_index):
                            option.state |= QtGui.QStyle.State_Selected
                        if child_index == self.currentIndex():
                            option.state |= QtGui.QStyle.State_HasFocus                
                    
                        # draw the widget using the item delegate
                        self.itemDelegate().paint(painter, option, child_index)
            
                # update the y-offset to include the child area:
                y_offset += item_info.child_area_rect.height()            
            
            # hide any group widgets that were not used:
            for w in self._group_widgets[next_group_widget_idx:]:
                w.hide()
        finally:
            painter.end()

    def _on_group_expanded_toggled(self, expanded):
        """
        """
        # get the row that is being expanded:
        group_widget = self.sender()
        row = self._group_widget_rows.get(group_widget)
        if row == None or row >= len(self._item_info):
            return

        # toggle collapsed state for item:        
        self._item_info[row].collapsed = not expanded
        
        # and update the viewport and scrollbars:
        self.updateGeometries()
        self.viewport().update()

    def updateGeometries(self):
        """
        """
        # calculate the maximum height of all visible items in the model:
        max_height = self._non_group_area_rect.height()
        for item_info in self._item_info:
            max_height += item_info.rect.height()
            if not item_info.collapsed:
                max_height += item_info.child_area_rect.height()
        
        self.horizontalScrollBar().setSingleStep(30)
        self.horizontalScrollBar().setPageStep(self.viewport().width())
        self.horizontalScrollBar().setRange(0, max(0, self._max_width - self.viewport().width()))
        
        self.verticalScrollBar().setSingleStep(30)#00)# TODO - make this more intelligent!
        self.verticalScrollBar().setPageStep(self.viewport().height())
        self.verticalScrollBar().setRange(0, max(0, max_height - self.viewport().height()))
    
    def resizeEvent(self, event):
        """
        """
        # at the moment, recalculating the dimensions is handled at the start of painting so
        # we don't need to do anything here.  If this causes problems later then we may have
        # to rethink things!
        pass

    def _get_item_rect(self, index):
        """
        """
        # first, get the row for each level of the hierarchy (bottom to top)
        rows = []
        while index.isValid() and index != self.rootIndex():
            rows.append(index.row())
            index = index.parent()
            
        # find the info for the root item:
        root_row = rows[-1]
        if root_row >= len(self._item_info):
            return QtCore.QRect()
        root_info = self._item_info[root_row]
        
        # and the Y offset for the start of the root item:
        y_offset = 0
        if root_info.is_group:
            y_offset += self._non_group_area_rect.height()
            for row_info in self._item_info[:root_row]:
                if not root_info.is_group:
                    continue
                y_offset += row_info.rect.height()
                if not row_info.collapsed:
                    y_offset += row_info.child_area_rect.height()

        # get the rect for the leaf item:
        rect = QtCore.QRect()
        if len(rows) == 1:
            rect = root_info.rect
        else:
            y_offset += root_info.rect.height()
            child_row = rows[-2]
            if child_row < len(root_info.child_rects):
                rect = self._item_info[root_row].child_rects[child_row]

        # and offset the rect by the Y offset:
        rect = rect.translated(0, y_offset)
        
        return rect
            
    def _update_item_info(self):
        """
        """
        # check to see if the viewport size has changed:
        viewport_sz = self.viewport().size()
        viewport_resized = False
        if not self.verticalScrollBar().isVisible():
            # to avoid unnecessary resizing, we always calculate the viewport width as if
            # the vertical scroll bar were visible:
            viewport_sz.setWidth(viewport_sz.width() - self.verticalScrollBar().width())
        if viewport_sz != self._prev_viewport_sz:
            # the viewport width has changed so we'll need to update all geometry :(
            viewport_resized = True
            # keep track of the new viewport size for the next time
            self._prev_viewport_sz = viewport_sz 
        
        if not self._update_some_item_info and not self._update_all_item_info and not viewport_resized:
            # nothing to do!
            return
        
        #print "%s, %s, %s, %s" % (self._update_all_item_info, self._update_some_item_info, viewport_resized, self._item_info)

        self._update_all_item_info = self._update_all_item_info or viewport_resized
        
        viewport_width = viewport_sz.width()
        max_width = viewport_width
        base_view_options = self.viewOptions()
        
        # iterate over root items:
        something_updated = False
        non_group_rows = []
        for row in range(self.model().rowCount()):

            item_info = self._item_info[row] if row < len(self._item_info) else GroupedListView.ItemInfo()
            if not self._update_all_item_info and not item_info.dirty:
                # no need to update item info!
                max_width = max(max_width, item_info.child_area_rect.width())
                if not item_info.is_group:
                    non_group_rows.append(row)
                continue
            
            # construxt the model index for this row:
            index = self.model().index(row, 0)
            
            # see if this item is tagged as a group:
            item_info.is_group = index.data(FileModel.GROUP_NODE_ROLE) or False
            
            if item_info.is_group:
                # update group widget size:
                if not self._calc_group_widget:
                    self._calc_group_widget = self.create_group_widget(self)
                    self._calc_group_widget.setVisible(False)            
                
                self._calc_group_widget.set_item(index)
                item_size = self._calc_group_widget.size()
                item_info.rect = QtCore.QRect(0, 0, item_size.width(), item_size.height())
        
                # update size info of children:
                (child_rects, max_width, bottom) = self._layout_rows(range(self.model().rowCount(index)), 
                                                             index, 
                                                             base_view_options, 
                                                             viewport_width, 
                                                             max_width)

                item_info.child_rects = child_rects
                item_info.child_area_rect = QtCore.QRect(0, 0, max_width, bottom)
            else:
                non_group_rows.append(row) 
            
            # reset dirty flag for item:
            item_info.dirty = False
            something_updated = True        
            
            if row < len(self._item_info):
                self._item_info[row] = item_info
            else:
                self._item_info.append(item_info)
            
        # now update non-group items:
        print "Non-group rows: %s" % non_group_rows
        
        (rects, max_width, bottom) = self._layout_rows(non_group_rows, 
                                               self.rootIndex(), 
                                               base_view_options, 
                                               viewport_width, 
                                               max_width)
        self._non_group_area_rect = QtCore.QRect(0, 0, max_width, bottom)
        
        for row, rect in zip(non_group_rows, rects):
            self._item_info[row].rect = rect
            
        # reset flags:
        self._update_all_item_info = False
        self._update_some_item_info = False
            
        if something_updated:
            # update all root level items to be the full width of the viewport:
            for item_info in self._item_info:
                if item_info.is_group:
                    item_info.rect.setRight(max_width)
            self._max_width = max_width

            # update scroll bars for the new dimensions:            
            self.updateGeometries()            
            
    def _layout_rows(self, row_indexes, parent_index, base_view_options, viewport_width, max_width):
        """
        """
        # update size info of children:
        row_height = 0
        left = 0 # might extend this later!
        x_pos = left
        y_pos = 0
        rects = []  
        for row in row_indexes:
        
            index = self.model().index(row, 0, parent_index)

            # do we need to modify the view options?
            view_options = base_view_options
            
            # get the item size:
            item_size = self.itemDelegate().sizeHint(view_options, index)
            
            # see if it fits in the current row:
            if x_pos == left or (x_pos + (item_size.width() * 0.5)) < viewport_width:
                # item will fit in the current row!
                pass
            else:
                # start a new row for this item:
                y_pos = y_pos + row_height + self._item_spacing.height()
                row_height = 0
                x_pos = left

            # store the item rect:
            item_rect = QtCore.QRect(x_pos, y_pos, 
                                     item_size.width(), item_size.height())
            rects.append(item_rect)

            # keep track of the tallest row item:                
            row_height = max(row_height, item_rect.height())
            x_pos += self._item_spacing.width() + item_rect.width()
            max_width = max(item_rect.right(), max_width)
            
        return (rects, max_width, y_pos + row_height)
        
            
class FileGroupedListView(GroupedListView):
    def create_group_widget(self, parent):
        """
        """
        return FileGroupWidget(parent)
        
        
        
        

    
    