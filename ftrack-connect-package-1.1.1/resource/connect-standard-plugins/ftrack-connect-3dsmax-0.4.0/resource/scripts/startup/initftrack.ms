-- Copyright (c) 2016 ftrack

-- Load the FtrackAssetHelperPlugin
include "ftrackassethelper.ms"

-- Return true if this version of 3ds Max is supported.
fn ftrackCheckMaxVersion = (
    local versionString = getFileVersion "$max/3dsmax.exe"
    local versionTokens = (filterString versionString ",")
    local majorVersion = versionTokens[1] as integer
    local servicePack = versionTokens[2] as integer

    if majorVersion < 18
        -- We don't support 2015 and earlier.
        then return false
    else if majorVersion == 18 and servicePack < 7
        -- We don't support 2016 versions before SP3.
        -- For some strange reason, SP3 is 7 in the version string.
        then return false

    return true
)

-- Initialize ftrack if the 3ds Max version is supported.
if ftrackCheckMaxVersion()
    then python.ExecuteFile("initftrack.py")
else
    messageBox "This version of 3ds Max is not supported.\nPlease use 3ds Max 2016 SP3 or newer." title: "Ftrack connect 3ds Max"
