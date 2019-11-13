# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api
import clique
import os
import glob


class ExtractWriteNodes(pyblish.api.InstancePlugin):
    '''Extract nuke render from write nodes.'''

    order = pyblish.api.ExtractorOrder

    families = ['ftrack', 'write']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance* and extract render.'''

        self.log.debug(
            'Started extracting write node {0!r}'.format(
                instance.name
            )
        )

        import nuke

        write_node = nuke.toNode(instance.name)
        file_comp = str(write_node['file'].value())
        proxy_comp = str(write_node['proxy'].value())
        node_name = str(write_node['name'].value()).strip()

        component_name = instance.name

        self.log.debug('Using component name: {0!r}'.format(component_name))

        new_component = None

        single_file = os.path.isfile(file_comp)
        if single_file:
            # File exists.
            new_component = {
                'path': file_comp,
                'name': component_name,
                'node_name': node_name
            }
            instance.data['ftrack_components'].append(new_component)

            if proxy_comp != '':
                new_component = {
                    'path': new_component,
                    'name': component_name + '_proxy',
                    'node_name': node_name
                }
                instance.data['ftrack_components'].append(new_component)
        else:
            # File does not exist, assume that it is a file sequence.

            # Use the timeline to define the amount of frames.
            first = str(int(nuke.root().knob('first_frame').value()))
            last = str(int(nuke.root().knob('last_frame').value()))

            # Then in case check if the limit are set.
            if write_node['use_limit'].value():
                first = str(write_node['first'].value())
                last = str(write_node['last'].value())

            # Always check how many frames are actually available.
            frames = write_node['file'].value()

            fragments = frames.split('.')
            extension = fragments.pop()
            # Pop padding.
            fragments.pop()
            prefix = '.'.join(fragments)

            root = os.path.dirname(prefix)
            files = glob.glob('{0}/*.{1}'.format(root, extension))
            collections = clique.assemble(files)

            for collection in collections[0]:
                if prefix in collection.head:
                    indexes = list(collection.indexes)
                    first = str(indexes[0])
                    last = str(indexes[-1])
                    break

            if first != last:
                sequence_path = u'{0} [{1}-{2}]'.format(
                    file_comp, first, last
                )
            else:
                sequence_path = unicode(file_comp % first)

            new_component = {
                'path': sequence_path,
                'name': component_name,
                'first': first,
                'last': last,
                'node_name': node_name
            }

            instance.data['ftrack_components'].append(new_component)
            self.log.debug(
                'Extracted {0!r} from {1!r}'.format(
                    new_component, instance.name
                )
            )

            if proxy_comp != '':

                if first != last:
                    sequence_path = u'{0} [{1}-{2}]'.format(
                        proxy_comp, first, last
                    )
                else:
                    sequence_path = unicode(proxy_comp % first)

                new_component = {
                    'path': new_component,
                    'name': component_name + '_proxy',
                    'first': first,
                    'last': last,
                    'node_name': node_name
                }

                instance.data['ftrack_components'].append(new_component)

        self.log.debug(
            'Extracted {0!r} from {1!r}'.format(
                new_component, instance.name
            )
        )
