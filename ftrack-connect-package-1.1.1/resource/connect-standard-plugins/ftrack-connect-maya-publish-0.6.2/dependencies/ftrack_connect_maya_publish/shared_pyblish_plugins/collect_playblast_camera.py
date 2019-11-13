# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
import maya.cmds as mc


class CollectPlayblastCamera(pyblish.api.ContextPlugin):
    '''Collect maya version.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and collect maya cameras for playblast.'''
        from ftrack_connect_pipeline import constant

        for group in mc.ls(assemblies=True, long=True):
            if mc.ls(group, dag=True, type='camera'):
                instance = context.create_instance(
                    group, families=constant.REVIEW_FAMILY_PYBLISH
                )

                instance.data['publish'] = False

                self.log.debug(
                    'Collected camera instance {0!r} {1!r}.'.format(
                        group, instance
                    )
                )

        self.log.debug('Collected maya cameras for playblast.')


pyblish.api.register_plugin(CollectPlayblastCamera)
