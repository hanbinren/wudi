# :copyright: Copyright (c) 2016 ftrack

import os

import MaxPlus
import sys

# Discover 3dsmax version.
raw_max_version = MaxPlus.FPValue()
MaxPlus.Core.EvalMAXScript(
    'getFileVersion "$max/3dsmax.exe"', raw_max_version
)
max_version = int(raw_max_version.Get().split(',')[0])

if max_version < 19:
    # Max 2015 & 2016 require this patch to avoid crashing during print and logging.
    # https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_B3FF3632_F177_4A90_AE3D_D36603B7A2F3_htm
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr

import functools
from QtExt import QtCore

from ftrack_connect_3dsmax.connector import Connector
from ftrack_connect_3dsmax.connector.maxcallbacks import *


try:
    import ftrack
    ftrack.setup()
except:
    pass


class FtrackMenuBuilder(object):
    '''Build the Ftrack menu.'''
    MENU_NAME = 'Ftrack'

    def __init__(self):
        '''Initialize the menu builder.'''
        if MaxPlus.MenuManager.MenuExists(self.MENU_NAME):
             MaxPlus.MenuManager.UnregisterMenu(self.MENU_NAME)

        self.__menu_builder = MaxPlus.MenuBuilder(self.MENU_NAME)

    def add_separator(self):
        '''Add a separator between menu items.'''
        self.__menu_builder.AddSeparator()

    def add_item(self, action):
        '''Add a menu item.'''
        self.__menu_builder.AddItem(action)

    def create(self):
        '''Create the Ftrack menu.'''
        self.__menu_builder.Create(MaxPlus.MenuManager.GetMainMenu())

    def __del__(self):
        '''Unregister the Ftrack menu.'''
        MaxPlus.MenuManager.UnregisterMenu(self.MENU_NAME)

class DisableMaxAcceleratorsEventFilter(QtCore.QObject):
    """An event filter that disables the 3ds Max accelerators while a widget is
    visible. This class is used when running in Max 2016, where widgets cannot
    be parented to Max's main window, and as a result they don't get the
    keyboard focus unless Max accelerators are disabled.
    """
    def eventFilter(self, obj, event):
        '''Enable / disable Max accelerators when a widget is shown / hidden.'''
        if event.type() == QtCore.QEvent.Show:
            MaxPlus.Core.EvalMAXScript('enableAccelerators = false')
        elif event.type() == QtCore.QEvent.Close:
            MaxPlus.Core.EvalMAXScript('enableAccelerators = true')
        elif event.type() == QtCore.QEvent.Hide:
            MaxPlus.Core.EvalMAXScript('enableAccelerators = true')

        return False

connector = None
ftrackMenuBuilder = None

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID',
    os.getenv('FTRACK_SHOTID')))

# Dialogs.
importAssetDialog = None
publishAssetDialog = None
assetManagerDialog = None
infoDialog = None
tasksDialog = None


def __adjustDialogLayoutMargins(dialog):
    '''Add extra spacing to a dialog main layout in Max 2017 and newer.'''
    # Get the Max version.
    vers = MaxPlus.Core.EvalMAXScript('getFileVersion "$max/3dsmax.exe"').Get()

    # Add an extra 5 pixels margin for Max 2017 or newer.
    if not vers.startswith('18'):
        dialog.mainLayout.setContentsMargins(5, 5, 5, 5)

def __createAndInitFtrackDialog(Dialog):
    '''Create an instance of a dialog and initialize it for use in 3ds Max'''
    dialog = Dialog(connector=connector)

    try:
        # AttachQWidgetToMax is only available in Max 2017 and newer.
        MaxPlus.AttachQWidgetToMax(dialog, isModelessDlg=True)
    except AttributeError:
        # If running 2016, the dialog cannot be parented to Max's window.
        dialog.installEventFilter(
            DisableMaxAcceleratorsEventFilter(dialog))

    # Make the dialog initial size bigger, as in Max by default they appear too small.
    dialog.resize(dialog.width(), 1.7 * dialog.height())
    return dialog

def __createDialogAction(actionName, callback):
    '''Create an action and add it to the menu builder if it is valid'''
    global ftrackMenuBuilder

    action = MaxPlus.ActionFactory.Create(
        actionName, actionName, callback)
    if action._IsValidWrapper():
        ftrackMenuBuilder.add_item(action)
        return action

def showImportAssetDialog():
    '''Create the import asset dialog if it does not exist and show it'''
    global importAssetDialog

    if not importAssetDialog:
        from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
        importAssetDialog = __createAndInitFtrackDialog(FtrackImportAssetDialog)
        __adjustDialogLayoutMargins(importAssetDialog)

    importAssetDialog.show()

def showPublishAssetDialog():
    '''Create the publish asset dialog if it does not exist and show it'''
    global publishAssetDialog

    if not publishAssetDialog:
        from ftrack_connect_3dsmax.ui.publisher import PublishAssetDialog
        publishAssetDialog = __createAndInitFtrackDialog(functools.partial(
            PublishAssetDialog, currentEntity=currentEntity))
        __adjustDialogLayoutMargins(publishAssetDialog)

    publishAssetDialog.show()

def showAssetManagerDialog():
    '''Create the asset manager dialog if it does not exist and show it'''
    global assetManagerDialog

    if not assetManagerDialog:
        from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
        assetManagerDialog = __createAndInitFtrackDialog(FtrackAssetManagerDialog)

        # Make some columns of the asset manager dialog wider to compensate
        # for the buttons appearing very small with Max's 2017 custom Qt stylesheet.
        tableWidget = assetManagerDialog.assetManagerWidget.ui.AssertManagerTableWidget
        tableWidget.setColumnWidth(0, 25)
        tableWidget.setColumnWidth(9, 35)
        tableWidget.setColumnWidth(11, 35)
        tableWidget.setColumnWidth(15, 35)

    assetManagerDialog.show()

def showInfoDialog():
    '''Create the info dialog if it does not exist and show it'''
    global infoDialog

    if not infoDialog:
        from ftrack_connect_3dsmax.ui.info import FtrackMaxInfoDialog
        infoDialog = __createAndInitFtrackDialog(FtrackMaxInfoDialog)

    infoDialog.show()

def showTasksDialog():
    '''Create the tasks dialog if it does not exist and show it'''
    global tasksDialog

    if not tasksDialog:
        from ftrack_connect_3dsmax.ui.tasks import FtrackTasksDialog
        tasksDialog = __createAndInitFtrackDialog(FtrackTasksDialog)

    tasksDialog.show()

def initFtrack():
    '''Initialize Ftrack, register assets and build the Ftrack menu.'''
    global connector
    connector = Connector()
    connector.registerAssets()

    global ftrackMenuBuilder
    ftrackMenuBuilder = FtrackMenuBuilder()

    __createDialogAction("Import Asset", showImportAssetDialog)
    __createDialogAction("Publish Asset", showPublishAssetDialog)
    ftrackMenuBuilder.add_separator()

    # Save the showAssetManagerAction for later use.
    showAssetManagerAction = __createDialogAction(
        "Asset Manager", showAssetManagerDialog)

    ftrackMenuBuilder.add_separator()
    __createDialogAction("Info", showInfoDialog)
    __createDialogAction("Tasks", showTasksDialog)

    # Create the Ftrack menu.
    ftrackMenuBuilder.create()

    registerMaxOpenFileCallbacks(showAssetManagerAction)

    # Send usage event.
    from ftrack_connect_3dsmax.connector import usage
    usage.send_event('USED-FTRACK-CONNECT-3DS-MAX')

initFtrack()
