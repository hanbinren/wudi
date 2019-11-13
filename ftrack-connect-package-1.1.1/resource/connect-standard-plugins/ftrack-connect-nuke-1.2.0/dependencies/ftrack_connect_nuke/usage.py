# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack


import ftrack_connect_nuke
import ftrack_connect.usage


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    import nuke

    if metadata is None:
        metadata = {
            'nuke_version': nuke.NUKE_VERSION_STRING,
            'ftrack_connect_nuke_version': ftrack_connect_nuke.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
