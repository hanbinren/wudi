# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os

from QtExt import QtCore, QtWidgets, QtGui

import ftrack
from ftrack_connect.ui.widget.stacked_options import StackedOptionsWidget
from ftrack_connect import connector as ftrack_connector
from ftrack_connect_maya.connector.mayacon import Connector as maya_connector


class Ui_ExportOptions(object):
    def setupUi(self, ExportOptions):
        ExportOptions.setObjectName("ExportOptions")
        ExportOptions.resize(339, 266)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            ExportOptions.sizePolicy().hasHeightForWidth()
        )
        ExportOptions.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(ExportOptions)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.optionsPlaceHolderLayout = QtWidgets.QHBoxLayout()
        self.optionsPlaceHolderLayout.setObjectName("optionsPlaceHolderLayout")
        self.verticalLayout.addLayout(self.optionsPlaceHolderLayout)
        self.label_4 = QtWidgets.QLabel(ExportOptions)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.thumbnailLineEdit = QtWidgets.QLineEdit(ExportOptions)
        self.thumbnailLineEdit.setObjectName("thumbnailLineEdit")
        self.gridLayout_4.addWidget(self.thumbnailLineEdit, 2, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(ExportOptions)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_4.addWidget(self.pushButton, 2, 1, 1, 1)
        self.screenshotButton = QtWidgets.QPushButton(ExportOptions)
        self.screenshotButton.setObjectName("screenshotButton")
        self.gridLayout_4.addWidget(self.screenshotButton, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_4)
        self.label_5 = QtWidgets.QLabel(ExportOptions)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)
        self.commentTextEdit = QtWidgets.QPlainTextEdit(ExportOptions)
        self.commentTextEdit.setMaximumSize(QtCore.QSize(16777215, 80))
        self.commentTextEdit.setObjectName("commentTextEdit")
        self.verticalLayout.addWidget(self.commentTextEdit)
        self.publishButton = QtWidgets.QPushButton(ExportOptions)
        self.publishButton.setObjectName("publishButton")
        self.verticalLayout.addWidget(self.publishButton)
        self.progressBar = QtWidgets.QProgressBar(ExportOptions)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.publishMessageLabel = QtWidgets.QLabel(ExportOptions)
        self.publishMessageLabel.setText("")
        self.publishMessageLabel.setObjectName("publishMessageLabel")
        self.verticalLayout.addWidget(self.publishMessageLabel)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(ExportOptions)
        
        QtCore.QObject.connect(
            self.pushButton,
            QtCore.SIGNAL("clicked()"),
            ExportOptions.setThumbnailFilename
        )
        QtCore.QObject.connect(
            self.screenshotButton,
            QtCore.SIGNAL("clicked()"),
            ExportOptions.takeScreenshot
        )
        QtCore.QMetaObject.connectSlotsByName(ExportOptions)

    def retranslateUi(self, ExportOptions):
        ExportOptions.setWindowTitle(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Form", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.label_4.setText(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Thumbnail:", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )

        self.pushButton.setText(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Browse", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )

        self.screenshotButton.setText(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Screenshot", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )

        self.label_5.setText(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Comment:", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )

        self.publishButton.setText(
            QtWidgets.QApplication.translate(
                "ExportOptions", "Publish!", None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )


class ExportOptionsWidget(QtWidgets.QWidget):
    def __init__(self, parent, task=None, connector=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_ExportOptions()
        self.ui.setupUi(self)
        self.stackedOptionsWidget = StackedOptionsWidget(
            self, connector=connector
        )

        xml = self.getXml()

        self.stackedOptionsWidget.initStackedOptions(xml)
        self.ui.optionsPlaceHolderLayout.addWidget(self.stackedOptionsWidget)
        self.ui.progressBar.hide()

    def getXml(self):
        xml = """<?xml version="1.0" encoding="UTF-8" ?>
        <options>
            <assettype name="default">
                <tab name="Options">
                </tab>
            </assettype>
            {0}
        </options>
        """
        xmlExtraAssetTypes = ""
        assetHandler = ftrack_connector.FTAssetHandlerInstance.instance()
        assetTypesStr = sorted(assetHandler.getAssetTypes())
        for assetTypeStr in assetTypesStr:
            assetClass = assetHandler.getAssetClass(assetTypeStr)
            if hasattr(assetClass, 'exportOptions'):
                xmlExtraAssetTypes += '<assettype name="' + assetTypeStr + '">'
                xmlExtraAssetTypes += assetClass.exportOptions()
                xmlExtraAssetTypes += '</assettype>'

        xml = xml.format(xmlExtraAssetTypes)

        return xml

    def resetOptions(self):
        '''Reset IO options'''
        xml = self.getXml()
        self.stackedOptionsWidget.resetOptions(xml)

    @QtCore.Slot(str)
    def setStackedWidget(self, stackName):
        self.stackedOptionsWidget.setCurrentPage(stackName)

    def getOptions(self):
        '''Return the options'''
        return self.stackedOptionsWidget.getOptions()

    def getComment(self):
        '''Return the comment'''
        return self.ui.commentTextEdit.toPlainText()

    def getThumbnail(self):
        '''Return the thumbnail'''
        return self.ui.thumbnailLineEdit.text()

    @QtCore.Slot()
    def setThumbnailFilename(self):
        '''Handle the thumbnail name generation'''
        shot = ftrack.Task(os.environ['FTRACK_SHOTID'])
        proj_root = shot.getProject().getRoot()
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open Image"),
            proj_root,
            self.tr("Image Files (*.png *.jpg *.jpeg")
        )
        self.ui.thumbnailLineEdit.setText(fileName[0])

    @QtCore.Slot()
    def takeScreenshot(self):
        '''Take a screenshot of the current window'''
        fileName = maya_connector.takeScreenshot()
        self.ui.thumbnailLineEdit.setText(fileName)

    def setComment(self, comment):
        '''Set comment'''
        self.ui.commentTextEdit.clear()
        self.ui.commentTextEdit.appendPlainText(comment)

    def setProgress(self, progressInt):
        '''Set progress bar to the given progressInt'''
        if not self.ui.progressBar.isVisible():
            self.ui.progressBar.show()
        self.ui.progressBar.setProperty("value", progressInt)
        if progressInt == 100:
            self.ui.progressBar.hide()

    def setMessage(self, message):
        '''Set message with the provided *message*'''
        self.ui.publishMessageLabel.setText(message)
