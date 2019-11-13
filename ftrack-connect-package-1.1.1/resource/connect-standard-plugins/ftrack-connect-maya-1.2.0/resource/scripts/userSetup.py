# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import maya.cmds as mc
import maya.mel as mm
import logging
import ftrack
import functools

import ftrack_connect.util
import ftrack_connect.asset_version_scanner
import ftrack_connect.config

from ftrack_connect_maya.usage import send_event
from ftrack_connect_maya.connector import Connector
from ftrack_connect_maya.connector.mayacon import DockedWidget

logger = logging.getLogger(
    'ftrack_connect_maya'
)

ftrack.setup()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
)

created_dialogs = dict()

connector = Connector()


def open_dialog(dialog_class):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class(connector=connector)
        ftrack_docked_dialog = DockedWidget(ftrack_dialog)
        created_dialogs[dialog_name] = ftrack_docked_dialog

    created_dialogs[dialog_name].show()


def loadAndInit():
    '''Load and Init the maya plugin, build the widgets and set the menu'''
    # Load the ftrack maya plugin

    # Maya 2018 on windows may hang if an attempt is made to
    # load Qt.QtWebEngineWidgets, we check the version and
    # os and disable the webwidgets if applicable.

    if mc.about(win=True):
        match = re.match(
            '([0-9]{4}).*', mc.about(version=True)
        )

        if int(match.groups()[0]) >= 2018:
            import QtExt

            # Disable web widgets.
            QtExt.is_webwidget_supported = lambda: False

            logger.debug(
                'Disabling webwidgets due to maya 2018 '
                'QtWebEngineWidgets incompatibility.'
            )


    mc.loadPlugin('ftrackMayaPlugin.py', quiet=True)
    # Create new maya connector and register the assets
    connector.registerAssets()

    # Check if maya is in batch mode
    if mc.about(batch=True):
        return

    gMainWindow = mm.eval('$temp1=$gMainWindow')
    if mc.menu('ftrack', exists=True):
        mc.deleteUI('ftrack')

    ftrackMenu = mc.menu(
        'ftrack',
        parent=gMainWindow,
        tearOff=False,
        label='ftrack'
    )

    from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
    from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
    from ftrack_connect_maya.ui.info import FtrackMayaInfoDialog
    from ftrack_connect_maya.ui.publisher import PublishAssetDialog
    from ftrack_connect_maya.ui.tasks import FtrackTasksDialog

    dialogs = [
        (FtrackImportAssetDialog, 'Import asset'),
        (
            functools.partial(PublishAssetDialog, currentEntity=currentEntity),
            'Publish asset'
        ),
        'divider',
        (FtrackAssetManagerDialog, 'Asset manager'),
        'divider',
        (FtrackMayaInfoDialog, 'Info'),
        (FtrackTasksDialog, 'Tasks')
    ]

    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            mc.menuItem(divider=True)
            continue

        dialog_class, label = item

        mc.menuItem(
            parent=ftrackMenu,
            label=label,
            command=(
                lambda x, dialog_class=dialog_class: open_dialog(dialog_class)
            )
        )

    send_event(
        'USED-FTRACK-CONNECT-MAYA'
    )



def handle_scan_result(result, scanned_ftrack_nodes):
    '''Handle scan *result*.'''
    message = []
    for partial_result, ftrack_node in zip(result, scanned_ftrack_nodes):
        if partial_result is None:
            # The version was not found on the server, probably because it has
            # been deleted.
            continue

        scanned = partial_result.get('scanned')
        latest = partial_result.get('latest')
        if scanned['version'] != latest['version']:
            message.append(
                '{0} can be updated from v{1} to v{2}'.format(
                    ftrack_node, scanned['version'], latest['version']
                )
            )

    if message:
        confirm = mc.confirmDialog(
            title='Scan result',
            message='\n'.join(message),
            button=['Open AssetManager', 'Close'],
            defaultButton='Close',
            cancelButton='Close',
            dismissString='Close'
        )

        if confirm != 'Close':
            from ftrack_connect.ui.widget.asset_manager import (
                FtrackAssetManagerDialog
            )

            global assetManagerDialog
            assetManagerDialog = FtrackAssetManagerDialog(connector=connector)
            assetManagerDialog.show()


def scan_for_new_assets():
    '''Check whether there is any new asset.'''
    nodes_in_scene = mc.ls(type='ftrackAssetNode')

    check_items = []
    scanned_ftrack_nodes = []
    for ftrack_node in nodes_in_scene:
        if not mc.referenceQuery(ftrack_node, isNodeReferenced=True):
            asset_version_id = mc.getAttr('{0}.assetId'.format(ftrack_node))
            if asset_version_id is None:
                mc.warning(
                    'FTrack node "{0}" does not contain data!'.format(ftrack_node)
                )
                continue

            component_name = mc.getAttr(ftrack_node + '.assetTake')
            check_items.append({
                'asset_version_id': asset_version_id,
                'component_name': component_name
            })
            scanned_ftrack_nodes.append(ftrack_node)

    if scanned_ftrack_nodes:
        import ftrack_api
        session = ftrack_api.Session(
            auto_connect_event_hub=False,
            plugin_paths=None
        )
        scanner = ftrack_connect.asset_version_scanner.Scanner(
            session=session,
            result_handler=(
                lambda result: ftrack_connect.util.invoke_in_main_thread(
                    handle_scan_result,
                    result,
                    scanned_ftrack_nodes
                )
            )
        )
        scanner.scan(check_items)


def refAssetManager():
    '''Refresh asset manager'''
    from ftrack_connect.connector import panelcom
    panelComInstance = panelcom.PanelComInstance.instance()
    panelComInstance.refreshListeners()


def framerateInit():
    '''Set the initial framerate with the values set on the shot'''
    import ftrack
    shotId = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shotId)
    fps = str(int(shot.get('fps')))

    mapping = {
        '15': 'game',
        '24': 'film',
        '25': 'pal',
        '30': 'ntsc',
        '48': 'show',
        '50': 'palf',
        '60': 'ntscf',
    }

    fpsType = mapping.get(fps, 'pal')
    mc.warning('Setting current unit to {0}'.format(fps))
    mc.currentUnit(time=fpsType)


if not Connector.batch():
    mc.scriptJob(e=["SceneOpened", "scan_for_new_assets()"], permanent=True)
    mc.scriptJob(e=["SceneOpened", "refAssetManager()"], permanent=True)
    mc.evalDeferred("loadAndInit()")
    mc.evalDeferred("framerateInit()")
    mc.evalDeferred("Connector.setTimeLine()")


ftrack_connect.config.configure_logging(
    'ftrack_connect_maya', level='WARNING'
)
