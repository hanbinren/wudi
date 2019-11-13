# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
from ftrack_connect_pipeline import constant


class ReviewableComponentValidator(pyblish.api.InstancePlugin):
    '''Validate exist input to write node.'''

    order = pyblish.api.ValidatorOrder

    families = constant.REVIEW_FAMILY_PYBLISH
    match = pyblish.api.Subset

    label = 'Validate reviewable write node.'

    optional = False

    def process(self, instance):
        '''Validate *instance*.'''
        import nuke

        self.log.debug(
            u'Validating Reviewable component generation for {0!r}'.format(
                instance.name
            )
        )

        write_node = nuke.toNode(instance.name)
        input_node = write_node.input(0)
        assert input_node, (
            u'No input node found for {0}'.format(instance.name)
        )


pyblish.api.register_plugin(ReviewableComponentValidator)
