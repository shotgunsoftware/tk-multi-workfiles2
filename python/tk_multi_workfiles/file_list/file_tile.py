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

from ..ui.file_tile import Ui_FileTile

class FileTile(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileTile()
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

        rhs_layout = QtGui.QVBoxLayout(self)
        rhs_layout.setContentsMargins(0, 0, 0, 0)
        rhs_layout.setSpacing(0)
        rhs_layout.addWidget(self._lock_icon)
        rhs_layout.addStretch(1)
        rhs_layout.addWidget(self._publish_icon)

        thumb_layout = QtGui.QHBoxLayout(self)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        thumb_layout.setSpacing(0)
        thumb_layout.addStretch()
        thumb_layout.addLayout(rhs_layout)

        self._ui.thumbnail.setLayout(thumb_layout)
        
        self._is_selected = False        
        self._background_styles = {}
        self._background_styles["normal"] = {
            "background-color": "rgb(0, 0, 0, 0)",
            "border-style": "solid",
            "border-width": "2px",
            "border-color": "rgb(0, 0, 0, 0)",
            "border-radius": "2px"
        }
        self._background_styles["selected"] = self._background_styles["normal"].copy()
        self._background_styles["selected"]["background-color"] = "rgb(135, 166, 185, 50)"#"rgb(0, 174, 237, 50)"
        self._background_styles["selected"]["border-color"] = "rgb(135, 166, 185)"#"rgb(0, 174, 237)"

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

    def set_is_publish(self, is_publish):
        """
        """
        self._publish_icon.setVisible(is_publish)

    def set_is_editable(self, editable, not_editable_reason = None):
        """
        Set if the file this item represents is editable - if not editable 
        then an additional padlock icon is shown with it's tooltip indicating 
        the reason why.
        """
        self._lock_icon.setVisible(not editable)
        # (AD) - this doesn't actually work as there is no concrete widget to show the tooltip on!
        self._lock_icon.setToolTip(not_editable_reason or "")
        
    def set_thumbnail(self, thumb):
        """
        """
        if not thumb or not isinstance(thumb, QtGui.QPixmap):
            thumb = QtGui.QPixmap(":/tk-multi-workfiles2/thumb_empty.png")
            
        self._ui.thumbnail.setPixmap(thumb)
        
        #geom = self._ui.thumbnail.geometry()
        #self._set_label_image(self._ui.thumbnail, thumb, geom.width(), geom.height())        
        
    def _set_label_image(self, label, image, w, h):
        """
        """
        if not image:
            # make sure it's cleared
            label.setPixmap(None)
            return
            
        pm = image
        if isinstance(pm, QtGui.QIcon):
            # extract the largest pixmap from the icon:
            max_sz = max([(sz.width(), sz.height()) for sz in image.availableSizes()] or [(256, 256)])
            pm = image.pixmap(max_sz[0], max_sz[1])
            
        # and scale the pm if needed:
        scaled_pm = pm
        if pm.width() > w or pm.height() > h:
            scaled_pm = pm.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            
        label.setPixmap(scaled_pm)        
        
    def _update_ui(self):
        """
        """
        style = self._build_style_string("background", 
                                         self._background_styles["selected" if self._is_selected else "normal"])
        self._ui.background.setStyleSheet(style)
        
    def _build_style_string(self, ui_name, style):
        """
        """
        return "#%s {%s}" % (ui_name, ";".join(["%s: %s" % (key, value) for key, value in style.iteritems()]))
        
        
        