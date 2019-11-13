# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import MaxPlus

from .pluginids import FTRACK_ASSET_HELPER_CLASS_ID
from .utils import evalMAXScript

import logging
logger = logging.getLogger(__name__)


def isFtrackAssetHelper(node):
    '''Return True if the node is a Ftrack asset helper node.'''
    if node.Object.ClassID == FTRACK_ASSET_HELPER_CLASS_ID:
        return True

    return False

def _forEachFtrackAssetHelper(node, fun, recurse=False):
    if isFtrackAssetHelper(node):
        fun(node)

    if recurse:
        for c in node.Children:
            _forEachFtrackAssetHelper(c, fun, recurse)

def forEachFtrackAssetHelper(fun, recurse=False):
    '''Calls a function for each Ftrack asset helper node in the scene.'''
    root = MaxPlus.Core.GetRootNode()
    for c in root.Children:
        _forEachFtrackAssetHelper(c, fun, recurse)

def getAllFtrackAssetHelperNodes(recurse=False):
    '''Return a list of Ftrack asset helper nodes in the scene.'''
    ftrackHelperNodes = []
    forEachFtrackAssetHelper(lambda helper: ftrackHelperNodes.append(helper), recurse)
    return ftrackHelperNodes

def createFtrackAssetHelper(assetName, assetId, assetVersion, assetPath,
    assetTake, assetComponentId, assetImportMode=None):
    '''Create a Ftrack asset helper and initialize its parameters.'''

    obj = MaxPlus.Factory.CreateHelperObject(FTRACK_ASSET_HELPER_CLASS_ID)

    if assetTake == '3dsmax':
        obj.ParameterBlock.assetImportMode.Value = assetImportMode

    node = MaxPlus.Factory.CreateNode(obj)
    node.Name = assetName

    # Try to freeze the helper object and lock the transform.
    try:
        cmd = 'freeze ${0} ; setTransformLockFlags ${0} #all'.format(assetName)
        evalMAXScript(cmd)
    except:
        logger.debug("Could not freeze object {0}".format(assetName))

    updateFtrackAssetHelper(node, assetId, assetVersion, assetPath, assetTake,
        assetComponentId)

    return node

def updateFtrackAssetHelper(ftrackHelperNode, assetId, assetVersion, assetPath,
    assetTake, assetComponentId):
    '''Update the parameters of a Ftrack asset helper.'''

    try:
        cmd = 'unfreeze ${0}'.format(ftrackHelperNode.Name)
        evalMAXScript(cmd)
    except:
        logger.debug("Could not unfreeze object {0}".format(ftrackHelperNode.Name))

    obj = ftrackHelperNode.Object
    obj.ParameterBlock.assetId.Value = assetId
    obj.ParameterBlock.assetVersion.Value = assetVersion
    obj.ParameterBlock.assetPath.Value = assetPath
    obj.ParameterBlock.assetTake.Value = assetTake
    obj.ParameterBlock.assetComponentId.Value = assetComponentId

    try:
        cmd = 'freeze ${0}'.format(ftrackHelperNode.Name)
        evalMAXScript(cmd)
    except:
        logger.debug("Could not freeze object {0}".format(ftrackHelperNode.Name))

def getAssetImportMode(ftrackHelperNode):
    '''Return the import mode used to import an asset.'''
    obj = ftrackHelperNode.Object
    return obj.ParameterBlock.assetImportMode.Value

def getAssetFilePath(ftrackHelperNode):
    '''Return the asset file path.'''
    obj = ftrackHelperNode.Object
    return obj.ParameterBlock.assetPath.Value

def getFtrackComponentIds():
    '''Return a list of all the components ids of all the assets
    imported in the scene.'''
    componentIds = []

    for node in getAllFtrackAssetHelperNodes(recurse=True):
        componentId = node.Object.ParameterBlock.assetComponentId.Value
        if componentId:
            componentIds.append(componentId)

    return componentIds

def getFtrackAssetVersionsInfo():
    '''Return a list of all the version ids, version numbers, takes and
    helper node names of all the assets imported in the scene.'''

    versions = []
    for node in getAllFtrackAssetHelperNodes(recurse=True):
        versionId = node.Object.ParameterBlock.assetId.Value
        version = node.Object.ParameterBlock.assetVersion.Value
        take = node.Object.ParameterBlock.assetTake.Value
        if versionId:
            versions.append((versionId, version, take, node.Name))

    return versions

def getAlembicImportArgs(ftrackHelperNode):
    '''Return a ; separated string of args used to import the Alembic asset.'''
    obj = ftrackHelperNode.Object
    return obj.ParameterBlock.alembicImportArgs.Value

def setAlembicImportArgs(ftrackHelperNode, options):
    '''Store the args used to import an Alembic asset into the helper node.'''
    obj = ftrackHelperNode.Object
    obj.ParameterBlock.alembicImportArgs.Value = options
