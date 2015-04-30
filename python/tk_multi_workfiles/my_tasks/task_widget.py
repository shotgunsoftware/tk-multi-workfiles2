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

from ..ui.task_widget import Ui_TaskWidget

class TaskWidget(QtGui.QWidget):
    """
    """
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_TaskWidget()
        self._ui.setupUi(self)

        self._background_styles = {}
        self._background_styles["normal"] = {
            "background-color": "rgb(0, 0, 0, 0)",
            "border-bottom-style": "solid",
            "border-bottom-width": "1px",
            "border-bottom-color": "rgb(64,64,64)"
        }
        self._background_styles["selected"] = self._background_styles["normal"].copy() 
        self._background_styles["selected"]["background-color"] = "rgb(0, 174, 237)"

        self._desc_styles = {}
        self._desc_styles["normal"] = {}
        self._desc_styles["selected"] = self._desc_styles["normal"].copy()
        self._desc_styles["selected"]["color"] = "rgb(255, 255, 255)"

    def set_selected(self, selected=True):
        """
        """
        bg_style = self._build_style_string("background", self._background_styles["selected" if selected else "normal"])
        self._ui.background.setStyleSheet(bg_style)
        
        desc_style = self._build_style_string("entity_label", self._desc_styles["selected" if selected else "normal"])
        self._ui.entity_label.setStyleSheet(desc_style)
        desc_style = self._build_style_string("task_label", self._desc_styles["selected" if selected else "normal"])
        self._ui.task_label.setStyleSheet(desc_style)
        desc_style = self._build_style_string("other_label", self._desc_styles["selected" if selected else "normal"])
        self._ui.other_label.setStyleSheet(desc_style)
        
    def set_thumbnail(self, thumb):
        """
        """
        geom = self._ui.thumbnail.geometry()
        self._set_label_image(self._ui.thumbnail, thumb, geom.width(), geom.height())
            
    def set_entity(self, name, typ, icon):
        """
        """
        self._ui.entity_label.setText(name)
        if not icon:
            self._ui.entity_icon.hide()
        else:
            self._ui.entity_icon.show()
            self._set_label_image(self._ui.entity_icon, icon, 20, 20)
    
    def set_task(self, name, icon):
        """
        """
        self._ui.task_label.setText("<big>%s</big>" % name)
        if not icon:
            self._ui.task_icon.hide()
        else:
            self._ui.task_icon.show()
            self._set_label_image(self._ui.task_icon, icon, 20, 20)
    
    def set_other(self, text):
        """
        """
        self._ui.other_label.setVisible(bool(text))
        self._ui.other_label.setText(text)

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
            scaled_pm = pm.scaled(w, h, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            
        label.setPixmap(scaled_pm)
        
            
            

    def _icon_to_pixmap(self, icon, w, h):

        if not icon:
            return None

        if icon:
            max_sz = max([(sz.width(), sz.height()) for sz in icon.availableSizes()] or [(256, 256)])
            thumb = icon.pixmap(max_sz[0], max_sz[1])


    def _build_style_string(self, ui_name, style):
        """
        """
        return "#%s {%s}" % (ui_name, ";".join(["%s: %s" % (key, value) for key, value in style.iteritems()]))
    
    
    
    
    
    