# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class CollectNukeScript(pyblish.api.ContextPlugin):
    '''Collect nuke write nodes from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add nuke write node instances.'''
        self.log.debug('Started collecting scene script.')

        instance = context.create_instance(
            'Scene', families=['ftrack', 'scene']
        )
        instance.data['publish'] = True
        instance.data['ftrack_components'] = []

        self.log.debug(
            'Collected scene instance {0!r}.'.format(
                instance
            )
        )

pyblish.api.register_plugin(CollectNukeScript)
