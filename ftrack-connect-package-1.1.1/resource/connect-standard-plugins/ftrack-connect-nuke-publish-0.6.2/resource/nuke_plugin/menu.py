# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os

import nuke
import ftrack_connect_pipeline
import ftrack_connect_pipeline.global_context_switch
import ftrack_connect_pipeline.publish

import ftrack_connect_nuke_publish.plugin


plugin = ftrack_connect_nuke_publish.plugin.NukePlugin(
    context_id=os.environ['FTRACK_CONTEXT_ID']
)
ftrack_connect_pipeline.register_plugin(plugin)

global_context_switch = (
    ftrack_connect_pipeline.global_context_switch.GlobalContextSwitch(
        plugin=plugin
    )
)

publish = ftrack_connect_pipeline.publish.Publish(
    plugin=plugin
)

nuke_menu = nuke.menu('Nuke')

ftrack_menu = nuke_menu.addMenu('&ftrack')

ftrack_menu.addSeparator()

publish_submenu = ftrack_menu.addMenu('Beta')

publish_submenu.addCommand(
    'Publish', publish.open
)

publish_submenu.addCommand(
    'Switch Context', global_context_switch.open
)
