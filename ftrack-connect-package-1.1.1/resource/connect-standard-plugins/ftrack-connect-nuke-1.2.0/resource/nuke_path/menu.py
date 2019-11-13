# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

# Import to bootstrap foundry api.
import ftrack_connect_nuke
import ftrack_connect

try:
    # part of nuke
    import foundry.assetmgr
except:
    # included in ftrack-connect-foundry
    import assetmgr_nuke

import nuke
