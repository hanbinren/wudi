# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
from ftrack_connect_pipeline import constant


class ReviewableComponentExtract(pyblish.api.InstancePlugin):
    '''Create a reviewable component.'''

    order = pyblish.api.ExtractorOrder - 0.1

    families = constant.REVIEW_FAMILY_PYBLISH
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance* and add review component to context.'''

        self.log.debug(
            'Pre extracting reviewable component {0!r}'.format(
                instance.name
            )
        )

        import tempfile
        import nuke
        write = nuke.toNode(instance.name)

        # Get the input of the given write node.
        input_node = write.input(0)

        # Generate output file name for mov.
        temp_review_mov = tempfile.NamedTemporaryFile(suffix='.mov').name

        first = str(int(nuke.root().knob('first_frame').value()))
        last = str(int(nuke.root().knob('last_frame').value()))

        # Create a new write_node.
        review_node = nuke.createNode('Write')
        review_node.setInput(0, input_node)
        review_node['file'].setValue(temp_review_mov)
        review_node['file_type'].setValue('mov')
        review_node['mov64_codec'].setValue('png')

        # Store the temp write node for later deletion.
        instance.data['ftrack_tmp_review_node'] = review_node['name'].getValue()

        if write['use_limit'].getValue():
            first = write['first'].getValue()
            last = write['last'].getValue()
            review_node['use_limit'].setValue(True)

        ranges = nuke.FrameRanges('{0}-{1}'.format(first, last))
        nuke.render(review_node, ranges)

        instance.data['ftrack_web_reviewable_components'] = [{
            'name': 'web-reviewable',
            'path': temp_review_mov
        }]

        self.log.debug(
            'Extracted Reviewable component from {0!r}'.format(
                instance.name
            )
        )


class PostReviewableComponentExtract(pyblish.api.InstancePlugin):
    '''Remove nodes used to generate a reviewable component.'''

    order = pyblish.api.ExtractorOrder + 0.1

    families = constant.REVIEW_FAMILY_PYBLISH
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''
        self.log.debug(
            'Post extracting reviewable component {0!r}'.format(
                instance.name
            )
        )

        import nuke
        node_name = instance.data['ftrack_tmp_review_node']
        nuke.delete(nuke.toNode(node_name))


pyblish.api.register_plugin(ReviewableComponentExtract)
pyblish.api.register_plugin(PostReviewableComponentExtract)
