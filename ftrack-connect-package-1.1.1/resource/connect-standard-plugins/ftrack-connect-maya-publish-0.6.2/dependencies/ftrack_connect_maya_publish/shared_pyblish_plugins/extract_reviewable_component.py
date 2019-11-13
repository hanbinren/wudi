# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api
from ftrack_connect_pipeline import constant


class ExtractReviewableComponent(pyblish.api.InstancePlugin):
    '''Generate a reviewable component.'''

    order = pyblish.api.ExtractorOrder

    families = constant.REVIEW_FAMILY_PYBLISH
    match = pyblish.api.Subset

    def do_playblast(self, camera_name):
        '''Run playblast command and return result path.'''
        import tempfile
        import maya.cmds as cmds

        panel = cmds.getPanel(wf=True)
        previous_camera = cmds.modelPanel(panel, q=True, camera=True)

        cmds.lookThru(camera_name)

        res_w = int(cmds.getAttr('defaultResolution.width'))
        res_h = int(cmds.getAttr('defaultResolution.height'))

        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        prev_selection = cmds.ls(sl=True)
        cmds.select(cl=True)

        filename = tempfile.NamedTemporaryFile(
            suffix='.mov'
        ).name

        cmds.playblast(
            format='qt',
            sequenceTime=0,
            clearCache=1,
            viewer=0,
            offScreen=True,
            showOrnaments=0,
            frame=range(int(start_frame), int(end_frame + 1)),
            filename=filename,
            fp=4,
            percent=100,
            compression="png",
            quality=70,
            w=res_w,
            h=res_h
        )

        if len(prev_selection):
            cmds.select(prev_selection)

        cmds.lookThru(previous_camera)

        return filename

    def process(self, instance):
        '''Process *instance* and add review component to context.'''
        self.log.debug('Started extracting reviewable component.')
        playblast_result = self.do_playblast(instance.name)
        instance.data['ftrack_web_reviewable_components'] = [{
            'name': 'web-reviewable',
            'path': playblast_result
        }]

        self.log.debug(
            'Collected reviewable component :{0!r} from {1!r}.'.format(
                playblast_result, instance
            )
        )


pyblish.api.register_plugin(ExtractReviewableComponent)
