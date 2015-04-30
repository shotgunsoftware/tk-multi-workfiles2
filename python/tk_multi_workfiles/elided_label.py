
import time

import sgtk
from sgtk.platform.qt import QtCore, QtGui

class ElidedLabel(QtGui.QLabel):
    """
    """
    def __init__(self, parent=None):
        """
        """
        QtGui.QLabel.__init__(self, parent)

        self._elide_mode = QtCore.Qt.ElideRight
        self._actual_text = ""

    #@property
    def _get_elide_mode(self):
        return self._elide_mode
    def _set_elide_mode(self, value):
        if (value != QtCore.Qt.ElideLeft
            and value != QtCore.Qt.ElideRight):
            raise ValueError("elide_mode must be set to either QtCore.Qt.ElideLeft or QtCore.Qt.ElideRight")
        self._elide_mode = value
        self._update_elided_text()
    elide_mode = property(_get_elide_mode, _set_elide_mode)

    def text(self):
        """
        Overriden base method to return the original unmodified text
        """
        return self._actual_text
    
    def setText(self, text):
        """
        Overriden base method to set the text on the label
        """
        self._actual_text = text
        self._update_elided_text()

    def resizeEvent(self, event):
        """
        """
        self._update_elided_text()

    def _update_elided_text(self):
        """
        """
        text = self._elide_text(self._actual_text)
        QtGui.QLabel.setText(self, text)
        
    def _elide_text(self, text):
        """
        """
        # target width is the label width:
        target_width = self.width()

        # Use a QTextDocument to measure html/richtext width 
        doc = QtGui.QTextDocument()
        doc.setHtml(text)
        doc.setDefaultFont(self.font())

        # if line width is already less than the target width then great!
        line_width = doc.idealWidth()
        if line_width <= target_width:
            return text

        # depending on the elide mode, insert ellipses in the correct place
        cursor = QtGui.QTextCursor(doc)
        ellipses = ""
        if self._elide_mode != QtCore.Qt.ElideNone:
            # add the ellipses in the correct place:
            if self._elide_mode == QtCore.Qt.ElideLeft:
                ellipses = "... "
                cursor.setPosition(0)
            elif self._elide_mode == QtCore.Qt.ElideRight:
                ellipses = " ..."
                char_count = doc.characterCount()
                cursor.setPosition(char_count-1)
            cursor.insertText(ellipses)
        ellipses_len = len(ellipses)

        # remove characters until it the text fits within the target width:
        while line_width > target_width:
            # if string is less than the ellipses length then just return
            # an empty string
            char_count = doc.characterCount()
            if char_count < ellipses_len:
                return ""

            # calculate the number of characters to remove - should always remove at least 1
            # to be sure the text gets shorter!
            line_width = doc.idealWidth()
            p = target_width/line_width
            # play it safe and remove a couple less than the calculated amount
            chars_to_delete = max(1, char_count - int(float(char_count) * p)-2)

            # remove the characters:
            if self._elide_mode == QtCore.Qt.ElideLeft:
                cursor.setPosition(ellipses_len)
                cursor.setPosition(chars_to_delete + ellipses_len, QtGui.QTextCursor.KeepAnchor)
            else:
                # default is to elide right
                cursor.setPosition(char_count - chars_to_delete - ellipses_len - 1)
                cursor.setPosition(char_count - ellipses_len - 1, QtGui.QTextCursor.KeepAnchor)
            cursor.removeSelectedText()

            # update line width:
            line_width = doc.idealWidth()

        return doc.toHtml()





