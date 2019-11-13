# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import uuid

import MaxPlus

import ftrack_api

from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance

from .assethelper import *
from .assetimportmodes import *
from .utils import *
from .xrefs import deleteSceneXRef


class Connector(maincon.Connector):
    def __init__(self):
        # We need to create our own session and call manually event_hub.connect()
        # on the main thread to avoid Max 2016 hanging.
        session = ftrack_api.Session(auto_connect_event_hub=False)
        session.event_hub.connect()
        super(Connector, self).__init__(session=session)

    @staticmethod
    def getAssets():
        '''Return the available assets in scene, return the *componentId(s)*'''

        componentIds = []

        for node in getAllFtrackAssetHelperNodes(recurse=True):
            obj = node.Object
            componentId = obj.ParameterBlock.assetComponentId.Value
            if componentId:
                componentIds.append((componentId, node.Name))

        return componentIds

    @staticmethod
    def getFileName():
        '''Return the *current scene* name'''
        return evalMAXScript('maxFilePath + maxFileName').Get()

    @staticmethod
    def getMainWindow():
        '''Return the *main window* instance'''
        return None

    @staticmethod
    def wrapinstance(ptr, base=None):
        '''
        Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)

        :param ptr: Pointer to QObject in memory
        :type ptr: long or Swig instance
        :param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
        :type base: QtWidgets.QWidget
        :return: QWidget or subclass instance
        :rtype: QtWidgets.QWidget
        '''
        return ptr

    @staticmethod
    def importAsset(iAObj):
        '''Import the asset provided by *iAObj*'''
        iAObj.assetName = '_'.join(
            [iAObj.assetType.upper(), iAObj.assetName, 'AST']
        )
        # Maya converts - to _ so let's do that as well
        iAObj.assetName = iAObj.assetName.replace('-', '_')

        # Check if this AssetName already exists in scene
        iAObj.assetName = Connector.getUniqueSceneName(iAObj.assetName)

        assetHandler = FTAssetHandlerInstance.instance()
        importAsset = assetHandler.getAssetClass(iAObj.assetType)
        if importAsset:
            result = importAsset.importAsset(iAObj)
            return result
        else:
            return 'assetType not supported'

    @staticmethod
    def selectObject(applicationObject=''):
        '''Select the *applicationObject*'''
        MaxPlus.SelectionManager.ClearNodeSelection()
        ftrackHelperNode = MaxPlus.INode.GetINodeByName(applicationObject)
        MaxPlus.SelectionManager.SelectNode(ftrackHelperNode, False)
        addAllChildrenToSelection(ftrackHelperNode)

    @staticmethod
    def selectObjects(selection):
        '''Select the given *selection*'''
        MaxPlus.SelectionManager.ClearNodeSelection()
        for nodeName in selection:
            node = MaxPlus.INode.GetINodeByName(nodeName)
            MaxPlus.SelectionManager.SelectNode(node, False)

    @staticmethod
    def removeObject(applicationObject=''):
        '''Remove the *applicationObject* from the scene'''

        ftrackHelperNode = MaxPlus.INode.GetINodeByName(applicationObject)

        importMode = getAssetImportMode(ftrackHelperNode)
        if importMode == SCENE_XREF_IMPORT_MODE:
            deleteSceneXRef(ftrackHelperNode)

        deleteAllChildren(ftrackHelperNode)
        ftrackHelperNode.Delete()

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        '''Change version of *iAObj* for the given *applicationObject*'''
        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(iAObj, applicationObject)
            return result
        else:
            print 'assetType not supported'
            return False

    @staticmethod
    def getSelectedObjects():
        '''Return the selected node names.'''
        selectedNodes = []
        for node in MaxPlus.SelectionManager.Nodes:
            selectedNodes.append(node.Name)

        return selectedNodes

    @staticmethod
    def getSelectedAssets():
        '''Return the selected assets'''

        selectedNodes = []
        root = MaxPlus.Core.GetRootNode()
        for node in MaxPlus.SelectionManager.Nodes:
            while node.Parent != root:
                if isFtrackAssetHelper(node.Parent):
                    selectedNodes.append(node.Name)
                    break

                node = node.Parent

        return selectedNodes

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        '''Set the node color'''

    @staticmethod
    def publishAsset(iAObj=None):
        '''Publish the asset provided by *iAObj*'''
        assetHandler = FTAssetHandlerInstance.instance()
        pubAsset = assetHandler.getAssetClass(iAObj.assetType)
        if pubAsset:
            publishedComponents, message = pubAsset.publishAsset(iAObj)
            return publishedComponents, message
        else:
            return [], 'assetType not supported'

    @staticmethod
    def getConnectorName():
        '''Return the connector name'''
        return 'max'

    @staticmethod
    def getUniqueSceneName(assetName):
        '''Return a unique scene name for the given *assetName*'''
        return getUniqueNodeName(assetName)

    @staticmethod
    def takeScreenshot():
        '''Take a screenshot and save it in the temp folder'''
        view = MaxPlus.ViewportManager.GetActiveViewport()
        bm = MaxPlus.Factory.CreateBitmap()
        storage = MaxPlus.Factory.CreateStorage(7)
        info = storage.GetBitmapInfo()
        bm.SetStorage(storage)
        bm.DeleteStorage()
        res = view.GetDIB(info, bm)
        if not res:
            return

        filename = '{0}.jpg'.format(uuid.uuid4().hex)
        outpath = os.path.join(MaxPlus.PathManager.GetTempDir(), filename)
        info.SetName(outpath)
        bm.OpenOutput(info)
        bm.Write(info)
        bm.Close(info)
        return outpath

    @staticmethod
    def batch():
        '''Return whether the application is in *batch mode* or not'''
        # It seems like Max does not have a batch mode.
        return False

    @classmethod
    def registerAssets(cls):
        '''Register all the available assets'''
        import maxassets
        maxassets.registerAssetTypes()
        super(Connector, cls).registerAssets()

    # Make certain scene validations before actualy publishing
    @classmethod
    def prePublish(cls, iAObj):
        '''Pre Publish check for given *iAObj*'''
        result, message = super(Connector, cls).prePublish(iAObj)
        if not result:
            return result, message

        return True, ''
