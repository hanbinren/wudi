# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import nuke
import ftrack_connect_pipeline.asset


def filter_instances(pyblish_context):
    '''Return camera instances from *pyblish_context*.'''
    match = set(['camera', 'ftrack'])
    return filter(
        lambda instance: match.issubset(instance.data['families']),
        pyblish_context
    )


class PublishCamera(ftrack_connect_pipeline.asset.PyblishAsset):
    '''Handle publish of nuke cameras.'''

    def get_options(self):
        '''Return global options.'''
        from ftrack_connect_pipeline.ui.widget.field import start_end_frame
        first = int(nuke.root().knob('first_frame').value())
        last = int(nuke.root().knob('last_frame').value())

        frame_range = start_end_frame.StartEndFrameField(first, last)

        options = [
            {
                'type': 'qt_widget',
                'name': 'frame_range',
                'widget': frame_range,
                'value': {
                    'start_frame': first,
                    'end_frame': last
                }
            }
        ]

        default_options = super(PublishCamera, self).get_options()

        return default_options + options

    def get_publish_items(self):
        '''Return list of items that can be published.'''
        options = []
        for instance in filter_instances(self.pyblish_context):
            options.append(
                {
                    'label': instance.name,
                    'name': instance.id,
                    'value': instance.data.get('publish', False)
                }
            )

        return options

    def get_scene_selection(self):
        '''Return a list of names for scene selection.'''
        selection = []
        for node in nuke.selectedNodes():
            selection.append(node.name())

        # Return list of instance ids for selected items in scene that match the
        # family.
        return [
            instance.id for instance in filter_instances(self.pyblish_context)
            if instance.name in selection
        ]

        return selection
