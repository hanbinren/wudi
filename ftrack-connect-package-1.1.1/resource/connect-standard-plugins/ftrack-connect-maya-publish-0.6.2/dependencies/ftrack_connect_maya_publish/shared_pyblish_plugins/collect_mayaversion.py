# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
import maya.cmds as mc


class CollectMayaVersion(pyblish.api.ContextPlugin):
    '''Collect maya version.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add Maya version information.'''

        context.data['software'] = {
            'name': 'Maya',
            'version': mc.about(v=True)
        }

        self.log.debug('Collected maya version information.')


pyblish.api.register_plugin(CollectMayaVersion)
