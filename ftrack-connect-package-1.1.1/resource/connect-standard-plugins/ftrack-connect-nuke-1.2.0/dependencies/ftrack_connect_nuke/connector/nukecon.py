# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import sys
import os
import tempfile
import urlparse
import traceback

from nukescripts import panels
import nukescripts
import nuke


from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance
from ftrack_connect.connector import HelpFunctions


def register_scheme(scheme):
    for method in filter(lambda s: s.startswith('uses_'), dir(urlparse)):
        getattr(urlparse, method).append(scheme)

register_scheme('ftrack')


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def getAssets():
        allReadNodes = nuke.allNodes('Read')
        allCamNodess = nuke.allNodes('Camera2')
        geosNodes = nuke.allNodes('ReadGeo2')

        allGizmos =  [n for n in nuke.allNodes() if type(n) ==  nuke.Gizmo]
        allInterestingNodes = allReadNodes + allCamNodess + allGizmos + geosNodes

        componentIds = []

        for readNode in allInterestingNodes:
            try:
                valueftrackId = readNode.knob('componentId').value()
                if valueftrackId != '':
                    if 'ftrack://' in valueftrackId:
                        url = urlparse.urlparse(valueftrackId)
                        valueftrackId = url.netloc
                    componentIds.append((valueftrackId, readNode.name()))
            except:
                pass

        return componentIds

    @staticmethod
    def getFileName():
        return nuke.root().name()

    @staticmethod
    def getMainWindow():
        return None

    @staticmethod
    def importAsset(iAObj):
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
    def selectObject(applicationObject='', clearSelection=True):
        if clearSelection:
            nukescripts.clear_selection_recursive()
        n = nuke.toNode(HelpFunctions.safeString(applicationObject))
        n.knob('selected').setValue(True)

    @staticmethod
    def selectObjects(selection):
        nukescripts.clear_selection_recursive()
        for obj in selection:
            Connector.selectObject(obj, clearSelection=False)

    @staticmethod
    def removeObject(applicationObject=''):
        deleteMeNode = nuke.toNode(HelpFunctions.safeString(applicationObject))
        nuke.delete(deleteMeNode)

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(
                iAObj, applicationObject
            )
            return result
        else:
            print 'assetType not supported'
            return False

    @staticmethod
    def getSelectedObjects():
        selection = nuke.selectedNodes()
        selectedObjects = []
        for node in selection:
            selectedObjects.append(node.name())
        return selectedObjects

    @staticmethod
    def getSelectedAssets():
        selection = nuke.selectedNodes()
        selectedObjects = []
        for node in selection:
            try:
                node.knob('componentId').value()
                selectedObjects.append(node.name())
            except:
                pass
        return selectedObjects

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        latestColor = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        oldColor = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        n = nuke.toNode(HelpFunctions.safeString(applicationObject))
        if latest:
            n.knob("note_font_color").setValue(latestColor)
        else:
            n.knob("note_font_color").setValue(oldColor)

    @staticmethod
    def publishAsset(iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        pubAsset = assetHandler.getAssetClass(iAObj.assetType)
        if pubAsset:
            publishedComponents, message = pubAsset.publishAsset(iAObj)
            #result = pubAsset.changeVersion(iAObj, applicationObject)
            return publishedComponents, message
        else:
            return [], 'assetType not supported'

    @staticmethod
    def getConnectorName():
        return 'nuke'

    @staticmethod
    def getUniqueSceneName(assetName):
        assetName = assetName
        res = nuke.toNode(HelpFunctions.safeString(assetName))
        if res:
            i = 0
            while res:
                uniqueAssetName = assetName + str(i)
                res = nuke.toNode(HelpFunctions.safeString(uniqueAssetName))
                i = i + 1
            return uniqueAssetName
        else:
            return assetName

    @classmethod
    def registerAssets(cls):
        import nukeassets
        nukeassets.registerAssetTypes()
        super(Connector, cls).registerAssets()

    @staticmethod
    def executeInThread(function, arg):
        nuke.executeInMainThreadWithResult(function, args=arg)

    # Create a thumbnail from the output of the nodeobject that is passed
    @staticmethod
    def createThumbNail(nodeObject):
        try:
            #test creating thumbnail
            reformatNode = nuke.nodes.Reformat()
            reformatNode['type'].setValue("to box")
            reformatNode['box_width'].setValue(200.0)

            reformatNode.setInput(0, nodeObject)

            w2 = nuke.nodes.Write()
            w2.setInput(0, reformatNode)
            thumbNailFilename = 'thumbnail_' + HelpFunctions.getUniqueNumber() + '.png'
            thumbnailDestination = os.path.join(tempfile.gettempdir(), thumbNailFilename)
            w2['file'].setValue(Connector.windowsFixPath(thumbnailDestination))
            w2['file_type'].setValue('png')

            curFrame = int(nuke.knob("frame"))
            nuke.execute(w2, curFrame, curFrame)

            nuke.delete(reformatNode)
            nuke.delete(w2)

            return thumbnailDestination
        except:
            import traceback
            traceback.print_exc(file=sys.stdout)
            return None

    @staticmethod
    def windowsFixPath(path):
        path = path.replace('\\', '/')
        path = path.replace('\\\\', '/')
        return path
