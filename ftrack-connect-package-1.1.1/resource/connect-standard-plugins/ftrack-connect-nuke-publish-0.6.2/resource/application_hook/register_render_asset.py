# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import functools

import ftrack_api
import ftrack_connect_pipeline.asset

from ftrack_connect_nuke_publish.asset.render import render_asset

FTRACK_ASSET_TYPE = 'render'


def create_asset_publish():
    '''Return asset publisher.'''
    return render_asset.PublishRender(
        description='publish render to ftrack.',
        asset_type_short=FTRACK_ASSET_TYPE
    )


def register_asset_plugin(session, event):
    '''Register asset plugin.'''
    render = ftrack_connect_pipeline.asset.Asset(
        identifier=FTRACK_ASSET_TYPE,
        label='Render',
        icon='video-collection',
        create_asset_publish=create_asset_publish
    )
    # Register render asset on session. This makes sure that discover is called
    # for import and publish.
    render.register(session)


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.pipeline.register-assets',
        functools.partial(register_asset_plugin, session)
    )
