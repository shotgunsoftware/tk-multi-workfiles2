import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.file_tile import Ui_FileTile

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

    @property
    def title(self):
        return self._ui.label.text()
    
    @title.setter
    def title(self, value):
        self._ui.label.setText(value)
        
    @property
    def selected(self):
        return self._is_selected
    
    @selected.setter
    def selected(self, value):
        self._is_selected = value
        self._update_ui()
        
    def set_thumbnail(self, thumb):
        """
        """
        if not thumb:
            thumb = QtGui.QPixmap(":/tk-multi-workfiles/thumb_empty.png")
        
        geom = self._ui.thumbnail.geometry()
        self._set_label_image(self._ui.thumbnail, thumb, geom.width(), geom.height())        
        
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
        
        
        