# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api
import maya.cmds as mc


def bake(camera):
    '''Return baked *camera*.'''
    temporary_cam_components = mc.duplicate(camera, un=1, rc=1)

    if mc.nodeType(temporary_cam_components[0]) == 'transform':
        temporary_camera = temporary_cam_components[0]
    else:
        temporary_camera = mc.ls(temporary_cam_components, type='transform')[0]

    pConstraint = mc.parentConstraint(camera, temporary_camera)

    try:
        mc.parent(temporary_camera, world=True)
    except RuntimeError:
        # Camera is already in world space.
        pass

    mc.bakeResults(
        temporary_camera,
        simulation=True,
        t=(
            mc.playbackOptions(q=True, minTime=True),
            mc.playbackOptions(q=True, maxTime=True)
        ),
        sb=1,
        at=['tx', 'ty', 'tz', 'rx', 'ry', 'rz'],
        hi='below')

    mc.delete(pConstraint)

    camera = temporary_camera
    return camera


def cleanup_bake(camera):
    '''Clean up baked *camera*.'''
    mc.delete(camera)


def lock_camera(camera):
    '''Return locked *camera*.'''
    channels = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
    camera_values = {}

    for channel in channels:
        channel_name = '{0}.{1}'.format(camera, channel)
        channel_value = mc.getAttr(channel_name, l=True)
        camera_values.setdefault(channel, channel_value)
        mc.setAttr(channel_name, l=True)

    return camera_values


def unlock_camera(camera, original_values):
    '''Unlock *camera* with *original_values*.'''
    for channel, value in original_values.items():
        channel_name = '{0}.{1}'.format(camera, channel)
        mc.setAttr(channel_name, l=value)


class PreCameraExtract(pyblish.api.InstancePlugin):
    '''Prepare camera for extraction.'''

    order = pyblish.api.ExtractorOrder - 0.1

    families = ['ftrack', 'camera']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''
        camera_options = instance.context.data['options'].get(
            'camera_options', {}
        )

        bake_camera_option = camera_options.get('bake', False)
        lock_camera_option = camera_options.get('lock', False)

        camera = str(instance)
        locked_attrs = {}

        if bake_camera_option:
            camera = bake(camera)

        if lock_camera_option:
            locked_attrs = lock_camera(camera)

        mc.select(str(camera), replace=True)
        instance.data['camera'] = camera
        instance.data['locked_attrs'] = locked_attrs

        self.log.debug(
            'Completed pre camera extract on {0!r} with {1!r}.'.format(
                instance.name, camera_options
            )
        )


class PostCameraExtract(pyblish.api.InstancePlugin):
    '''Restore camera after ectraction.'''

    order = pyblish.api.ExtractorOrder + 0.1

    families = ['ftrack', 'camera']
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *instance*.'''
        camera_options = instance.context.data['options'].get(
            'camera_options', {}
        )

        bake_camera_option = camera_options.get('bake', False)
        lock_camera_option = camera_options.get('lock', False)

        camera = instance.data['camera']
        locked_attrs = instance.data['locked_attrs']

        if lock_camera_option:
            locked_attrs = unlock_camera(camera, locked_attrs)

        if bake_camera_option:
            camera = cleanup_bake(camera)

        self.log.debug(
            'Completed post camera extract on {0!r} with {1!r}.'.format(
                instance.name, camera_options
            )
        )
