
import sgtk
from sgtk.platform.qt import QtCore, QtGui

GroupedListBase = QtGui.QAbstractItemView#QtGui.QTreeView

class GroupedListView(GroupedListBase):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        GroupedListBase.__init__(self, parent)
        
        self._item_rects = {}
        self._max_width = 0
        self._max_height = 0
        self._rects_dirty = True
        
    def set_expanded(self, index, expand):
        """
        """
        if not index.isValid() or index.parent != self.rootIndex():
            # can only expand valid root indexes!
            return 
    
        # AD - TODO
    
    def is_expanded(self, index):
        """
        """
        if not index.isValid() or index.parent != self.rootIndex():
            return False
        
        # AD - TODO

        
    def setModel(self, model):
        """
        Set the model the view will use
        """
        self._rects_dirty = True
        GroupedListBase.setModel(self, model)
        
    def dataChanged(self, top_left, bottom_right):
        """
        Called when data in the model has been changed
        """
        self._rects_dirty = True
        GroupedListBase.dataChanged(self, top_left, bottom_right)
                
    def rowsInserted(self, parent_index, start, end):
        """
        Called when rows have been inserted into the model
        """
        self._rects_dirty = True
        GroupedListBase.rowsInserted(self, parent_index, start, end)
        
    def rowsAboutToBeRemoved(self, parent_index, start, end):
        """
        Called just before rows are going to be removed from the model
        """
        self._rects_dirty = True        
        GroupedListBase.rowsAboutToBeRemoved(self, parent_index, start, end)        
        
    def visualRect(self, index):
        """
        Return the rectangle occupied by the item for the given 
        index in the viewport
        """
        rect = QtCore.QRect()
        if index.isValid():
            rect = self._get_item_rect(index)
        return rect
    
    def isIndexHidden(self, index):
        """
        Return true if the specified index is hidden (e.g. a collapsed child
        in a tree view)
        """
        is_visible = (index.isValid() 
                      and (index.parent() == self.rootIndex() 
                           or index.parent().parent() == self.rootIndex())) 
        return not is_visible
    
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
        
        num_rows = len(self._item_rects)
        for row, (rect, children) in enumerate(self._item_rects):
            
            if point.y() < rect.y():
                # point definitely isn't on an item
                break
            
            # check to see if the point is in the scope of this branch:
            if row+1 < num_rows:
                next_row_rect, _ = self._item_rects[row+1]
                if point.y() >= next_row_rect.y():
                    continue

            # ok, we'll need an index for this row:
            index = self.model().index(row, 0)
            
            # if the point is in the item rect then we've got a hit!
            if rect.contains(point):
                return index 
            
            # no hit on parent so lets iterate through children:
            for child_row, (child_rect, _) in enumerate(children):
                if child_rect.contains(point):
                    # found a hit on a child item
                    return self.model().index(child_row, 0, index)
        
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

        num_rows = len(self._item_rects)
        for row, (rect, children) in enumerate(self._item_rects):
            
            if selection_rect.bottom() < rect.top():
                break
                        
            # check to see if the point is in the scope of this branch:
            if row+1 < num_rows:
                next_row_rect, _ = self._item_rects[row+1]
                if selection_rect.top() >= next_row_rect.top():
                    continue
                
            # we'll need an index for this row:
            index = self.model().index(row, 0)
                
            # ok, so check to see if any child items are inside the selection rectangle:
            top_left = None
            bottom_right = None
            for child_row, (child_rect, _) in enumerate(children):
                if child_rect.intersects(selection_rect):
                    child_index = self.model().index(child_row, 0, index)
                    if not top_left:
                        top_left = child_index
                    else:
                        bottom_right = child_index
                else:
                    if top_left:
                        selection.select(top_left, bottom_right or top_left)
                        top_left = None
                        bottom_right = None
                    
            if top_left:
                selection.select(top_left, bottom_right or top_left)

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
        self._calculate_item_rects()
        
        viewport_rect = self.viewport().rect()
        viewport_offset = (-self.horizontalOffset(), -self.verticalOffset())
        
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHints(QtGui.QPainter.Antialiasing |
                               QtGui.QPainter.TextAntialiasing)
        for row in range(self.model().rowCount()):
            
            index = self.model().index(row, 0, self.rootIndex())
            
            rect = self._get_item_rect(index)
            rect = rect.translated(viewport_offset[0], viewport_offset[1])
            
            if (rect.isValid 
                and rect.top() <= viewport_rect.bottom() 
                and rect.bottom() >= viewport_rect.top()):
                # need to paint the widget:
                option = self.viewOptions()
                option.rect = rect
                if self.selectionModel().isSelected(index):
                    option.state |= QtGui.QStyle.State_Selected
                if index == self.currentIndex():
                    option.state |= QtGui.QStyle.State_HasFocus
    
                self.itemDelegate().paint(painter, option, index)
                        
            # and draw children:
            for child_row in range(self.model().rowCount(index)):
            
                child_index = self.model().index(child_row, 0, index)
                child_rect = self._get_item_rect(child_index)
                child_rect = child_rect.translated(viewport_offset[0], viewport_offset[1])

                if (child_rect.isValid 
                    and child_rect.top() <= viewport_rect.bottom() 
                    and child_rect.bottom() >= viewport_rect.top()):
                    # draw the widget!
                    option = self.viewOptions()
                    option.rect = child_rect
                    if self.selectionModel().isSelected(child_index):
                        option.state |= QtGui.QStyle.State_Selected
                    if child_index == self.currentIndex():
                        option.state |= QtGui.QStyle.State_HasFocus                
                
                    self.itemDelegate().paint(painter, option, child_index)

    def updateGeometries(self):
        """
        """
        self.horizontalScrollBar().setSingleStep(1)
        self.horizontalScrollBar().setPageStep(self.viewport().width())
        self.horizontalScrollBar().setRange(0, max(0, self._max_width - self.viewport().width()))
        
        self.verticalScrollBar().setSingleStep(1)#00)# TODO - make this more intelligent!
        self.verticalScrollBar().setPageStep(self.viewport().height())
        self.verticalScrollBar().setRange(0, max(0, self._max_height - self.viewport().height()))
    
    def resizeEvent(self, event):
        """
        """
        # make sure item rects are up to date:
        self._rects_dirty = True
        self._calculate_item_rects()
        self.updateGeometries()

    def mousePressEvent(self, event):
        """
        """
        GroupedListBase.mousePressEvent(self, event)

    def _get_item_rect(self, index):
        """
        """
        rows = []
        while index.isValid() and index != self.rootIndex():
            rows.append(index.row())
            index = index.parent()
            
        rect = QtCore.QRect()
        rects = self._item_rects
        for row in reversed(rows):
            if row >= len(rects):
                rect = QtCore.QRect()
                break
            
            rect, rects = rects[row]
        return rect


    def _calculate_item_rects(self):
        """
        
        [(QRect(), []), (QRect(), [])]
        
        row: rect, children
        
        """
        if not self._rects_dirty:
            return
        
        viewport_width = self.viewport().width()
        
        rects = []
        max_width = viewport_width
        
        x_pos = 0
        y_pos = 0
        item_spacing = QtCore.QSize(2, 2)
        
        base_view_options = self.viewOptions()
        
        # iterate over root items:
        for row in range(self.model().rowCount()):

            # reset x_pos for root item:
            left = 0 # might extend this later!
            x_pos = left

            index = self.model().index(row, 0)
            
            # do we need to modify the view options?
            view_options = base_view_options
            
            # get the item size and calculate the rectangle the widget will need:
            item_size = self.itemDelegate().sizeHint(view_options, index)
            item_rect = QtCore.QRect(x_pos, y_pos, item_size.width(), item_size.height())
                        
            # update y_pos:
            y_pos += item_rect.height() + item_spacing.height()

            # now determine layout for children:
            child_rects = []
            row_height = 0
            for child_row in range(self.model().rowCount(index)):
            
                child_index = self.model().index(child_row, 0, index)

                # do we need to modify the view options?
                view_options = base_view_options
                
                # get the item size:
                child_item_size = self.itemDelegate().sizeHint(view_options, child_index)
                
                # see if it fits in the current row:
                if x_pos == left or (x_pos + (child_item_size.width() * 0.5)) < viewport_width:
                    # item will fit in the current row!
                    pass
                else:
                    # start a new row for this item:
                    y_pos = y_pos + row_height + item_spacing.height()
                    row_height = 0
                    x_pos = left

                # store the item rect:
                child_item_rect = QtCore.QRect(x_pos, y_pos, 
                                               child_item_size.width(), child_item_size.height())
                child_rects.append((child_item_rect, []))

                # keep track of the tallest row item:                
                row_height = max(row_height, child_item_rect.height())
                x_pos += item_spacing.width() + child_item_rect.width()
                max_width = max(child_item_rect.right(), max_width)

            # if needed, update y_pos:
            if row_height > 0:
                y_pos = y_pos + row_height + item_spacing.height()
                
            rects.append((item_rect, child_rects))
            
        # update all root level items to be the full width of the viewport:
        for rect, _ in rects:
            rect.setRight(max_width)
                
        self._item_rects = rects
        self._max_width = max_width
        self._max_height = y_pos
        
        self._rects_dirty = False
        self.viewport().update()

            
            
            
            
        
        
        
        
        

    
    