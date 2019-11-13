# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import functools

import ftrack_api
import ftrack_connect_pipeline.asset

from ftrack_connect_nuke_publish.asset.geometry import geometry_asset

FTRACK_ASSET_TYPE = 'geo'


def create_asset_publish():
    '''Return asset publisher.'''
    return geometry_asset.PublishGeo(
        description='publish geometry to ftrack.',
        asset_type_short=FTRACK_ASSET_TYPE,
        enable_reviewable_component=False
    )


def register_asset_plugin(session, event):
    '''Register asset plugin.'''
    geo = ftrack_connect_pipeline.asset.Asset(
        identifier=FTRACK_ASSET_TYPE,
        label='Geometry',
        icon='extension',
        create_asset_publish=create_asset_publish
    )
    # Register geo asset on session. This makes sure that discover is called
    # for import and publish.
    geo.register(session)


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.pipeline.register-assets',
        functools.partial(register_asset_plugin, session)
    )
