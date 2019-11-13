# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class ExtractWriteGeoNodes(pyblish.api.InstancePlugin):
    '''Extract nuke geo from write geo nodes.'''

    order = pyblish.api.ExtractorOrder

    families = ['ftrack', 'geo']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance* and extract geo.'''
        import nuke

        self.log.debug(
            'Started extracting write geo node {0!r}.'.format(
                instance.name
            )
        )

        write_geo_node = nuke.toNode(instance.name)
        new_component = {
            'path': unicode(write_geo_node['file'].value()),
            'name': 'alembic',
            'node_name': unicode(write_geo_node['name'].value()).strip()
        }

        instance.data['ftrack_components'].append(new_component)

        self.log.debug(
            'Extracted {0!r} from {1!r}.'.format(
                new_component, instance.name
            )
        )
