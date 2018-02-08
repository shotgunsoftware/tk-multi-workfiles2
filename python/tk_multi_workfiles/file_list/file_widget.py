# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..ui.file_widget import Ui_FileWidget

class FileWidget(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileWidget()
        self._ui.setupUi(self)
        
        # create the status icons and add them to a layout over the main thumbnail:
        self._publish_icon = QtGui.QLabel(self)
        self._publish_icon.setMinimumSize(16, 16)
        self._publish_icon.setAlignment(QtCore.Qt.AlignCenter)
        self._publish_icon.setPixmap(QtGui.QPixmap(":/tk-multi-workfiles2/publish_icon.png"))
        self._publish_icon.hide()

        # not sure I like this - think I preferred it when it was over on the right of the tile!
        self._lock_icon = QtGui.QLabel(self)
        self._lock_icon.setMinimumSize(16, 16)
        self._lock_icon.setAlignment(QtCore.Qt.AlignCenter)
        self._lock_icon.setPixmap(QtGui.QPixmap(":/tk-multi-workfiles2/padlock.png"))
        self._lock_icon.hide()

        rhs_layout = QtGui.QVBoxLayout()
        rhs_layout.setContentsMargins(0, 0, 0, 0)
        rhs_layout.setSpacing(0)
        rhs_layout.addWidget(self._lock_icon)
        rhs_layout.addStretch(1)
        rhs_layout.addWidget(self._publish_icon)

        thumb_layout = QtGui.QHBoxLayout(self._ui.thumbnail)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        thumb_layout.setSpacing(0)
        thumb_layout.addStretch()
        thumb_layout.addLayout(rhs_layout)

        self._ui.thumbnail.setLayout(thumb_layout)
        
        self._is_selected = False
        self._update_ui()

    #@property
    def _get_title(self):
        return self._ui.label.text()
    #@title.setter
    def _set_title(self, value):
        self._ui.label.setText(value)
    title=property(_get_title, _set_title)

    #@property
    def _get_selected(self):
        return self._is_selected
    #@selected.setter
    def _set_selected(self, value):
        self._is_selected = value
        self._update_ui()
    selected=property(_get_selected, _set_selected)

    def _get_subtitle(self):
        return self._ui.subtitle.text()

    def _set_subtitle(self, value):
        self._ui.subtitle.setText(value)
    subtitle = property(_get_subtitle, _set_subtitle)

    def set_show_subtitle(self, show_subtitle):
        """
        Set if the widget's subtitle should be displayed.

        :param show_subtitle: True if the subtitle should be displayed, otherwise False
        """
        self._ui.subtitle.setVisible(show_subtitle)

    def set_is_publish(self, is_publish):
        """
        """
        self._publish_icon.setVisible(is_publish)

    def set_is_editable(self, editable):
        """
        Set if the file this item represents is editable - if not editable 
        then an additional padlock icon is shown on the thumbnail for this item

        :param editable:    True if the file is editable, otherwise False
        """
        self._lock_icon.setVisible(not editable)

    def set_thumbnail(self, thumb):
        """
        """
        if not thumb or not isinstance(thumb, QtGui.QPixmap):
            thumb = QtGui.QPixmap(":/tk-multi-workfiles2/thumb_empty.png")
        self._ui.thumbnail.setPixmap(thumb)

    def _update_ui(self):
        """
        """
        self._ui.background.setProperty("selected", self._is_selected)
        self._ui.background.style().unpolish(self._ui.background)
        self._ui.background.ensurePolished()
