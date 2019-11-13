# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import functools

import ftrack_api
import ftrack_connect_pipeline.asset

from ftrack_connect_maya_publish.asset.scene import scene_asset

FTRACK_ASSET_TYPE = 'scene'


def create_asset_publish():
    '''Return asset publisher.'''
    return scene_asset.PublishScene(
        description='publish maya scene to ftrack.',
        enable_scene_as_reference=False,
        asset_type_short=FTRACK_ASSET_TYPE

    )


def register_asset_plugin(session, event):
    '''Register asset plugin.'''
    scene = ftrack_connect_pipeline.asset.Asset(
        identifier=FTRACK_ASSET_TYPE,
        label='Scene',
        icon='home',
        create_asset_publish=create_asset_publish
    )
    scene.register(session)


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.pipeline.register-assets',
        functools.partial(register_asset_plugin, session)
    )
