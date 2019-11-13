# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import weakref
import logging

import ftrack_api
import ftrack

try:
    import ftrack_location_compatibility
except ImportError:
    dependencies_path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'package')
    )
    sys.path.append(dependencies_path)
    import ftrack_location_compatibility


logger = logging.getLogger('ftrack-location-compatibility-register')

def new_api_event_listener(event):
    '''Handle *event*.'''
    session = event['data']['session']

    # Store session on cached module.
    if session not in [ref() for ref in ftrack_location_compatibility.sessions]:
        ftrack_location_compatibility.sessions.append(
            weakref.ref(session)
        )

    if ftrack_location_compatibility.is_legacy_location_registered:
        logger.debug(
            'Called by legacy and new api, continue and register locations.'''
        )

        ftrack_location_compatibility.register_locations(
            session
        )


def legacy_location_registered():
    '''Handle legacy locations being registered.'''

    if not ftrack_location_compatibility.is_legacy_location_registered:
        logger.debug(
            'Called by legacy and new api, continue and register locations.'''
        )

        ftrack_location_compatibility.sessions = [
            ref for ref in ftrack_location_compatibility.sessions if ref()
        ]

        for session in [ref() for ref in ftrack_location_compatibility.sessions]:
            if session:
                ftrack_location_compatibility.register_locations(
                    session
                )

    # Store legacy location registry information on cached module.
    ftrack_location_compatibility.is_legacy_location_registered = True

def register(api_object):
    '''Register to *session*.'''
    if isinstance(api_object, ftrack_api.Session):
        if not ftrack_location_compatibility.is_legacy_api_patched:
            ftrack_location_compatibility.is_legacy_api_patched = True

            # Patch the legacy api to allow multipe calls to setup
            ftrack_location_compatibility.patch_legacy_api()

            if not ftrack.EVENT_HUB.connected:
                # Call setup in the legacy api if we are not already
                # connected, this is to ensure that all locations are available.
                ftrack.LOCATION_PLUGINS.discover()
                ftrack.EVENT_HUB.connect()

        logger.debug('Register called for session.')

        session = api_object
        session.event_hub.subscribe(
            'topic=ftrack.api.session.configure-location',
            new_api_event_listener
        )

    if api_object is ftrack.EVENT_HANDLERS:
        logger.debug(
            'Register called for legacy event handlers registry.'
        )

        legacy_location_registered()