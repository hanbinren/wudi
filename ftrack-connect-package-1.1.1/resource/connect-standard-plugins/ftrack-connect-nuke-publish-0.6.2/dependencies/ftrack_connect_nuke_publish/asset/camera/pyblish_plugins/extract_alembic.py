# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api
import tempfile


class PreCameraAlembicExtract(pyblish.api.InstancePlugin):
    '''Create temporary Scene and WriteGeo nodes and initialize them.'''

    order = pyblish.api.ExtractorOrder - 0.1

    families = ['ftrack', 'camera']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''
        self.log.debug(
            'Pre extracting nuke camera {0!r}'.format(
                instance.name
            )
        )

        import nuke
        camera_node = nuke.toNode(instance.name)

        frame_range = instance.context.data['options'].get(
            'frame_range', {}
        )

        first = frame_range['start_frame']
        last = frame_range['end_frame']

        scn = nuke.nodes.Scene()
        scn.setInput(0, camera_node)
        instance.data['nuke_scene'] = scn

        write = nuke.nodes.WriteGeo()
        write.setInput(0, scn)
        write['file_type'].setValue('abc')
        write['writeCameras'].setValue(True)
        write['writeGeometries'].setValue(False)
        write['writeAxes'].setValue(False)
        write['writePointClouds'].setValue(False)
        write['storageFormat'].setValue('Ogawa')
        write['use_limit'].setValue(True)
        write['first'].setValue(float(first))
        write['last'].setValue(float(last))

        instance.data['nuke_write'] = write


class ExtractCameraAlembic(pyblish.api.InstancePlugin):
    '''Prepare component to be published.'''

    order = pyblish.api.ExtractorOrder

    families = ['ftrack', 'camera']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''
        import nuke
        self.log.debug(
            'Started extracting camera {0!r} with options '
            '{1!r}.'.format(
                instance.name, instance.data['options']
            )
        )

        write_node = instance.data['nuke_write']
        temporary_path = tempfile.mkstemp(suffix='.abc')[-1]
        write_node['file'].setValue(temporary_path)

        nuke.execute(write_node.name())

        new_component = {
            'name': '{0}.alembic'.format(instance.name),
            'path': temporary_path,
        }

        instance.data['ftrack_components'].append(new_component)
        self.log.debug(
            'Extracted {0!r} from {1!r}'.format(new_component, instance.name)
        )


class PostCameraAlembicExtract(pyblish.api.InstancePlugin):
    '''Remove temporary Scene and WriteGeo nodes.'''

    order = pyblish.api.ExtractorOrder + 0.1

    families = ['ftrack', 'camera']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''

        self.log.debug(
            'Post extracting nuke camera {0!r}'.format(
                instance.name
            )
        )

        import nuke
        nuke.delete(instance.data['nuke_write'])
        nuke.delete(instance.data['nuke_scene'])
