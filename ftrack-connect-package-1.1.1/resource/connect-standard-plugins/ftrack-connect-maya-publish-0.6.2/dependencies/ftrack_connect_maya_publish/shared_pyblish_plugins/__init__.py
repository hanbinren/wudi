# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def register():
    '''Register shared pyblish plugins.'''
    # Register shared pyblish plugins.
    import ftrack_connect_maya_publish.shared_pyblish_plugins.collect
    import ftrack_connect_maya_publish.shared_pyblish_plugins.collect_playblast_camera
    import ftrack_connect_maya_publish.shared_pyblish_plugins.collect_mayaversion
    import ftrack_connect_maya_publish.shared_pyblish_plugins.extract_alembic
    import ftrack_connect_maya_publish.shared_pyblish_plugins.extract_mayabinary
    import ftrack_connect_maya_publish.shared_pyblish_plugins.extract_reviewable_component
