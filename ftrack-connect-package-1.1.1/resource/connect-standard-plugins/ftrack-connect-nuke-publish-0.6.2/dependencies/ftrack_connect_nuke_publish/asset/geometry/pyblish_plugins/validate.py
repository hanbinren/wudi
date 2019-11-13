# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class GeoPublishValidator(pyblish.api.InstancePlugin):
    '''Validate Geo publish.'''

    order = pyblish.api.ValidatorOrder

    families = ['ftrack', 'geo']
    match = pyblish.api.Subset

    label = 'Validate Alembic component.'
    optional = False

    def process(self, instance):
        '''Validate *instance*.'''
        import nuke
        import os

        node = nuke.toNode(instance.name)
        file_path = unicode(node['file'].value())

        self.log.debug(
            'Validating {0} from {1}'.format(file_path, instance.name)
        )

        filename, extension = os.path.splitext(file_path)

        # Extension is not '.abc' does not work.
        #: TODO: Investigate this further.
        if extension.lower() != '.abc':
            error_message = (
                'Geometry file for node {0} is not an alembic file'.format(
                    instance.name
                )
            )
            assert False, error_message

        if not os.path.exists(file_path):
            error_message = 'Alembic file for node {0} does not exist.'.format(
                instance.name
            )
            assert False, error_message
