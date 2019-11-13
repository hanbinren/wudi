# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os

import ftrack
import getpass
import functools

import FnAssetAPI
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets
from FnAssetAPI import specifications

import ftrack_connect_nuke
from ftrack_connect.connector import HelpFunctions
from ftrack_connect.ui.widget import header

from FnAssetAPI.ui.dialogs import TabbedBrowserDialog
from ftrack_connect_nuke import connector
from ftrack_connect.ui.theme import applyTheme
from ftrack_connect.ui import resource

class TableKnob():
    def makeUI(self):
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(['', 'Filename', 'Component', 'NodeName', '', '', ''])
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setColumnWidth(0, 25)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 25)
        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.setColumnHidden(5, True)
        self.tableWidget.setColumnHidden(6, True)
        self.tableWidget.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setTextElideMode(QtCore.Qt.ElideLeft)
        self.tableWidget.setMinimumHeight(200)

        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.tableWidget.updateValue = self.updateValue

        return self.tableWidget

    def updateValue(self):
        pass


class FtrackPublishLocale(specifications.LocaleSpecification):
    _type = "ftrack.publish"


class BrowseKnob():

    def __init__(self):
        self.current_task = ftrack.Task(
            os.getenv('FTRACK_TASKID',
                os.getenv('FTRACK_SHOTID')
            )
        )

        self.targetTask = self.current_task.getEntityRef()
        session = FnAssetAPI.SessionManager.currentSession()
        self.context = session.createContext()
        self.context.access = self.context.kWrite
        self.context.locale = FtrackPublishLocale()
        self.spec = specifications.ImageSpecification()
        self.spec.referenceHint = self.targetTask

    def makeUI(self):
        self.mainWidget = QtWidgets.QWidget()
        applyTheme(self.mainWidget, 'integration')

        self.mainWidget.setContentsMargins(0, 0, 0, 0)
        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.mainWidget.setLayout(self.hlayout)

        self._lineEdit = QtWidgets.QLineEdit()
        self._lineEdit.setText(HelpFunctions.getPath(self.current_task, slash=True))
        self.hlayout.addWidget(self._lineEdit)

        self._browse = QtWidgets.QPushButton("Browse")
        self.hlayout.addWidget(self._browse)

        QtCore.QObject.connect(self._browse, QtCore.SIGNAL('clicked()'), self.openBrowser)

        return self.mainWidget

    def updateValue(self):
        pass

    def openBrowser(self):
        browser = TabbedBrowserDialog.buildForSession(self.spec, self.context)
        browser.setWindowTitle(FnAssetAPI.l("Publish to"))
        browser.setAcceptButtonTitle("Set")
        if not browser.exec_():
            return ''

        self.targetTask = browser.getSelection()[0]
        obj = connector.Connector.objectById(self.targetTask)
        self._lineEdit.setText(HelpFunctions.getPath(obj, slash=True))


# Header widget cache used to fix bug in Nuke that causes the HeaderKnob
# to be instansiated multiple times. Handle destroy event to ensure that it
# is re-created if pane and header gets destroyed.
HEADER_WIDGET_CACHE = dict()


def handleHeaderDestroyed(cacheId, *args, **kwargs):
    '''Remove header from dictionary.'''
    if cacheId in HEADER_WIDGET_CACHE:
        HEADER_WIDGET_CACHE.pop(cacheId)


class HeaderKnob():
    '''Header knob.'''

    def __init__(self, cacheId):
        '''Instansiate header knob with *cacheId*.

        *cacheId* is used to retrieve a header that is already created.

        '''
        if cacheId not in HEADER_WIDGET_CACHE:
            headerWidget = header.Header(
                getpass.getuser(), parent=None
            )
            applyTheme(headerWidget, 'integration')
            headerWidget.destroyed.connect(
                functools.partial(handleHeaderDestroyed, cacheId)
            )

            HEADER_WIDGET_CACHE[cacheId] = headerWidget

        self.headerWidget = HEADER_WIDGET_CACHE[cacheId]

    def makeUI(self):
        '''Return widget.'''
        return self.headerWidget

    def updateValue(self):
        pass
