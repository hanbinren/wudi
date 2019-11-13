# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class CollectLights(pyblish.api.ContextPlugin):
    '''Collect lights from Maya.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add maya lights instances.'''
        import maya.cmds as mc

        self.log.debug('Started collecting lights from scene.')

        selection = mc.ls(assemblies=True, long=True, sl=1)

        for group in mc.ls(assemblies=True, long=True):
            if mc.ls(group, dag=True, type='light'):

                instance = context.create_instance(
                    group, families=['ftrack', 'light']
                )

                instance.data['publish'] = group in selection
                instance.data['ftrack_components'] = []

                self.log.debug(
                    'Collected light instance {0!r} {1!r}.'.format(
                        group, instance
                    )
                )
