# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
from QtExt import QtGui, QtCore, QtWidgets

from ftrack_connect.ui.widget.web_view import WebViewWidget
from ftrack_connect.ui.widget.header import Header
from ftrack_connect.ui.theme import applyTheme

import ftrack


class FtrackTasksDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, connector=None):
        ''''Initialize dialog with *parent* and *connector* instance.'''
        if not connector:
            raise ValueError(
                'Please provide a connector object for {0}'.format(
                    self.__class__.__name__
                )
            )
        self.connector = connector
        if not parent:
            self.parent = self.connector.getMainWindow()
        super(FtrackTasksDialog, self).__init__(self.parent)
        applyTheme(self, 'integration')
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )
        self.setMinimumWidth(500)
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalMainLayout = QtWidgets.QVBoxLayout(self)
        self.horizontalLayout = QtWidgets.QHBoxLayout()

        self.headerWidget = Header(getpass.getuser(), self)
        self.headerWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self.verticalMainLayout.addWidget(self.headerWidget)

        self.tasksWidget = WebViewWidget(self)

        url = ftrack.getWebWidgetUrl('tasks', theme='tf')

        self.tasksWidget.setUrl(url)
        self.horizontalLayout.addWidget(self.tasksWidget)
        self.verticalMainLayout.addLayout(self.horizontalLayout)

        self.setObjectName('ftrackTasks')
        self.setWindowTitle("ftrackTasks")

    def keyPressEvent(self, e):
        '''Handle the key press Event'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackTasksDialog, self).keyPressEvent(e)
