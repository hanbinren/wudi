# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class CollectCameras(pyblish.api.ContextPlugin):
    '''Collect cameras from Maya.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add maya camera instances.'''
        import maya.cmds as mc

        self.log.debug('Started collecting camera from scene.')

        selection = mc.ls(assemblies=True, long=True, sl=1)

        for group in mc.ls(assemblies=True, long=True):
            if mc.ls(group, dag=True, type='camera'):
                if group in ['|top', '|front', '|side']:
                    continue

                instance = context.create_instance(
                    group, families=['ftrack', 'camera']
                )

                instance.data['publish'] = group in selection
                instance.data['ftrack_components'] = []

                self.log.debug(
                    'Collected camera instance {0!r} {1!r}.'.format(
                        group, instance
                    )
                )
