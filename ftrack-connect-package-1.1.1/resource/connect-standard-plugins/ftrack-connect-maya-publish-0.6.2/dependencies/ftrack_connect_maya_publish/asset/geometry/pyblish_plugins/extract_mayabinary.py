# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class ExtractGeometryMayaBinary(pyblish.api.InstancePlugin):
    '''Extract geometry as maya binary.'''

    order = pyblish.api.ExtractorOrder

    families = ['ftrack', 'geometry']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance* and extract media.'''
        import tempfile
        import maya.cmds as mc

        # Select the given geometries.
        mc.select(str(instance), replace=True)

        context_options = instance.context.data['options'].get(
            'maya_binary', {}
        )
        self.log.debug(
            'Started extracting geometry {0!r} with options '
            '{1!r}.'.format(
                instance.name, context_options
            )
        )

        # Extract options and provide defaults.
        keep_reference = context_options.get('reference', False)
        keep_history = context_options.get('history', False)
        keep_channels = context_options.get('channels', False)
        keep_constraints = context_options.get('constraint', False)
        keep_expressions = context_options.get('expression', False)
        keep_shaders = context_options.get('shaders', True)
        export_selected = context_options.get('export_selected', True)

        # Generate temp file.
        temporary_path = tempfile.mkstemp(suffix='.mb')[-1]

        # Save maya file.
        mc.file(
            temporary_path,
            op='v=0',
            typ='mayaBinary',
            preserveReferences=keep_reference,
            constructionHistory=keep_history,
            channels=keep_channels,
            constraints=keep_constraints,
            expressions=keep_expressions,
            shader=keep_shaders,
            exportSelected=export_selected,
            exportAll=not export_selected,
            force=True
        )
        name = instance.name
        if name.startswith('|'):
            name = name[1:]

        new_component = {
            'name': '{0}.mayabinary'.format(name),
            'path': temporary_path,
        }

        instance.data['ftrack_components'].append(new_component)
        self.log.debug(
            'Extracted {0!r} from {1!r}'.format(new_component, instance.name)
        )
