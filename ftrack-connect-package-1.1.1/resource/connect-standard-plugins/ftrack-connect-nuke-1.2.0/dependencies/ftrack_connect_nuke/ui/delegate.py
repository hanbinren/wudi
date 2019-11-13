# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import FnAssetAPI
from ftrack_connect_foundry.ui import delegate
import ftrack_connect.ui.theme
from ftrack_connect.ui import resource


class Delegate(delegate.Delegate):
    def __init__(self, bridge):
        super(Delegate, self).__init__(bridge)
        self._bridge = bridge
        self.moduleName =  ".".join(__name__.split(".")[:-1])

    def populate_ftrack(self):

        import nuke
        import legacy
        from nukescripts import panels

        from ftrack_connect_nuke.connector import Connector

        # Check if QtWebKit or QWebEngine is avaliable.
        from FnAssetAPI.ui.toolkit import is_webwidget_supported
        has_webwidgets = is_webwidget_supported()

        Connector.registerAssets()

        # wrappers for initializing the widgets with
        # the correct connector object
        def wrapImportAssetDialog(*args, **kwargs):
            from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
            return FtrackImportAssetDialog(connector=Connector())

        def wrapAssetManagerDialog(*args, **kwargs):
            from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
            return FtrackAssetManagerDialog(connector=Connector())

        # Populate the ui
        nukeMenu = nuke.menu("Nuke")
        ftrackMenu = nukeMenu.addMenu("&ftrack")

        ftrackMenu.addSeparator()

        # add ftrack publish node to the menu
        ftrackMenu.addCommand('Create Publish Node', lambda: legacy.createFtrackPublish())

        ftrackMenu.addSeparator()

        globals()['ftrackImportAssetClass'] = wrapImportAssetDialog

        panels.registerWidgetAsPanel(
            '{0}.{1}'.format(__name__, 'ftrackImportAssetClass'),
            'ftrackImportAsset',
            'ftrackDialogs.ftrackImportAssetDialog'
        )

        ftrackMenu.addSeparator()

        ftrackMenu.addCommand(
            'Import Asset',
            'pane = nuke.getPaneFor("Properties.1");'
            'panel = nukescripts.restorePanel("ftrackDialogs.ftrackImportAssetDialog");'
            'panel.addToPane(pane)'
        )

        globals()['ftrackAssetManagerDialogClass'] = wrapAssetManagerDialog

        # Create the asset manager dialog entry in the menu
        panels.registerWidgetAsPanel(
            '{0}.{1}'.format(__name__, 'ftrackAssetManagerDialogClass'),
            'ftrackAssetManager',
            'ftrackDialogs.ftrackAssetManagerDialog'
        )
        ftrackMenu.addCommand(
            'Asset Manager',
            'pane = nuke.getPaneFor("Properties.1");'
            'panel = nukescripts.restorePanel("ftrackDialogs.ftrackAssetManagerDialog");'
            'panel.addToPane(pane)'
        )

        if has_webwidgets:

            def wrapAssetInfoDialog(*args, **kwargs):
                from ftrack_connect_nuke.ui.widget.info_view import AssetInfoView
                return AssetInfoView(bridge=self._bridge)

            globals()['ftrackAssetInfoDialogClass'] = wrapAssetInfoDialog

            # Create the crew dialog entry in the menu
            panels.registerWidgetAsPanel(
                '{0}.{1}'.format(__name__, 'ftrackAssetInfoDialogClass'),
                'ftrackAssetInfo',
                'ftrackDialogs.ftrackAssetInfoDialog'

            )

            ftrackMenu.addCommand(
                'Asset Info',
                'pane = nuke.getPaneFor("Properties.1");'
                'panel = nukescripts.restorePanel("ftrackDialogs.ftrackAssetInfoDialog");'
                'panel.addToPane(pane)'
            )

        ftrackMenu.addSeparator()

        if has_webwidgets:
            from ftrack_connect_foundry.ui.info_view import WorkingTaskInfoView as _WorkingTaskInfoView
            from ftrack_connect_foundry.ui.tasks_view import TasksView as _TasksView

            # Add Web Views located in the ftrack_connect_foundry package to the
            # menu for easier access.
            for widget in [
                _TasksView,
                _WorkingTaskInfoView
            ]:
                ftrackMenu.addCommand(
                    widget.getDisplayName(),
                    'pane = nuke.getPaneFor("Properties.1");'
                    'panel = nukescripts.restorePanel("{identifier}");'
                    'panel.addToPane(pane)'.format(
                        identifier=widget.getIdentifier()
                    )
                )

        ftrackMenu.addSeparator()

        # Add new entries in the ftrack menu.
        ftrackMenu.addSeparator()

        if has_webwidgets:
            from ftrack_connect_nuke.ui.widget.publish_gizmo import GizmoPublisherDialog
            ftrackMenu.addCommand('Publish gizmo', GizmoPublisherDialog)

        # Add ftrack publish node
        toolbar = nuke.toolbar("Nodes")
        ftrackNodesMenu = toolbar.addMenu("ftrack", icon="ftrack_logo.png")
        ftrackNodesMenu.addCommand('ftrackPublish', lambda: legacy.createFtrackPublish())

        # Set calbacks

        def asset_info_menu_switch():
            '''Enable and disable asset info depending on selection.'''

            this_node = nuke.thisNode()

            # Do not continue if selection is not node.
            if not isinstance(this_node, nuke.Node):
                return

            try:
                is_ftrack = this_node.knob('assetVersionId')
            except ValueError:
                is_ftrack = False

            nuke_menu = nuke.menu('Nuke')
            menu_item = nuke_menu.findItem('&ftrack')
            asset_info_menu = menu_item.findItem('Asset Info')

            if has_webwidgets and asset_info_menu:
                if is_ftrack:
                    asset_info_menu.setEnabled(True)
                else:
                    asset_info_menu.setEnabled(False)

        nuke.addKnobChanged(asset_info_menu_switch)

        # other callbacks
        nuke.addOnScriptLoad(legacy.refAssetManager)
        nuke.addOnScriptLoad(legacy.scan_for_new_assets)
        nuke.addOnUserCreate(legacy.addFtrackComponentField, nodeClass='Write')
        nuke.addOnUserCreate(legacy.addFtrackComponentField, nodeClass='WriteGeo')
        nuke.addOnUserCreate(legacy.addFtrackComponentField, nodeClass='Read')
        nuke.addKnobChanged(legacy.ftrackPublishKnobChanged, nodeClass="Group")
        nuke.addOnCreate(legacy.ftrackPublishHieroInit)

        # Set default values from environments.
        start_frame = os.environ.get('FS', 0)
        end_frame = os.environ.get('FE', 100)

        FnAssetAPI.logging.debug('Setting start frame : {}'.format(start_frame))
        nuke.knob('root.first_frame', str(start_frame))
        FnAssetAPI.logging.debug('Setting end frame : {}'.format(end_frame))
        nuke.knob('root.last_frame', str(end_frame))

    def populateUI(self, uiElement, specification, context):
        super(Delegate, self).populateUI(uiElement, specification, context)

        host = FnAssetAPI.SessionManager.currentSession().getHost()

        if host and host.getIdentifier() == 'uk.co.foundry.nuke':
            self.populate_ftrack()

            # Set font on QApplication once UI is created.
            # We do this once since it takes some time to apply the font.
            ftrack_connect.ui.theme.applyFont()


