# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class RenderPublishValidator(pyblish.api.InstancePlugin):
    '''Validate that write node output exists.'''

    order = pyblish.api.ValidatorOrder

    families = ['ftrack', 'write']
    match = pyblish.api.Subset

    label = 'Validate that write node output exists.'

    optional = False

    def check_frames(self, input_frames, write_node, instance_name):
        '''Check that all the frames expressed in *input_frames* exists.

        It'll use *write_node* and *instance_name* to fetch data and report.

        '''

        import nuke
        import os
        import clique
        import glob

        self.log.info(
            'Validating {0} from {1}.'.format(input_frames, instance_name)
        )

        single_file = os.path.isfile(input_frames)
        if not single_file:
            first = int(nuke.root().knob('first_frame').value())
            last = int(nuke.root().knob('last_frame').value())

            # Then in case check if the limit are set.
            if write_node['use_limit'].value():
                first = int(write_node['first'].value())
                last = int(write_node['last'].value())

            # Always check how many frames are actually available.
            frames = input_frames

            fragments = frames.split('.')

            assert len(fragments) >= 3, (
                u'Could not validate that {0} exists.'.format(frames)
            )

            extension = fragments.pop()
            # Pop padding, not used.
            fragments.pop()
            prefix = '.'.join(fragments)

            root = os.path.dirname(prefix)
            file_name = os.path.basename(prefix)
            frame_query = '{0}/{1}*.{2}'.format(
                root, file_name, extension
            )
            self.log.debug('Looking for {0}'.format(frame_query))

            files = glob.glob(frame_query)
            collections, remainder = clique.assemble(files)

            assert collections, u'No frames found: {0}.'.format(frames)

            assert len(collections) == 1, (
                u'Multiple frame ranges not expected: {0}.'
            ).format(frames)

            collection = collections[0]

            for index in list(collection.indexes):
                in_range = first <= index <= last
                if not in_range:
                    # Discard index since it will not be published.
                    collection.indexes.discard(index)

            assert collection.is_contiguous(), (
                u'Missing images ({0}) in sequence: {1}.'
            ).format(collection.format('{holes}'), frames)

        else:
            assert os.path.exists(
                input_frames
            ), u'File {0} does not exist!'.format(input_frames)

    def process(self, instance):
        '''Validate *instance*.'''
        import nuke

        write_node = nuke.toNode(instance.name)
        file_comp = str(write_node['file'].value())
        proxy_comp = str(write_node['proxy'].value())
        for comp_data in [file_comp, proxy_comp]:
            if comp_data:
                self.check_frames(comp_data, write_node, instance.name)
