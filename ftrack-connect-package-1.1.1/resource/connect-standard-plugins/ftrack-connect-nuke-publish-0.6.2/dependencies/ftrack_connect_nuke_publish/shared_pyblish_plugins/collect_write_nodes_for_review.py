# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class CollectWriteNodeForReviewScript(pyblish.api.ContextPlugin):
    '''Collect nuke write nodes from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add nuke write node instances.'''
        from ftrack_connect_pipeline import constant
        import nuke
        self.log.debug('Started collecting write nodes from scene.')
        selection = nuke.selectedNodes()

        for node in nuke.allNodes():
            if node.Class() == 'Write':
                instance = context.create_instance(
                    node.name(), families=constant.REVIEW_FAMILY_PYBLISH
                )
                instance.data['publish'] = node in selection

                self.log.debug(
                    'Collected Write node instance {0!r} {1!r}.'.format(
                        node.name(), instance
                    )
                )


pyblish.api.register_plugin(CollectWriteNodeForReviewScript)
