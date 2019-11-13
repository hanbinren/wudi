# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def register():
    '''Register shared pyblish plugins.'''
    # Register shared pyblish plugins.
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.collect_nuke_version
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.collect_nuke_script
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.collect_write_nodes_for_review
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.extract_nuke_script
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.extract_reviewable_component
    import ftrack_connect_nuke_publish.shared_pyblish_plugins.validate_reviewable_component
