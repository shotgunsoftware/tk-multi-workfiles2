# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'open_options_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from tank.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


class Ui_OpenOptionsForm(object):
    def setupUi(self, OpenOptionsForm):
        if not OpenOptionsForm.objectName():
            OpenOptionsForm.setObjectName(u"OpenOptionsForm")
        OpenOptionsForm.resize(514, 666)
        self.verticalLayout_3 = QVBoxLayout(OpenOptionsForm)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setSpacing(4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.name_label = QLabel(OpenOptionsForm)
        self.name_label.setObjectName(u"name_label")

        self.verticalLayout_6.addWidget(self.name_label)

        self.name_line = QFrame(OpenOptionsForm)
        self.name_line.setObjectName(u"name_line")
        self.name_line.setFrameShadow(QFrame.Plain)
        self.name_line.setFrameShape(QFrame.HLine)

        self.verticalLayout_6.addWidget(self.name_line)

        self.verticalLayout.addLayout(self.verticalLayout_6)

        self.title_label = QLabel(OpenOptionsForm)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.verticalLayout.addWidget(self.title_label)

        self.publish_frame = QFrame(OpenOptionsForm)
        self.publish_frame.setObjectName(u"publish_frame")
        self.publish_frame.setCursor(QCursor(Qt.PointingHandCursor))
        self.publish_frame.setMouseTracking(False)
        self.publish_frame.setFocusPolicy(Qt.TabFocus)
        self.publish_frame.setStyleSheet(u"#publish_frame {\n"
"border-radius: 4px;\n"
"border-style: none;\n"
"border-width: 1px;\n"
"border-color: rgb(0,0,0);\n"
"background-color: rgba(255,255,255,48);\n"
"}")
        self.publish_frame.setFrameShape(QFrame.StyledPanel)
        self.publish_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.publish_frame)
        self.verticalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.publish_title_label = QLabel(self.publish_frame)
        self.publish_title_label.setObjectName(u"publish_title_label")

        self.verticalLayout_4.addWidget(self.publish_title_label)

        self.publish_line = QFrame(self.publish_frame)
        self.publish_line.setObjectName(u"publish_line")
        self.publish_line.setFrameShadow(QFrame.Plain)
        self.publish_line.setFrameShape(QFrame.HLine)

        self.verticalLayout_4.addWidget(self.publish_line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.publish_details = QLabel(self.publish_frame)
        self.publish_details.setObjectName(u"publish_details")
        self.publish_details.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.publish_details.setWordWrap(True)
        self.publish_details.setMargin(0)
        self.publish_details.setIndent(0)

        self.horizontalLayout.addWidget(self.publish_details)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.publish_thumbnail = QLabel(self.publish_frame)
        self.publish_thumbnail.setObjectName(u"publish_thumbnail")
        self.publish_thumbnail.setMinimumSize(QSize(130, 90))
        self.publish_thumbnail.setMaximumSize(QSize(130, 90))
        self.publish_thumbnail.setStyleSheet(u"#publish_thumbnail {\n"
"background-color: rgba(0,0,0,32);\n"
"border-radius: 2px;\n"
"}")
        self.publish_thumbnail.setFrameShape(QFrame.NoFrame)
        self.publish_thumbnail.setLineWidth(0)
        self.publish_thumbnail.setAlignment(Qt.AlignCenter)
        self.publish_thumbnail.setMargin(0)
        self.publish_thumbnail.setIndent(0)

        self.verticalLayout_11.addWidget(self.publish_thumbnail)

        self.verticalSpacer_5 = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_5)

        self.horizontalLayout.addLayout(self.verticalLayout_11)

        self.horizontalLayout.setStretch(0, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.publish_note = QLabel(self.publish_frame)
        self.publish_note.setObjectName(u"publish_note")
        self.publish_note.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_4.addWidget(self.publish_note)

        self.verticalLayout.addWidget(self.publish_frame)

        self.or_label_a = QLabel(OpenOptionsForm)
        self.or_label_a.setObjectName(u"or_label_a")
        self.or_label_a.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.or_label_a)

        self.work_file_frame = QFrame(OpenOptionsForm)
        self.work_file_frame.setObjectName(u"work_file_frame")
        self.work_file_frame.setCursor(QCursor(Qt.PointingHandCursor))
        self.work_file_frame.setFocusPolicy(Qt.TabFocus)
        self.work_file_frame.setStyleSheet(u"#work_file_frame {\n"
"border-radius: 4px;\n"
"border-style: none;\n"
"border-width: 1px;\n"
"border-color: rgb(0,0,0);\n"
"background-color: rgba(255,255,255,48);\n"
"}")
        self.work_file_frame.setFrameShape(QFrame.StyledPanel)
        self.work_file_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.work_file_frame)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.work_file_title_label = QLabel(self.work_file_frame)
        self.work_file_title_label.setObjectName(u"work_file_title_label")

        self.verticalLayout_2.addWidget(self.work_file_title_label)

        self.work_file_line = QFrame(self.work_file_frame)
        self.work_file_line.setObjectName(u"work_file_line")
        self.work_file_line.setFrameShadow(QFrame.Plain)
        self.work_file_line.setFrameShape(QFrame.HLine)

        self.verticalLayout_2.addWidget(self.work_file_line)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.work_file_details = QLabel(self.work_file_frame)
        self.work_file_details.setObjectName(u"work_file_details")
        self.work_file_details.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.work_file_details.setMargin(0)
        self.work_file_details.setIndent(0)

        self.horizontalLayout_5.addWidget(self.work_file_details)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.work_file_thumbnail = QLabel(self.work_file_frame)
        self.work_file_thumbnail.setObjectName(u"work_file_thumbnail")
        self.work_file_thumbnail.setMinimumSize(QSize(130, 90))
        self.work_file_thumbnail.setMaximumSize(QSize(130, 90))
        self.work_file_thumbnail.setStyleSheet(u"#work_file_thumbnail {\n"
"background-color: rgba(0,0,0,32);\n"
"border-radius: 2px;\n"
"}")
        self.work_file_thumbnail.setFrameShape(QFrame.NoFrame)
        self.work_file_thumbnail.setLineWidth(0)
        self.work_file_thumbnail.setAlignment(Qt.AlignCenter)
        self.work_file_thumbnail.setMargin(0)
        self.work_file_thumbnail.setIndent(0)

        self.verticalLayout_12.addWidget(self.work_file_thumbnail)

        self.verticalSpacer_6 = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_6)

        self.horizontalLayout_5.addLayout(self.verticalLayout_12)

        self.horizontalLayout_5.setStretch(0, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.verticalLayout.addWidget(self.work_file_frame)

        self.or_label_b = QLabel(OpenOptionsForm)
        self.or_label_b.setObjectName(u"or_label_b")
        self.or_label_b.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.or_label_b)

        self.publish_ro_frame = QFrame(OpenOptionsForm)
        self.publish_ro_frame.setObjectName(u"publish_ro_frame")
        self.publish_ro_frame.setCursor(QCursor(Qt.PointingHandCursor))
        self.publish_ro_frame.setMouseTracking(False)
        self.publish_ro_frame.setFocusPolicy(Qt.TabFocus)
        self.publish_ro_frame.setStyleSheet(u"#publish_ro_frame {\n"
"border-radius: 4px;\n"
"border-style: none;\n"
"border-width: 1px;\n"
"border-color: rgb(0,0,0);\n"
"background-color: rgba(255,255,255,48);\n"
"}")
        self.publish_ro_frame.setFrameShape(QFrame.StyledPanel)
        self.publish_ro_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.publish_ro_frame)
        self.verticalLayout_8.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.publish_ro_title_label = QLabel(self.publish_ro_frame)
        self.publish_ro_title_label.setObjectName(u"publish_ro_title_label")

        self.verticalLayout_8.addWidget(self.publish_ro_title_label)

        self.publish_ro_line = QFrame(self.publish_ro_frame)
        self.publish_ro_line.setObjectName(u"publish_ro_line")
        self.publish_ro_line.setFrameShadow(QFrame.Plain)
        self.publish_ro_line.setFrameShape(QFrame.HLine)

        self.verticalLayout_8.addWidget(self.publish_ro_line)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_9 = QLabel(self.publish_ro_frame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.label_9.setWordWrap(True)
        self.label_9.setMargin(0)
        self.label_9.setIndent(0)

        self.horizontalLayout_3.addWidget(self.label_9)

        self.horizontalLayout_3.setStretch(0, 1)

        self.verticalLayout_8.addLayout(self.horizontalLayout_3)

        self.verticalLayout.addWidget(self.publish_ro_frame)

        self.verticalLayout_3.addLayout(self.verticalLayout)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.break_line = QFrame(OpenOptionsForm)
        self.break_line.setObjectName(u"break_line")
        self.break_line.setFrameShadow(QFrame.Plain)
        self.break_line.setFrameShape(QFrame.HLine)

        self.verticalLayout_5.addWidget(self.break_line)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(12, 12, 12, 12)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.cancel_btn = QPushButton(OpenOptionsForm)
        self.cancel_btn.setObjectName(u"cancel_btn")
        self.cancel_btn.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_4.addWidget(self.cancel_btn)

        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.verticalLayout_3.addLayout(self.verticalLayout_5)

        self.verticalLayout_3.setStretch(1, 1)
        QWidget.setTabOrder(self.publish_frame, self.work_file_frame)
        QWidget.setTabOrder(self.work_file_frame, self.cancel_btn)

        self.retranslateUi(OpenOptionsForm)

        self.cancel_btn.setDefault(False)

        QMetaObject.connectSlotsByName(OpenOptionsForm)
    # setupUi

    def retranslateUi(self, OpenOptionsForm):
        OpenOptionsForm.setWindowTitle(QCoreApplication.translate("OpenOptionsForm", u"Form", None))
        self.name_label.setText(QCoreApplication.translate("OpenOptionsForm", u"<big><b>name</b></big>", None))
        self.title_label.setText(QCoreApplication.translate("OpenOptionsForm", u"<big>There is a more recent, published version of this file available!</big>", None))
#if QT_CONFIG(tooltip)
        self.publish_frame.setToolTip(QCoreApplication.translate("OpenOptionsForm", u"Click to open the newer Published File", None))
#endif // QT_CONFIG(tooltip)
        self.publish_title_label.setText(QCoreApplication.translate("OpenOptionsForm", u"<big>Would you like to continue your work from the latest Publish?</big>", None))
        self.publish_details.setText(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p>Version v000<br/>Published on...<br/>Published by...<br/>Description:<br/><span style=\" font-style:italic;\">No description was entered for this publish</span></p></body></html>", None))
        self.publish_thumbnail.setText("")
        self.publish_note.setText(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p><small>(Note: The published file will be copied to your work area as version v000 and then opened)</small></p></body></html>", None))
        self.or_label_a.setText(QCoreApplication.translate("OpenOptionsForm", u"<big><b>OR</b></big>", None))
#if QT_CONFIG(tooltip)
        self.work_file_frame.setToolTip(QCoreApplication.translate("OpenOptionsForm", u"Click to open the older Work File", None))
#endif // QT_CONFIG(tooltip)
        self.work_file_title_label.setText(QCoreApplication.translate("OpenOptionsForm", u"<big>Would you prefer to open the older Work File instead?</big>", None))
        self.work_file_details.setText(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p>Version v000<br/>Updated on...<br/>Updated by...</p></body></html>", None))
        self.work_file_thumbnail.setText("")
        self.or_label_b.setText(QCoreApplication.translate("OpenOptionsForm", u"<big><b>OR</b></big>", None))
#if QT_CONFIG(tooltip)
        self.publish_ro_frame.setToolTip(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p>Click to open the older Published File read-only</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.publish_ro_title_label.setText(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p><span style=\" font-size:large;\">You can open the older Publish read-only?</span></p></body></html>", None))
        self.label_9.setText(QCoreApplication.translate("OpenOptionsForm", u"<html><head/><body><p><span style=\" font-style:italic;\">Note: If you open the Publish read-only, you will have to save the file into your Work Area before you can continue working with it.</span></p></body></html>", None))
        self.cancel_btn.setText(QCoreApplication.translate("OpenOptionsForm", u"Cancel", None))
    # retranslateUi
