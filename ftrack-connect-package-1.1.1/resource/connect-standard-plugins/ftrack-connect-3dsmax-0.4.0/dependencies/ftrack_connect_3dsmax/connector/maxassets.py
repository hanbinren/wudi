# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import copy
import uuid
import ftrack

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    FTAssetType,
    FTComponent
)

from ftrack_connect.connector import panelcom

import maxcon

import MaxPlus

from .alembic import *
from .assethelper import *
from .assetimportmodes import *
from .maxcallbacks import *
from .utils import *
from .xrefs import *

import logging
logger = logging.getLogger(__name__)

ticks = MaxPlus.Core.EvalMAXScript('ticksperframe').GetInt()
currentStartFrame =  MaxPlus.Animation.GetAnimRange().Start() / ticks
currentEndFrame =  MaxPlus.Animation.GetAnimRange().End() / ticks


class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()

    def _getUniqueFtrackAssetHelperName(self, iAObj):
        return getUniqueNodeName(iAObj.assetName + 'FtrackAssetHelper')

    def __getAssetIdFromHelperNode(self, helperNode):
        assetVersId = helperNode.Object.ParameterBlock.assetId.Value
        vers = ftrack.AssetVersion(id=assetVersId)
        return vers.getAsset().getId()

    def _cleanupSelectionAndGroupUnderHelper(self, helperNode):
        assetId = self.__getAssetIdFromHelperNode(helperNode)
        rootNode = MaxPlus.Core.GetRootNode()

        nodesToDelete = []

        logger.debug(u'Removing duplicated asset helper objects')
        for node in MaxPlus.SelectionManager.Nodes:
            if isFtrackAssetHelper(node) and node.Parent == rootNode:
                helperAssetId = self.__getAssetIdFromHelperNode(node)
                if helperAssetId == assetId:
                    logger.debug(
                        u'Deleting imported helper node {0}'.format(node.Name))
                    nodesToDelete.append(node)

        # Delete helper nodes that represent the asset we are importing.
        for node in nodesToDelete:
            MaxPlus.SelectionManager.DeSelectNode(node)
            node.Delete()

        logger.debug(u'Parenting objects to helper object')
        for node in MaxPlus.SelectionManager.Nodes:
            if node.Parent == rootNode:
                node.Parent = helperNode

    def _reimportSceneXRefs(self):
        for node in MaxPlus.SelectionManager.Nodes:
            if isFtrackAssetHelper(node) and getAssetImportMode(node) == SCENE_XREF_IMPORT_MODE:
                if not sceneXRefImported(node):
                    logger.debug(u'Re-importing {0} scene xref.'.format(
                        node.Name))
                    reimportSceneXRef(node)

    def _reportError(self, msg):
        # It seems there's no good way to raise an error and
        # abort publishing. Raising an exception produces
        # a very generic error message in the publish dialog and
        # the user has to check in the script editor to find the real error.
        # For now, we use a message box to tell the user what was wrong.
        from QtExt import QtWidgets
        QtWidgets.QMessageBox.critical(None, "Error", msg)
        raise RuntimeError(msg)

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''
        logger.debug(u'Importing asset {0}'.format(iAObj.filePath))

        savedSel = saveSelection()
        deselectAll()

        logger.debug(u'Importing asset')

        ftrackHelperName = self._getUniqueFtrackAssetHelperName(iAObj)
        logger.debug(u'Ftrack helper obj name = {0}'.format(ftrackHelperName))

        if iAObj.componentName == 'alembic':
            if exocortexAlembicAvailable():
                try:
                    alembicArgs = exocortexImportAlembic(
                        iAObj.filePath, iAObj.options)

                    logger.debug(u'Creating ftrack asset helper object')
                    helperNode = createFtrackAssetHelper(
                        ftrackHelperName,
                        iAObj.assetVersionId,
                        int(iAObj.assetVersion),
                        iAObj.filePath,
                        iAObj.componentName,
                        iAObj.componentId)

                    setAlembicImportArgs(helperNode, alembicArgs)
                    self._cleanupSelectionAndGroupUnderHelper(helperNode)
                except RuntimeError, e:
                    self._reportError(str(e))
            else:
                self._reportError(
                    'Exocortex Crate plugin not available. Cannot import Alembic.')
        else:
            importMode = iAObj.options['importMode'] if 'importMode' in iAObj.options else 'importMode'
            logger.debug(u'Import mode = {0}'.format(importMode))

            if importMode == OBJECT_XREF_IMPORT_MODE:
                logger.debug(u'Importing asset as a Obj XRefs')
                importObjXRefs(iAObj.filePath)

                logger.debug(u'Creating ftrack asset helper object')
                helperNode = createFtrackAssetHelper(
                    ftrackHelperName,
                    iAObj.assetVersionId,
                    int(iAObj.assetVersion),
                    iAObj.filePath,
                    iAObj.componentName,
                    iAObj.componentId,
                    importMode)

                self._cleanupSelectionAndGroupUnderHelper(helperNode)
                self._reimportSceneXRefs()
            elif importMode == SCENE_XREF_IMPORT_MODE:
                logger.debug(u'Creating ftrack asset helper object')
                helperNode = createFtrackAssetHelper(
                    ftrackHelperName,
                    iAObj.assetVersionId,
                    int(iAObj.assetVersion),
                    iAObj.filePath,
                    iAObj.componentName,
                    iAObj.componentId,
                    importMode)

                logger.debug(u'Importing asset as a Scene XRef')
                importSceneXRef(iAObj.filePath, helperNode.Name)
            else: #if importMode == IMPORT_IMPORT_MODE:
                logger.debug(u'Importing asset')
                mergeMaxFile(iAObj.filePath)

                logger.debug(u'Creating ftrack asset helper object')
                helperNode = createFtrackAssetHelper(
                    ftrackHelperName,
                    iAObj.assetVersionId,
                    int(iAObj.assetVersion),
                    iAObj.filePath,
                    iAObj.componentName,
                    iAObj.componentId,
                    importMode)

                self._cleanupSelectionAndGroupUnderHelper(helperNode)
                self._reimportSceneXRefs()

        restoreSelection(savedSel)
        logger.debug(u'Import asset done')
        return 'Imported ' + iAObj.assetType + ' asset'

    def getGroupName(self, nodes, assetName):
        '''Return the node among the *nodes* containing the given *assetName*.'''
        for node in nodes:
            splitnode = node.split('|')
            for n in splitnode:
                if assetName in n:
                    return n
        return assetName

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = '3dsmax'

        if iAObj.options.get('exportMode') == 'Selection':
            # Check if the selection is empty and abort if it is.
            if selectionEmpty():
                self._reportError('No objects selected to publish.')

            exportSelectedMode = True
        else:
            exportSelectedMode = False

        publishedComponents = []

        temporaryPath = os.path.join(
            MaxPlus.PathManager.GetTempDir() + uuid.uuid4().hex + '.max')

        if exportSelectedMode:
            MaxPlus.FileManager.SaveSelected(temporaryPath)
        else:
            MaxPlus.FileManager.Save(temporaryPath, False, False)

        publishedComponents.append(
            FTComponent(
                componentname=componentName,
                path=temporaryPath
            )
        )

        # Handle dependencies.
        dependenciesVersion = []
        for node in getAllFtrackAssetHelperNodes(recurse=True):
            obj = node.Object
            dependencyAssetId = obj.ParameterBlock.assetId.Value
            if dependencyAssetId:
                dependencyVersion = ftrack.AssetVersion(dependencyAssetId)
                dependenciesVersion.append(dependencyVersion)

        if dependenciesVersion:
            currentVersion = ftrack.AssetVersion(iAObj.assetVersionId)
            currentVersion.addUsesVersions(versions=dependenciesVersion)

        panelComInstance.emitPublishProgressStep()
        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    def getSceneSettingsObj(self, iAObj):
        '''Return default settings for the provided *iAObj*.'''
        iAObjCopy = copy.copy(iAObj)
        iAObjCopy.options['exportMode'] = 'All'
        iAObjCopy.customComponentName = 'maxScene'
        return iAObjCopy

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        assetHelperNode = MaxPlus.INode.GetINodeByName(applicationObject)

        if iAObj.componentName == 'alembic':
            if exocortexAlembicAvailable():
                deleteAllChildren(assetHelperNode)
                exocortexImportAlembic(iAObj.filePath, iAObj.options)
                self._cleanupSelectionAndGroupUnderHelper(assetHelperNode)
            else:
                self._reportError(
                    'Exocortex Crate plugin not available. Cannot change Alembic version.')
        else:
            importMode = getAssetImportMode(assetHelperNode)

            if importMode == OBJECT_XREF_IMPORT_MODE:
                deleteAllChildren(assetHelperNode)
                importObjXRefs(iAObj.filePath)
                self._cleanupSelectionAndGroupUnderHelper(assetHelperNode)
            elif importMode == SCENE_XREF_IMPORT_MODE:
                updateSceneXRef(iAObj.filePath, assetHelperNode)
            else: #if importMode == IMPORT_IMPORT_MODE:
                deleteAllChildren(assetHelperNode)
                mergeMaxFile(iAObj.filePath)
                self._cleanupSelectionAndGroupUnderHelper(assetHelperNode)

        logger.debug(u'Updating Ftrack helper object.')
        updateFtrackAssetHelper(
            assetHelperNode,
            iAObj.assetVersionId,
            int(iAObj.assetVersion),
            iAObj.filePath,
            iAObj.componentName,
            iAObj.componentId)

        return True

class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        publishedComponents = []

        totalSteps = self.getTotalSteps(
            steps=[
                iAObj.options['3dsmax'],
                iAObj.options['alembic'],
            ]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        if iAObj.options.get('alembic'):
            if exocortexAlembicAvailable():
                temporaryPath = os.path.join(
                    MaxPlus.PathManager.GetTempDir() + uuid.uuid4().hex + '.abc')

                publishedComponents.append(
                    FTComponent(
                        componentname='alembic',
                        path=temporaryPath
                    )
                )

                try:
                    exocortexExportAlembic(temporaryPath, iAObj.options)
                except RuntimeError, e:
                    self._reportError(str(e))
            else:
                self._reportError(
                    'Exocortex Crate plugin not available. Cannot publish Alembic.')

            panelComInstance.emitPublishProgressStep()

        if iAObj.options['3dsmax']:
            iAObj.setTotalSteps = False
            components, message = GenericAsset.publishAsset(self, iAObj)
            publishedComponents += components

            panelComInstance.emitPublishProgressStep()

        return publishedComponents, 'Published GeometryAsset asset'

    @staticmethod
    def importOptions():
        '''Return import options for the component'''

        xml = '''
        <tab name="Max Options" accepts="max">
            <row name="Import Mode" accepts="max">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                    <optionitem name="Object XRef"/>
                    <optionitem name="Scene XRef"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic Options" enabled="{0}">
            <row name="Create Time Control" accepts="max">
                <option type="checkbox" name="alembicCreateTimeControl" value="False"/>
            </row>
            <row name="Object Duplication" accepts="max">
                <option type="radio" name="alembicObjectDuplication">
                        <optionitem name="Copy" value="True"/>
                        <optionitem name="Instance"/>
                        <optionitem name="Reference"/>
                </option>
            </row>
        </tab>
        '''
        xml = xml.format(str(exocortexAlembicAvailable()))
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = """
        <tab name="Max Options" accepts="max">
            <row name="Max" accepts="max">
                <option type="checkbox" name="3dsmax" value="True"/>
            </row>
            <row name="Max Selection Mode" accepts="max">
                <option type="radio" name="exportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic Options" enabled="{2}">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic" value="{2}"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation"/>
            </row>
            <row name="Frame Range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Samples Per Frame">
                <option type="float" name="samplesPerFrame" value="1"/>
            </row>
            <row name="Normals" accepts="max">
                <option type="checkbox" name="alembicNormalsWrite" value="True"/>
            </row>
            <row name="UVs" accepts="max">
                <option type="checkbox" name="alembicUVWrite" value="True"/>
            </row>
            <row name="Flatten Hierarchy" accepts="max">
                <option type="checkbox" name="alembicFlattenHierarchy" value="False"/>
            </row>
            <row name="Alembic Selection Mode" accepts="max">
                <option type="radio" name="alembicExportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        """
        s = os.getenv('FS', currentStartFrame)
        e = os.getenv('FE', currentEndFrame)
        xml = xml.format(s, e, str(exocortexAlembicAvailable()))
        return xml

class CameraAsset(GenericAsset):

    def __init__(self):
        super(CameraAsset, self).__init__()

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        result = GenericAsset.importAsset(self, iAObj)
        return result

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        result = GenericAsset.changeVersion(self, iAObj, applicationObject)
        return result

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        savedSel = saveSelection()
        selectOnlyCameras()

        if selectionEmpty():
            self._reportError('No cameras selected to publish.')

        totalSteps = self.getTotalSteps(
            steps=[
                True, iAObj.options['maxPublishScene'], iAObj.options['alembic']]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        publishedComponents, message = GenericAsset.publishAsset(self, iAObj)
        if not publishedComponents:
            return publishedComponents, message

        if iAObj.options['maxPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        if iAObj.options.get('alembic'):
            if exocortexAlembicAvailable():
                temporaryPath = os.path.join(
                    MaxPlus.PathManager.GetTempDir() + uuid.uuid4().hex + '.abc')

                publishedComponents.append(
                    FTComponent(
                        componentname='alembic',
                        path=temporaryPath
                    )
                )

                try:
                    exocortexExportAlembic(temporaryPath, iAObj.options)
                except RuntimeError, e:
                    self._reportError(str(e))
            else:
                self._reportError(
                    'Exocortex Crate plugin not available. Cannot publish Alembic.')

            panelComInstance.emitPublishProgressStep()

        restoreSelection(savedSel)

        return publishedComponents, message

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Import mode" accepts="max">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                    <optionitem name="Object XRef"/>
                </option>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''
        xml = '''
        <tab name="Options">
            <row name="Export" accepts="max">
                <option type="radio" name="exportMode">
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
            <row name="Attach scene to asset" accepts="max">
                <option type="checkbox" name="maxPublishScene"/>
            </row>
        </tab>
        <tab name="Alembic options" enabled="{2}">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic" value="{2}"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation"/>
            </row>
            <row name="Frame Range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Samples Per Frame">
                <option type="float" name="samplesPerFrame" value="1"/>
            </row>
            <row name="Alembic Selection Mode" accepts="max">
                <option type="radio" name="alembicExportMode">
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        '''
        s = os.getenv('FS', currentStartFrame)
        e = os.getenv('FE', currentEndFrame)
        xml = xml.format(s, e, str(exocortexAlembicAvailable()))
        return xml

class RigAsset(GenericAsset):
    def __init__(self):
        super(RigAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        totalSteps = self.getTotalSteps(
            steps=[True, iAObj.options['maxPublishScene']]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        publishedComponents, message = GenericAsset.publishAsset(self, iAObj)
        if not publishedComponents:
            return publishedComponents, message

        if iAObj.options['maxPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        return publishedComponents, message

    @staticmethod
    def importOptions():
        '''Return import options for the component'''

        xml = '''
        <tab name="Max Options" accepts="max">
            <row name="Import Mode" accepts="max">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                    <optionitem name="Object XRef"/>
                </option>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Options">
            <row name="Attach scene to asset" accepts="max">
                <option type="checkbox" name="maxPublishScene"/>
            </row>
            <row name="Export" accepts="max">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                        <optionitem name="Selection"/>
                </option>
            </row>
        </tab>
        '''
        return xml

class SceneAsset(GenericAsset):
    def __init__(self):
        super(SceneAsset, self).__init__()

    def __resetScene(self):
        cmd = '''
        result = false
        if checkForSave() do (
            resetMaxFile #noprompt
            result = true
        )
        result
        '''
        return MaxPlus.Core.EvalMAXScript(cmd).Get()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(1)
        iAObj.customComponentName = '3dsmaxScene'
        components, message = GenericAsset.publishAsset(self, iAObj)
        return components, message

    def importAsset(self, iAObj=None):
        if self.__resetScene():
            logger.debug(u'Importing scene asset {0}'.format(iAObj.filePath))

            importMode = iAObj.options['importMode'] if 'importMode' in iAObj.options else 'importMode'
            logger.debug(u'Import mode = {0}'.format(importMode))

            if importMode == SCENE_XREF_IMPORT_MODE:
                super(SceneAsset, self).importAsset(iAObj)
            else:
                # Temporary disable the file open callbacks.
                with DisableOpenFileCallbacks() as d:
                    MaxPlus.FileManager.Open(iAObj.filePath, True, True, True, False)
                    selectAll()

                    logger.debug(u'Creating ftrack asset helper object')
                    ftrackHelperName = self._getUniqueFtrackAssetHelperName(iAObj)
                    logger.debug(u'Ftrack helper obj name = {0}'.format(ftrackHelperName))

                    helperNode = createFtrackAssetHelper(
                        ftrackHelperName,
                        iAObj.assetVersionId,
                        int(iAObj.assetVersion),
                        iAObj.filePath,
                        iAObj.componentName,
                        iAObj.componentId,
                        importMode)

                    self._cleanupSelectionAndGroupUnderHelper(helperNode)
                    self._reimportSceneXRefs()
                    deselectAll()

                    # Call manually the asset refresh callback.
                    checkForNewAssetsAndRefreshAssetManager()

                return 'Imported ' + iAObj.assetType + ' asset'

    def changeVersion(self, iAObj=None, applicationObject=None):
        if self.__resetScene():
            self.importAsset(iAObj)
            return True

        return False

    @staticmethod
    def importOptions():
        '''Return import options for the component'''

        xml = '''
        <tab name="Options">
            <row name="Import mode" accepts="max">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                    <optionitem name="Scene XRef"/>
                </option>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Max options" accepts="max">
            <row name="Max Selection Mode" accepts="max">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                </option>
            </row>
        </tab>
        '''
        return xml

class LightRigAsset(GenericAsset):
    def __init__(self):
        super(LightRigAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        totalSteps = self.getTotalSteps(
            steps=[True, iAObj.options['maxPublishScene']]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        publishedComponents, message = GenericAsset.publishAsset(self, iAObj)
        if not publishedComponents:
            return publishedComponents, message

        if iAObj.options['maxPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        return publishedComponents, message

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Options">
            <row name="Attach scene to asset" accepts="max">
                <option type="checkbox" name="maxPublishScene"/>
            </row>
            <row name="Export" accepts="max">
                <option type="radio" name="exportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        '''
        return xml

def registerAssetTypes():

    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='cam', cls=CameraAsset)
    assetHandler.registerAssetType(name='lgt', cls=LightRigAsset)
    assetHandler.registerAssetType(name='rig', cls=RigAsset)
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
