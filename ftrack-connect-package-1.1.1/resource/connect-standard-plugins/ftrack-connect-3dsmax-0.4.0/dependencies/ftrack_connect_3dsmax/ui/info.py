# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtCore, QtGui, QtWidgets

from ftrack_connect.ui.widget.info import FtrackInfoDialog
from ftrack_connect.ui.theme import applyTheme


class FtrackMaxInfoDialog(FtrackInfoDialog):
    def __init__(self, parent=None, connector=None):
        super(FtrackMaxInfoDialog, self).__init__(
            parent=parent,
            connector=connector
        )

        self.headerWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        applyTheme(self, 'integration')

    def keyPressEvent(self, e):
        '''Handle Esc key press event'''
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackMaxInfoDialog, self).keyPressEvent(e)
