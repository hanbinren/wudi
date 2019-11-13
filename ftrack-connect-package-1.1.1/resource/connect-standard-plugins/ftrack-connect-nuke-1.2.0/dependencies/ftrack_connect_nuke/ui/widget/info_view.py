# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from QtExt import QtGui, QtWidgets
from ftrack_connect_foundry.ui.info_view import InfoView
import nuke


class AssetInfoView(InfoView):
    '''Display information about selected entity.'''

    _kIdentifier = 'com.ftrack.asset_information_panel'
    _kDisplayName = 'Asset Info'

    def __init__(self, bridge, parent=None):
        '''Initialise InvfoView.'''
        super(AssetInfoView, self).__init__(
            bridge, parent=parent
        )

        nodes = nuke.selectedNodes()
        node = nodes[0]

        asset_version_id = node.knob('assetVersionId')
        asset_id = asset_version_id.value()
        asset_id = asset_id.split('ftrack://')[-1].split('?')[0]
        self.setEntityReference(asset_id)
