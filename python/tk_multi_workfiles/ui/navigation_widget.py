# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'navigation_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_NavigationWidget(object):
    def setupUi(self, NavigationWidget):
        NavigationWidget.setObjectName("NavigationWidget")
        NavigationWidget.resize(126, 42)
        self.horizontalLayout = QtGui.QHBoxLayout(NavigationWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.navigation_prev = QtGui.QToolButton(NavigationWidget)
        self.navigation_prev.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_prev.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_prev.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/tk-multi-workfiles/left_arrow.png);\n"
"}\n"
"\n"
"QToolButton:disabled{\n"
"   background-image: url(:/tk-multi-workfiles/left_arrow_disabled.png);\n"
"}\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/tk-multi-workfiles/left_arrow_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/tk-multi-workfiles/left_arrow_pressed.png);\n"
"}\n"
"")
        self.navigation_prev.setObjectName("navigation_prev")
        self.horizontalLayout_2.addWidget(self.navigation_prev)
        self.navigation_home = QtGui.QToolButton(NavigationWidget)
        self.navigation_home.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_home.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_home.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/tk-multi-workfiles/home.png);\n"
"}\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/tk-multi-workfiles/home_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/tk-multi-workfiles/home_pressed.png);\n"
"}\n"
"")
        self.navigation_home.setObjectName("navigation_home")
        self.horizontalLayout_2.addWidget(self.navigation_home)
        self.navigation_next = QtGui.QToolButton(NavigationWidget)
        self.navigation_next.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_next.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_next.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/tk-multi-workfiles/right_arrow.png);\n"
"}\n"
"\n"
"QToolButton:disabled{\n"
"   background-image: url(:/tk-multi-workfiles/right_arrow_disabled.png);\n"
"}\n"
"\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/tk-multi-workfiles/right_arrow_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/tk-multi-workfiles/right_arrow_pressed.png);\n"
"}\n"
"")
        self.navigation_next.setObjectName("navigation_next")
        self.horizontalLayout_2.addWidget(self.navigation_next)
        self.horizontalLayout.addLayout(self.horizontalLayout_2)
        spacerItem = QtGui.QSpacerItem(0, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(NavigationWidget)
        QtCore.QMetaObject.connectSlotsByName(NavigationWidget)

    def retranslateUi(self, NavigationWidget):
        NavigationWidget.setWindowTitle(QtGui.QApplication.translate("NavigationWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_prev.setToolTip(QtGui.QApplication.translate("NavigationWidget", "<i>Go back</i> in the folder history.", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_home.setToolTip(QtGui.QApplication.translate("NavigationWidget", "Clicking the <i>home button</i> will take you to the location that best matches your current work area.", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_next.setToolTip(QtGui.QApplication.translate("NavigationWidget", "<i>Go forward</i> in the folder history.", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
