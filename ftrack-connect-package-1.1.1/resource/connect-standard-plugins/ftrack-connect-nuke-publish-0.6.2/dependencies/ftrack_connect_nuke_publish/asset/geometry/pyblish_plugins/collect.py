# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class CollectWriteGeoNodes(pyblish.api.ContextPlugin):
    '''Collect nuke write geo nodes from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add nuke write geo node instances.'''
        import nuke

        self.log.debug('Started collecting write geo nodes from scene.')

        selection = nuke.selectedNodes()

        for node in nuke.allNodes():
            if node.Class() == 'WriteGeo':
                instance = context.create_instance(
                    node.name(), families=['ftrack', 'geo']
                )
                instance.data['publish'] = node in selection
                instance.data['ftrack_components'] = []

                self.log.debug(
                    'Collected write geo node instance {0!r} {1!r}.'.format(
                        node.name(), instance
                    )
                )
