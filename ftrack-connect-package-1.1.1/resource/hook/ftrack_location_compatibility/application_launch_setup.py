# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import sys
import os
import logging
import ftrack
import ftrack_connect.application

try:
    import ftrack_location_compatibility
except ImportError:
    dependencies_path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'package')
    )
    sys.path.append(dependencies_path)
    import ftrack_location_compatibility

import ftrack_connect.application

logger = logging.getLogger(
    'ftrack-location-compatibility-application-launch-setup'
)


def setup(event):
    '''Add FTRACK_EVENT_PLUGIN_PATH back to envs when application start.'''
    if 'options' not in event['data']:
        event['data']['options'] = {'env': {}}

    environment = event['data']['options']['env']

    _location_compatibility_hook_path = os.path.abspath(
        os.path.dirname(__file__)
    )

    ftrack_location_compatibility_path = os.path.abspath(
        os.path.join(
            os.path.dirname(ftrack_location_compatibility.__file__),
            '..',
            'package'
        )
    )

    ftrack_connect.application.appendPath(
        ftrack_location_compatibility_path,
        'PYTHONPATH',
        environment
    )

    location_compatibility_hook_path = os.environ.get(
        'FTRACK_LOCATION_COMPATIBILITY_PLUGIN_PATH',
        _location_compatibility_hook_path
    )

    ftrack_connect.application.appendPath(
        location_compatibility_hook_path,
        'FTRACK_EVENT_PLUGIN_PATH',
        environment
    )


def register(registry, **kw):
    '''Register hooks.'''
    logger.debug('Registering application launch setup.')
    # Run when application are launched
    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.connect.application.launch',
        setup
    )
