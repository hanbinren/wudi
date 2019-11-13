# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class CollectCameras(pyblish.api.ContextPlugin):
    '''Collect Cameras from Nuke.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add nuke camera instances.'''
        import nuke

        self.log.debug('Started collecting camera from scene.')

        selection = nuke.selectedNodes()

        for node in nuke.allNodes():
            if node.Class() == 'Camera' or node.Class() == 'Camera2':
                instance = context.create_instance(
                    node.name(), families=['ftrack', 'camera']
                )

                instance.data['publish'] = node in selection
                instance.data['ftrack_components'] = []

                self.log.debug(
                    'Collected camera instance {0!r} {1!r}.'.format(
                        node.name(), instance
                    )
                )
