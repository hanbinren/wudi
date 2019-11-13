# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import getpass
import logging

from QtExt import QtCore, QtWidgets, QtGui

import ftrack
from ftrack_connect.connector import FTAssetHandlerInstance

log = logging.getLogger(__file__)


class Ui_ExportAssetOptions(object):
    def setupUi(self, ExportAssetOptions):
        ExportAssetOptions.setObjectName("ExportAssetOptions")
        ExportAssetOptions.resize(429, 130)
        self.verticalLayout = QtWidgets.QVBoxLayout(ExportAssetOptions)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.assetTaskLabel = QtWidgets.QLabel(ExportAssetOptions)
        self.assetTaskLabel.setMinimumSize(QtCore.QSize(120, 0))
        self.assetTaskLabel.setMaximumSize(QtCore.QSize(120, 16777215))
        self.assetTaskLabel.setObjectName("assetTaskLabel")
        self.gridLayout.addWidget(self.assetTaskLabel, 1, 0, 1, 1)
        self.ListAssetsComboBox = QtWidgets.QComboBox(ExportAssetOptions)
        self.ListAssetsComboBox.setMinimumSize(QtCore.QSize(100, 0))
        self.ListAssetsComboBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.ListAssetsComboBox.setObjectName("ListAssetsComboBox")
        self.gridLayout.addWidget(self.ListAssetsComboBox, 0, 1, 1, 1)
        self.ListAssetNamesComboBox = QtWidgets.QComboBox(ExportAssetOptions)
        self.ListAssetNamesComboBox.setMinimumSize(QtCore.QSize(100, 0))
        self.ListAssetNamesComboBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.ListAssetNamesComboBox.setObjectName("ListAssetNamesComboBox")
        self.gridLayout.addWidget(self.ListAssetNamesComboBox, 3, 1, 1, 1)
        self.AssetNameLineEdit = QtWidgets.QLineEdit(ExportAssetOptions)
        self.AssetNameLineEdit.setEnabled(True)
        self.AssetNameLineEdit.setMinimumSize(QtCore.QSize(100, 0))
        self.AssetNameLineEdit.setMaximumSize(QtCore.QSize(200, 16777215))
        self.AssetNameLineEdit.setObjectName("AssetNameLineEdit")
        self.gridLayout.addWidget(self.AssetNameLineEdit, 4, 1, 1, 1)
        self.AssetTaskComboBox = QtWidgets.QComboBox(ExportAssetOptions)
        self.AssetTaskComboBox.setMinimumSize(QtCore.QSize(100, 0))
        self.AssetTaskComboBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.AssetTaskComboBox.setObjectName("AssetTaskComboBox")
        self.gridLayout.addWidget(self.AssetTaskComboBox, 1, 1, 1, 1)
        self.labelAssetType = QtWidgets.QLabel(ExportAssetOptions)
        self.labelAssetType.setMinimumSize(QtCore.QSize(120, 0))
        self.labelAssetType.setMaximumSize(QtCore.QSize(120, 16777215))
        self.labelAssetType.setObjectName("labelAssetType")
        self.gridLayout.addWidget(self.labelAssetType, 0, 0, 1, 1)
        self.assetNameLabel = QtWidgets.QLabel(ExportAssetOptions)
        self.assetNameLabel.setMinimumSize(QtCore.QSize(120, 0))
        self.assetNameLabel.setMaximumSize(QtCore.QSize(120, 16777215))
        self.assetNameLabel.setObjectName("assetNameLabel")
        self.gridLayout.addWidget(self.assetNameLabel, 4, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(ExportAssetOptions)
        self.label_2.setMinimumSize(QtCore.QSize(120, 0))
        self.label_2.setMaximumSize(QtCore.QSize(120, 16777215))
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.assetTaskLabel_2 = QtWidgets.QLabel(ExportAssetOptions)
        self.assetTaskLabel_2.setMinimumSize(QtCore.QSize(120, 0))
        self.assetTaskLabel_2.setMaximumSize(QtCore.QSize(120, 16777215))
        self.assetTaskLabel_2.setObjectName("assetTaskLabel_2")
        self.gridLayout.addWidget(self.assetTaskLabel_2, 2, 0, 1, 1)
        self.ListStatusComboBox = QtWidgets.QComboBox(ExportAssetOptions)
        self.ListStatusComboBox.setMinimumSize(QtCore.QSize(100, 0))
        self.ListStatusComboBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.ListStatusComboBox.setObjectName("ListStatusComboBox")
        self.gridLayout.addWidget(self.ListStatusComboBox, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(ExportAssetOptions)

        self.ListAssetsComboBox.currentIndexChanged[int].connect(
            ExportAssetOptions.setFilter
        )

        self.ListAssetsComboBox.currentIndexChanged[int].connect(
            ExportAssetOptions.emitAssetType
        )
        QtCore.QMetaObject.connectSlotsByName(ExportAssetOptions)

    def retranslateUi(self, ExportAssetOptions):
        ExportAssetOptions.setWindowTitle(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "Form",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.assetTaskLabel.setText(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "Task",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.labelAssetType.setText(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "AssetType",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.assetNameLabel.setText(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "AssetName:",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.label_2.setText(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "Existing Assets",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )
        self.assetTaskLabel_2.setText(
            QtWidgets.QApplication.translate(
                "ExportAssetOptions",
                "Task status",
                None,
                QtWidgets.QApplication.UnicodeUTF8
            )
        )


class ExportAssetOptionsWidget(QtWidgets.QWidget):
    clickedAssetSignal = QtCore.Signal(str)
    clickedAssetTypeSignal = QtCore.Signal(str)

    def __init__(self, parent, browseMode='Shot'):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_ExportAssetOptions()
        self.ui.setupUi(self)
        self.currentAssetType = None
        self.currentTask = None
        self.browseMode = browseMode
        self.ui.ListAssetsViewModel = QtGui.QStandardItemModel()

        self.ui.ListAssetsSortModel = QtCore.QSortFilterProxyModel()

        self.ui.ListAssetsSortModel.setDynamicSortFilter(True)
        self.ui.ListAssetsSortModel.setFilterKeyColumn(1)
        self.ui.ListAssetsSortModel.setSourceModel(self.ui.ListAssetsViewModel)

        self.ui.ListAssetNamesComboBox.setModel(self.ui.ListAssetsSortModel)

        self.ui.ListAssetsComboBoxModel = QtGui.QStandardItemModel()

        assetTypeItem = QtGui.QStandardItem('Select AssetType')
        self.assetTypes = []
        self.assetTypes.append('')
        self.ui.ListAssetsComboBoxModel.appendRow(assetTypeItem)

        assetHandler = FTAssetHandlerInstance.instance()
        self.assetTypesStr = sorted(assetHandler.getAssetTypes())

        for assetTypeStr in self.assetTypesStr:
            try:
                assetType = ftrack.AssetType(assetTypeStr)
            except:
                log.warning(
                    '{0} not available in ftrack'.format(assetTypeStr)
                )
                continue
            assetTypeItem = QtGui.QStandardItem(assetType.getName())
            assetTypeItem.type = assetType.getShort()
            self.assetTypes.append(assetTypeItem.type)
            self.ui.ListAssetsComboBoxModel.appendRow(assetTypeItem)

        self.ui.ListAssetsComboBox.setModel(self.ui.ListAssetsComboBoxModel)

        self.ui.AssetTaskComboBoxModel = QtGui.QStandardItemModel()
        self.ui.AssetTaskComboBox.setModel(self.ui.AssetTaskComboBoxModel)

        self.ui.ListAssetNamesComboBox.currentIndexChanged[str].connect(
            self.onAssetChanged
        )

        if browseMode == 'Task':
            self.ui.AssetTaskComboBox.hide()
            self.ui.assetTaskLabel.hide()

    def onAssetChanged(self, asset_name):
        '''Hanldes the asset name logic on asset change'''
        if asset_name != 'New':
            self.ui.AssetNameLineEdit.setEnabled(False)
            self.ui.AssetNameLineEdit.setText(asset_name)
        else:
            self.ui.AssetNameLineEdit.setEnabled(True)
            self.ui.AssetNameLineEdit.setText('')

    @QtCore.Slot(object)
    def updateView(self, ftrackEntity):
        '''Update view with the provided *ftrackEntity*'''
        try:
            self.currentTask = ftrackEntity
            project = self.currentTask.getProject()
            taskid = '11c137c0-ee7e-4f9c-91c5-8c77cec22b2c'
            # Populate statuses based on task if it is a task.
            if self.currentTask.get('object_typeid') == taskid:
                self.ui.ListStatusComboBox.show()
                self.ui.assetTaskLabel_2.show()
                self.ui.ListStatusComboBox.clear()
                statuses = project.getTaskStatuses(
                    self.currentTask.get('typeid')
                )
                for index, status, in enumerate(statuses):
                    self.ui.ListStatusComboBox.addItem(status.getName())
                    if status.get('statusid') == self.currentTask.get('statusid'):
                        self.ui.ListStatusComboBox.setCurrentIndex(index)
            else:
                self.ui.ListStatusComboBox.hide()
                self.ui.assetTaskLabel_2.hide()

            if self.browseMode == 'Task':
                task = self.currentTask.getParent()

            assets = task.getAssets(assetTypes=self.assetTypesStr)
            assets = sorted(assets, key=lambda a: a.getName().lower())
            self.ui.ListAssetsViewModel.clear()

            item = QtGui.QStandardItem('New')
            item.id = ''
            curAssetType = self.currentAssetType
            if curAssetType:
                itemType = QtGui.QStandardItem(curAssetType)
            else:
                itemType = QtGui.QStandardItem('')
            self.ui.ListAssetsViewModel.setItem(0, 0, item)
            self.ui.ListAssetsViewModel.setItem(0, 1, itemType)
            self.ui.ListAssetNamesComboBox.setCurrentIndex(0)

            blankRows = 0
            for i in range(0, len(assets)):
                assetName = assets[i].getName()
                if assetName != '':
                    item = QtGui.QStandardItem(assetName)
                    item.id = assets[i].getId()
                    itemType = QtGui.QStandardItem(
                        assets[i].getType().getShort()
                    )

                    j = i - blankRows + 1
                    self.ui.ListAssetsViewModel.setItem(j, 0, item)
                    self.ui.ListAssetsViewModel.setItem(j, 1, itemType)
                else:
                    blankRows += 1
        except:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)

    @QtCore.Slot(QtCore.QModelIndex)
    def emitAssetId(self, modelindex):
        '''Signal for emitting changes on the assetId for the give *modelIndex*'''
        clickedItem = self.ui.ListAssetsViewModel.itemFromIndex(
            self.ui.ListAssetsSortModel.mapToSource(modelindex)
        )
        self.clickedAssetSignal.emit(clickedItem.id)

    @QtCore.Slot(int)
    def emitAssetType(self, comboIndex):
        '''Signal for emitting changes on the assetId for the give *comboIndex*'''

        comboItem = self.ui.ListAssetsComboBoxModel.item(comboIndex)
        if type(comboItem.type) is str:
            self.clickedAssetTypeSignal.emit(comboItem.type)
            self.currentAssetType = comboItem.type

    @QtCore.Slot(int)
    def setFilter(self, comboBoxIndex):
        '''Set filtering for the given *comboBoxIndex*'''
        if comboBoxIndex:
            comboItem = self.ui.ListAssetsComboBoxModel.item(comboBoxIndex)
            newItem = self.ui.ListAssetsViewModel.item(0, 1)
            newItem.setText(comboItem.type)
            self.ui.ListAssetsSortModel.setFilterFixedString(comboItem.type)
        else:
            self.ui.ListAssetsSortModel.setFilterFixedString('')

    def setAssetType(self, assetType):
        '''Set the asset to the given *assetType*'''
        for position, item in enumerate(self.assetTypes):
            if item == assetType:
                assetTypeIndex = int(position)
                if assetTypeIndex == self.ui.ListAssetsComboBox.currentIndex():
                    self.ui.ListAssetsComboBox.setCurrentIndex(0)
                self.ui.ListAssetsComboBox.setCurrentIndex(assetTypeIndex)

    def setAssetName(self, assetName):
        '''Set the asset to the given *assetName*'''
        self.ui.AssetNameLineEdit.setText('')
        rows = self.ui.ListAssetsSortModel.rowCount()
        existingAssetFound = False
        for i in range(rows):
            index = self.ui.ListAssetsSortModel.index(i, 0)
            datas = self.ui.ListAssetsSortModel.data(index)

            if datas == assetName:
                self.ui.ListAssetNamesComboBox.setCurrentIndex(int(i))
                existingAssetFound = True

        if not existingAssetFound:
            self.ui.AssetNameLineEdit.setText(assetName)

    def getAssetType(self):
        '''Return the current asset type'''
        return self.currentAssetType

    @QtCore.Slot(object)
    def updateTasks(self, ftrackEntity):
        '''Update task with the provided *ftrackEntity*'''
        self.currentTask = ftrackEntity
        try:
            shotpath = self.currentTask.getName()
            taskParents = self.currentTask.getParents()

            for parent in taskParents:
                shotpath = '{0}.{1}'.format(parent.getName(), shotpath)

            self.ui.AssetTaskComboBox.clear()
            tasks = self.currentTask.getTasks()
            curIndex = 0
            ftrackuser = ftrack.User(getpass.getuser())
            taskids = [x.getId() for x in ftrackuser.getTasks()]

            for i in range(len(tasks)):
                assetTaskItem = QtGui.QStandardItem(tasks[i].getName())
                assetTaskItem.id = tasks[i].getId()
                self.ui.AssetTaskComboBoxModel.appendRow(assetTaskItem)

                if (os.environ.get('FTRACK_TASKID') == assetTaskItem.id):
                    curIndex = i
                else:
                    if assetTaskItem.id in taskids:
                        curIndex = i

            self.ui.AssetTaskComboBox.setCurrentIndex(curIndex)

        except:
            print 'Not a task'

    def getShot(self):
        '''Return the current shot'''
        if self.browseMode == 'Shot':
            return self.currentTask
        else:
            return self.currentTask.getParent()

    def getTask(self):
        '''Return the current task'''
        if self.browseMode == 'Shot':
            comboItem = self.ui.AssetTaskComboBoxModel.item(
                self.ui.AssetTaskComboBox.currentIndex()
            )
            if comboItem:
                return ftrack.Task(comboItem.id)
            else:
                return None
        else:
            return self.currentTask

    def getStatus(self):
        '''Return the current asset status'''
        return self.ui.ListStatusComboBox.currentText()

    def getAssetName(self):
        '''Retain logic for defining a new asset name'''
        if self.ui.ListAssetNamesComboBox.currentText() == 'New':
            return self.ui.AssetNameLineEdit.text()
        else:
            return self.ui.ListAssetNamesComboBox.currentText()
