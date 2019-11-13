# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import uuid

import maya.cmds as mc
import maya.OpenMayaUI as mui
import maya.mel as mm

from ftrack_connect.connector import base as maincon
from ftrack_connect.connector import FTAssetHandlerInstance


class DockedWidget(object):
    def __init__(self, widget):
        super(DockedWidget, self).__init__()
        self.panelWidth = 650
        self.qtObject = widget
        self.type = 'panel'
        self.dockAllowedAreas = ['all']
        self.gotRefresh = None

    def show(self):
        '''Show the current widget, return the widget itself'''
        hasName = hasattr(self.qtObject, 'dockControlName')
        if hasName:
            name = self.qtObject.dockControlName
            mc.dockControl(name, e=True, r=True)
            if not mc.dockControl(
                name, q=True, io=True
            ):
                returnObj = self.qtObject
            else:
                self.createDockLayout()
                returnObj = self.qtObject

            if self.gotRefresh:
                returnObj.refresh()
            return returnObj

        self.qtObject.show()
        self.createDockLayout()
        return self.qtObject

    def getWindow(self):
        '''Return the widget'''
        return self.qtObject

    def createDockLayout(self):
        '''Create a layout for Docked widgets'''
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = mc.paneLayout(parent=gMainWindow, width=200)
        dockControl = mc.dockControl(
            l=self.qtObject.windowTitle().replace('ftrack', ''),
            allowedArea="all",
            area="right",
            content=columnLay,
            width=self.panelWidth
        )
        mc.control(str(self.qtObject.objectName()), e=True, p=columnLay)
        self.qtObject.dockControlName = dockControl
        return


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def setTimeLine():
        '''Set time line to FS , FE environment values'''
        import ftrack
        startFrame = float(os.getenv('FS', 1001))
        endFrame = float(os.getenv('FE', 1101))
        shotId = os.getenv('FTRACK_SHOTID')
        try:
            shot = ftrack.Shot(id=shotId)
        except ftrack.api.ftrackerror.FTrackError as error:
            mc.warning(u'Could not set timeline due to: "{0}"'.format(error))
        else:
            handles = float(shot.get('handles'))

            mc.warning(
                'Setting timeline to {0} {1} '.format(startFrame, endFrame)
            )

            # Add handles to start and end frame.
            hsf = startFrame - handles
            hef = endFrame + handles

            mc.playbackOptions(
                minTime=hsf,
                maxTime=hef,
                animationStartTime=hsf,
                animationEndTime=hef
            )

    @staticmethod
    def getAssets():
        '''Return the available assets in scene, return the *componentId(s)*'''
        allObjects = mc.ls(type='ftrackAssetNode')

        componentIds = []

        for ftrackobj in allObjects:
            if not mc.referenceQuery(ftrackobj, isNodeReferenced=True):
                assetcomponentid = mc.getAttr(ftrackobj + '.assetComponentId')
                nameInScene = mc.listConnections(
                    '{0}.assetLink'.format(ftrackobj),
                    destination=True,
                    source=False
                )
                if not nameInScene:
                    mc.warning(
                        'AssetLink broken for assetNode {0}'.format(
                            str(ftrackobj)
                        )
                    )
                    continue
                else:
                    nameInScene = nameInScene[0]

                componentIds.append((assetcomponentid, nameInScene))
        return componentIds

    @staticmethod
    def getFileName():
        '''Return the *current scene* name'''
        return mc.file(query=1, sceneName=True)

    @staticmethod
    def getMainWindow():
        '''Return the *main window* instance'''

        from QtExt import QtWidgets
        ptr = mui.MQtUtil.mainWindow()
        if ptr is not None:
            return Connector.wrapinstance(ptr, QtWidgets.QMainWindow)

    @staticmethod
    def wrapinstance(ptr, base=None):
        """
        Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)

        :param ptr: Pointer to QObject in memory
        :type ptr: long or Swig instance
        :param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
        :type base: QtGui.QWidget
        :return: QWidget or subclass instance
        :rtype: QtGui.QWidget
        """

        if ptr is None:
            return None

        if not base:
            from QtExt import QtWidgets, QtCore
            base = QtWidgets.QObject

        try:
            from pymel.core.uitypes import pysideWrapInstance
        except ImportError:
            ptr = long(ptr)  # Ensure type
            if 'shiboken' in globals():
                import shiboken
                if base is None:
                    qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
                    metaObj = qObj.metaObject()
                    cls = metaObj.className()
                    superCls = metaObj.superClass().className()
                    if hasattr(QtWidgets, cls):
                        base = getattr(QtWidgets, cls)
                    elif hasattr(QtWidgets, superCls):
                        base = getattr(QtWidgets, superCls)
                    else:
                        base = QtWidgets.QWidget
                return shiboken.wrapInstance(long(ptr), base)
            return None
        else:
            return pysideWrapInstance(ptr, base)

    @staticmethod
    def importAsset(iAObj):
        '''Import the asset provided by *iAObj*'''
        iAObj.assetName = "_".join(
            [iAObj.assetType.upper(), iAObj.assetName, "AST"]
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
        mc.select(applicationObject, r=True)

    @staticmethod
    def selectObjects(selection):
        '''Select the given *selection*'''
        mc.select(selection)

    @staticmethod
    def removeObject(applicationObject=''):
        '''Remove the *applicationObject* from the scene'''
        ftrackNode = mc.listConnections(
            '{0}.ftrack'.format(applicationObject), d=False, s=True
        )
        ftrackNode = ftrackNode[0]
        referenceNode = False
        for node in mc.listConnections('{0}.assetLink'.format(ftrackNode)):
            if mc.nodeType(node) == 'reference':
                if 'sharedReferenceNode' in node:
                    continue
                referenceNode = node

        if referenceNode:
            referenceNode = Connector.getReferenceNode(applicationObject)
            if referenceNode:
                mc.file(rfn=referenceNode, rr=True)
        else:
            nodes = mc.listConnections('{0}.assetLink'.format(ftrackNode))
            nodes.append(ftrackNode)
            for node in nodes:
                try:
                    mc.delete(node)
                except Exception as error:
                    print 'Node: {0} could not be deleted, error: {1}'.format(
                        node, error
                    )

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
        '''Return the selected nodes'''
        return mc.ls(selection=True)

    @staticmethod
    def getSelectedAssets():
        '''Return the selected assets'''
        selection = mc.ls(selection=True)
        selectedObjects = []
        for node in selection:
            try:
                mc.listConnections('{0}.ftrack'.format(node), d=False, s=True)
                selectedObjects.append(node)
            except:
                transformParents = mc.listRelatives(
                    node, allParents=True, type='transform'
                )
                for parent in transformParents:
                    try:
                        mc.listConnections(
                            '{0}.ftrack'.format(parent), d=False, s=True
                        )
                        selectedObjects.append(parent)
                        break
                    except:
                        pass

        return selectedObjects

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        '''Set the node color'''
        pass

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
        return 'maya'

    @staticmethod
    def getUniqueSceneName(assetName):
        '''Return a unique scene name for the given *assetName*'''
        currentSelection = mc.ls(sl=True)
        try:
            mc.select(assetName)
            uniqueNameNotFound = True
            i = 0
            while uniqueNameNotFound:
                uniqueAssetName = assetName + str(i)
                try:
                    mc.select(uniqueAssetName)
                except:
                    uniqueNameNotFound = False
                i = i + 1

        except:
            uniqueAssetName = assetName
        if len(currentSelection) > 0:
            mc.select(currentSelection)
        return uniqueAssetName

    @staticmethod
    def getReferenceNode(assetLink):
        '''Return the references nodes for the given *assetLink*'''
        res = ''
        try:
            res = mc.referenceQuery(assetLink, referenceNode=True)
        except:
            childs = mc.listRelatives(assetLink, children=True)

            if childs:
                for child in childs:
                    try:
                        res = mc.referenceQuery(child, referenceNode=True)
                        break

                    except:
                        pass
            else:
                return None
        if res == '':
            print 'Could not find reference node'
            return None
        else:
            return res

    @staticmethod
    def takeScreenshot():
        '''Take a screenshot and save it in the temp folder'''
        import tempfile
        nodes = mc.ls(sl=True)
        mc.select(cl=True)

        # Ensure JPEG is set in renderglobals.
        # Only used on windows for some reason
        currentFormatStr = mc.getAttr(
            'defaultRenderGlobals.imageFormat',
            asString=True
        )

        restoreRenderGlobals = False
        if not (
            'jpg' in currentFormatStr.lower() or
            'jpeg' in currentFormatStr.lower()
        ):
            currentFormatInt = mc.getAttr('defaultRenderGlobals.imageFormat')
            mc.setAttr('defaultRenderGlobals.imageFormat', 8)
            restoreRenderGlobals = True

        filename = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        res = mc.playblast(
            format="image",
            frame=mc.currentTime(query=True),
            compression='jpg',
            quality=80,
            showOrnaments=False,
            forceOverwrite=True,
            viewer=False,
            filename=filename
        )

        if restoreRenderGlobals:
            mc.setAttr('defaultRenderGlobals.imageFormat', currentFormatInt)

        if nodes is not None and len(nodes):
            mc.select(nodes)
        res = res.replace('####', '*')
        import glob
        path = glob.glob(res)[0]
        return path

    @staticmethod
    def batch():
        '''Return whether the application is in *batch mode* or not'''
        return mc.about(batch=True)

    @classmethod
    def registerAssets(cls):
        '''Register all the available assets'''
        import mayaassets
        mayaassets.registerAssetTypes()
        super(Connector, cls).registerAssets()

    @staticmethod
    def executeInThread(function, arg):
        '''Execute the given *function* with provided *args* in a separate thread
        '''
        import maya.utils
        maya.utils.executeInMainThreadWithResult(function, arg)

    # Make certain scene validations before actualy publishing
    @classmethod
    def prePublish(cls, iAObj):
        '''Pre Publish check for given *iAObj*'''
        result, message = super(Connector, cls).prePublish(iAObj)
        if not result:
            return result, message

        nodes = mc.ls(sl=True)
        if len(nodes) == 0:
            if (
                'exportMode' in iAObj.options and
                iAObj.options['exportMode'] == 'Selection'
            ):
                return None, 'Nothing selected'
            if (
                'alembicExportMode' in iAObj.options and
                iAObj.options['alembicExportMode'] == 'Selection'
            ):
                return None, 'Nothing selected'

        return True, ''
