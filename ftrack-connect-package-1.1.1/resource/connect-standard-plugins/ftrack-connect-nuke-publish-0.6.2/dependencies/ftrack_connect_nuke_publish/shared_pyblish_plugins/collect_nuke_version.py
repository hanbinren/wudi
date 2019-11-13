# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
import nuke


class CollectNukeVersion(pyblish.api.ContextPlugin):
    '''Collect nuke version.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add Nuke version information.'''

        context.data['software'] = {
            'name': 'Nuke',
            'version': nuke.NUKE_VERSION_STRING
        }

        self.log.debug('Collected nuke version information.')


pyblish.api.register_plugin(CollectNukeVersion)
