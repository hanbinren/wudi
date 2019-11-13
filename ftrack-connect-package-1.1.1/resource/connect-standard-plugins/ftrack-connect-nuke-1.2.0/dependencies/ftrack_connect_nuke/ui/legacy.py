# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import ftrack
import clique
import glob
import tempfile
import uuid
import urlparse

from FnAssetAPI.ui.toolkit import QtGui, QtWidgets

import FnAssetAPI

import nuke
import nukescripts

from ftrack_connect.connector import (
    FTComponent, FTAssetObject, HelpFunctions
)
import ftrack_connect.util
import ftrack_connect.asset_version_scanner

import ftrack_connect_nuke
from ftrack_connect_nuke import connector
from ftrack_connect_nuke.connector import nukeassets


from knobs import TableKnob, BrowseKnob, HeaderKnob
from ftrack_connect.ui.theme import applyTheme

current_module = ".".join(__name__.split(".")[:-1])+'.legacy'



class ProgressDialog(QtWidgets.QDialog):
    def __init__(self):
        super(ProgressDialog, self).__init__()
        applyTheme(self, 'integration')
        self.hbox = QtWidgets.QHBoxLayout()
        self.progressBar = QtWidgets.QProgressBar(self)
        self.hbox.addWidget(self.progressBar)
        self.setLayout(self.hbox)

        self.setMinimumSize(QtCore.QSize(720, 560))


def refAssetManager():
    # Inline to avoid Nuke crashing on startup without traceback.
    from ftrack_connect.connector import PanelComInstance
    panelComInstance = PanelComInstance.instance()
    panelComInstance.refreshListeners()


def handle_scan_result(result, scanned_ftrack_nodes):
    '''Handle scan *result*.'''
    message = []
    for partial_result, ftrack_node in zip(result, scanned_ftrack_nodes):
        if partial_result is None:
            # The version was not found on the server, probably because it has
            # been deleted.
            continue

        scanned = partial_result.get('scanned')
        latest = partial_result.get('latest')
        if scanned['version'] != latest['version']:
            message.append(
                '{0} can be updated from v{1} to v{2}'.format(
                    ftrack_node, scanned['version'], latest['version']
                )
            )

    if message:
        nuke.message('\n'.join(message))


def scan_for_new_assets():
    '''Scan scene for outdated asset versions.'''
    allAssets = connector.Connector.getAssets()
    message = ''

    check_items = []
    scanned_ftrack_nodes = []

    for ftrack_node in allAssets:
        ftrack_node = ftrack_node[1]
        n = nuke.toNode(HelpFunctions.safeString(ftrack_node))
        ftrack_asset_version_id_url = n.knob('assetVersionId').value()

        url = urlparse.urlparse(ftrack_asset_version_id_url)
        query = urlparse.parse_qs(url.query)
        entityType = query.get('entityType')[0]

        asset_version_id = url.netloc
        component_name = n.knob('componentName').value()

        if asset_version_id is None:
            nuke.message(
                'FTrack node "{0}" does not contain data!'.format(ftrack_node)
            )
            continue

        new_item = {
            'asset_version_id': asset_version_id,
            'component_name': component_name   
        }
        check_items.append(new_item)
        scanned_ftrack_nodes.append(ftrack_node)

    if scanned_ftrack_nodes:
        import ftrack_api
        session = ftrack_api.Session(
            auto_connect_event_hub=False,
            plugin_paths=None
        )
        scanner = ftrack_connect.asset_version_scanner.Scanner(
            session=session,
            result_handler=(
                lambda result: ftrack_connect.util.invoke_in_main_thread(
                    handle_scan_result,
                    result,
                    scanned_ftrack_nodes
                )
            )
        )
        scanner.scan(check_items)


@ftrack.withGetCache
def addPublishKnobsToGroupNode(g):
    tab = nuke.Tab_Knob('ftrackpub', 'ftrack Publish')
    g.addKnob(tab)

    headerKnob = nuke.PyCustom_Knob(
        'fheader', '', 'ftrack_connect_nuke.ui.knobs.HeaderKnob("{0}")'.format(
            str(uuid.uuid1())
        )
    )
    headerKnob.setFlag(nuke.STARTLINE)
    g.addKnob(headerKnob)

    whitespaceKnob = nuke.Text_Knob('fwhite', '  ', '  ')
    g.addKnob(whitespaceKnob)


    browseKnob = nuke.PyCustom_Knob("fpubto", "Publish to:", "ftrack_connect_nuke.ui.knobs.BrowseKnob()")
    browseKnob.setFlag(nuke.STARTLINE)
    g.addKnob(browseKnob)

    existingAssetsKnob = nuke.Enumeration_Knob('fassetnameexisting', 'Existing assets:', ['New'])
    g.addKnob(existingAssetsKnob)

    nameKnob = nuke.String_Knob('ftrackassetname', 'Asset name:', '')
    g.addKnob(nameKnob)

    hrefKnob = nuke.String_Knob('componentId', 'componentId', '')
    hrefKnob.setVisible(False)
    g.addKnob(hrefKnob)

    typeKnob = nuke.Enumeration_Knob('ftrackassettype', 'Asset type:', ['No inputs connected'])
    typeKnob.setFlag(nuke.STARTLINE)
    g.addKnob(typeKnob)

    tableKnob = nuke.PyCustom_Knob("ftable", "Components:", "ftrack_connect_nuke.ui.knobs.TableKnob()")
    tableKnob.setFlag(nuke.STARTLINE)
    g.addKnob(tableKnob)

    copyFilesKnob = nuke.Boolean_Knob('fcopy', 'Force copy files', True)
    copyFilesKnob.setFlag(nuke.STARTLINE)
    copyFilesKnob.setTooltip(
        'This will force the selection of a managed ftrack Location and the '
        'files will be copied to a new place when published to ftrack. If not '
        'checked ftrack will pick a Location depending on the Storage scenario '
        'and any custom Location plugins.'
    )
    g.addKnob(copyFilesKnob)

    scriptKnob = nuke.Boolean_Knob('fscript', 'Attach nukescript', 1)
    scriptKnob.setFlag(nuke.STARTLINE)
    g.addKnob(scriptKnob)

    commentKnob = nuke.Multiline_Eval_String_Knob('fcomment', 'Comment:', '')
    g.addKnob(commentKnob)

    refreshKnob = nuke.PyScript_Knob('refreshknob', 'Refresh', 'ftrack_connect_nuke.ui.legacy.ftrackPublishKnobChanged(forceRefresh=True)')
    refreshKnob.setFlag(nuke.STARTLINE)
    g.addKnob(refreshKnob)

    publishKnob = nuke.PyScript_Knob('pknob', 'Publish', 'ftrack_connect_nuke.ui.legacy.publishAssetKnob()')
    g.addKnob(publishKnob)
    publishKnob.setEnabled(False)


def createFtrackPublish():
    g = nuke.createNode('Group')
    g.begin()
    inputNode = nuke.createNode("Input", inpanel=False)
    g.end()
    nodeName = 'ftrackPublish'
    nodeName = connector.Connector.getUniqueSceneName(nodeName)
    g['name'].setValue(nodeName)
    addPublishKnobsToGroupNode(g)


def publishAssetKnob():
    n = nuke.thisNode()
    header = getHeaderKnob(n)
    ftrackPublishKnobChanged(g=n, forceRefresh=True)
    n.knob('pknob').setEnabled(False)
    tableWidget = n['ftable'].getObject().tableWidget
    content = []
    for row in range(tableWidget.rowCount()):
        filePath = tableWidget.item(row, 1).text()
        compName = tableWidget.item(row, 2).text()
        first = tableWidget.item(row, 5).text()
        last = tableWidget.item(row, 6).text()
        nodeName = tableWidget.item(row, 3).text()
        meta = getMetaData(nodeName)


        if tableWidget.item(row, 4).toolTip() == 'T':
            content.append((filePath, compName, first, last, nodeName, meta))
        else:
            header.setMessage('Can not find ' + filePath + ' on disk', 'error')
            return

    if len(content) == 0:
        header.setMessage('Nothing to publish', 'warning')
        return

    if 'New' == n['fassetnameexisting'].value() and n['ftrackassetname'].value() == '':
        header.setMessage('Enter an assetname or select an existing', 'warning')
        return
    elif 'New' != n['fassetnameexisting'].value():
        assetName = n['fassetnameexisting'].value()
    else:
        assetName = n['ftrackassetname'].value()

    comment = n['fcomment'].value()

    if os.getenv('FTRACK_MODE','') == 'Shot':
        currentTask = None
        shot = connector.Connector.objectById(os.environ['FTRACK_SHOTID'])
        tasks = shot.getTasks()
        selectedTask = n['ftask'].value()
        for task in tasks:
            if task.getName() == selectedTask:
                currentTask = task
    else:
        currentTask = connector.Connector.objectById(n.knob('fpubto').getObject().targetTask)

    shot = currentTask.getParent()

    publishAsset(n, assetName, content, comment, shot, currentTask)
    n.knob('pknob').setEnabled(True)


def get_dependencies():
    dependencies = {}

    ft_attributes = [
        'assetVersionId',
    ]

    for node in nuke.allNodes():
        for attr in ft_attributes:
            attribute =  node.knob(attr)
            if attribute:
                knob_value = attribute.value()
                if 'ftrack' in knob_value:
                   version_id = knob_value.split('ftrack://')[-1].split('?')[0]
                   dependency_version = ftrack.AssetVersion(version_id)
                   print 'dependency %s found' % dependency_version
                   dependencies[node['name'].value()] = dependency_version

    return dependencies


def publishAsset(n, assetName, content, comment, shot, currentTask):
    header = getHeaderKnob(n)

    if not currentTask:
        header.setMessage('Could not find current task', 'warning')
    else:
        publishProgress = nuke.ProgressTask('Publishing assets')
        publishProgress.setProgress(0)
        currentTaskId = currentTask.getId()
        assetType = n['ftrackassettype'].value()

        publishProgress.setMessage('Validating asset types')
        try:
            ftrack.AssetType(assetType)
        except ftrack.FTrackError:
            header.setMessage(
                'No Asset type with short name "{0}" found. Contact your '
                'system administrator to add it.'.format(assetType), 'warning'
            )
            return

        publishProgress.setMessage('Creating new version')
        asset = shot.createAsset(assetName, assetType)
        assetVersion = asset.createVersion(comment=comment, taskid=currentTaskId)

        if assetType in ['img', 'cam', 'geo', 'render']:
            if assetType == 'img':
                imgAsset = nukeassets.ImageSequenceAsset()
                publishedComponents = imgAsset.publishContent(content, assetVersion, progressCallback=publishProgress.setProgress)

            elif assetType == 'cam':
                camAsset = nukeassets.CameraAsset()
                publishedComponents = camAsset.publishContent(content, assetVersion, progressCallback=publishProgress.setProgress)

            elif assetType == 'geo':
                geoAsset = nukeassets.GeometryAsset()
                publishedComponents = geoAsset.publishContent(content, assetVersion, progressCallback=publishProgress.setProgress)

            elif assetType == 'render':
                renderAsset = nukeassets.RenderAsset()
                publishedComponents = renderAsset.publishContent(
                    content, assetVersion,
                    progressCallback=publishProgress.setProgress
                )

            if n['fscript'].value():
                if n['fcopy'].value():
                    temporaryPath = HelpFunctions.temporaryFile(suffix='.nk')
                    nuke.scriptSave(temporaryPath)
                    mainPath = temporaryPath
                else:
                    if nuke.Root().name() == 'Root':
                        tmp_script = tempfile.NamedTemporaryFile(suffix='.nk')
                        curScript = nuke.toNode("root").name()
                        nuke.scriptSaveAs(tmp_script.name)
                        mainAbsPath = tmp_script.name
                    else:
                        mainAbsPath = nuke.root()['name'].value()
                    mainPath = mainAbsPath

                publishedComponents.append(FTComponent(componentname='nukescript', path=mainPath))

            if publishedComponents:
                pubObj = FTAssetObject(
                    assetVersionId=assetVersion.getId()
                )
                connector.Connector.publishAssetFiles(
                    publishedComponents,
                    assetVersion,
                    pubObj,
                    copyFiles=n['fcopy'].value(),
                    progressCallback=publishProgress.setProgress
                )

        else:
            header.setMessage("Can't publish this assettype yet", 'info')
            return

        publishProgress.setMessage('Setting up version dependencies')
        dependencies = get_dependencies()
        if dependencies:
            for name, version in dependencies.items():
                assetVersion.addUsesVersions(versions=version)

        assetVersion.publish()
        publishProgress.setProgress(100)

        header.setMessage('Asset published!')

def getMetaData(nodeName):
    n = nuke.toNode(HelpFunctions.safeString(nodeName))
    metaData = []
    metaData.append(('res_x', str(n.width())))
    metaData.append(('res_y', str(n.height())))

    return metaData

def ftrackPublishKnobChanged(forceRefresh=False, g=None):
    g = g or nuke.thisNode()

    if 'ftable' in g.knobs():
        header = getHeaderKnob(g)
        nodeAssetType = ''
        if nuke.thisKnob().name() in ['inputChange', 'fscript'] or forceRefresh == True:
            thisNodeName = g['name'].value()
            g = nuke.toNode(HelpFunctions.safeString(thisNodeName))
            # Add new labels
            cmdString = ''
            assetType = None
            availableAssetTypes = ['']
            inputMissmatch = None

            tableWidget = g['ftable'].getObject().tableWidget
            tableWidget.setRowCount(0)
            components = []

            for inputNode in range(g.inputs()):
                inNode = g.input(inputNode)

                if inNode:
                    if inNode.Class() in ['Read', 'Write']:
                        nodeAssetType = 'img'
                    elif inNode.Class() in ['WriteGeo']:
                        nodeAssetType = 'geo'
                    else:
                        nodeAssetType = ''

                    if not assetType:
                        assetType = nodeAssetType

                    if assetType != nodeAssetType:
                        inputMissmatch = True

                    if nodeAssetType == 'img':
                        fileComp = str(inNode['file'].value())
                        proxyComp = str(inNode['proxy'].value())
                        nameComp = str(inNode['name'].value()).strip()

                        if inNode.Class() == 'Read':
                            first = str(inNode['first'].value())
                            last = str(inNode['last'].value())
                            if first == '0.0' and last == '0.0':
                                first = str(int(nuke.root().knob("first_frame").value()))
                                last = str(int(nuke.root().knob("last_frame").value()))

                            availableAssetTypes = ['img', 'render']

                        elif inNode.Class() == 'Write':

                            # use the timeline to define the amount of frames
                            first = str(int(nuke.root().knob("first_frame").value()))
                            last = str(int(nuke.root().knob("last_frame").value()))

                            # then in case check if the limit are set
                            if inNode['use_limit'].value():
                                first = str(inNode['first'].value())
                                last = str(inNode['last'].value())

                            # always check how many frames are actually available
                            frames = inNode['file'].value()

                            try:
                                # Try to collect the sequence prefix, padding
                                # and extension. If this fails with a ValueError
                                # we are probably handling a non-sequence file.
                                # If so rely on the first_frame and last_frame
                                # of the root node.
                                prefix, padding, extension = frames.split('.')
                            except ValueError:
                                FnAssetAPI.logging.debug(
                                    'Could not determine prefix, padding '
                                    'and extension from "".'.format(frames)
                                )
                                availableAssetTypes = ['render']
                            else:
                                root = os.path.dirname(prefix)
                                files = glob.glob('{0}/*.{1}'.format(
                                    root, extension
                                ))
                                collections = clique.assemble(files)

                                for collection in collections[0]:
                                    if prefix in collection.head:
                                        indexes = list(collection.indexes)
                                        first = str(indexes[0])
                                        last = str(indexes[-1])
                                        break

                                availableAssetTypes = ['img']

                        try:
                            compNameComp = inNode['fcompname'].value()
                        except:
                            compNameComp = ''

                        if compNameComp == '':
                            compNameComp = nameComp

                        components.append((fileComp, compNameComp, first, last, nameComp))
                        if proxyComp != '':
                            components.append((proxyComp, compNameComp + '_proxy', first, last, nameComp))

                    elif nodeAssetType == 'geo':
                        fileComp = str(inNode['file'].value())
                        nameComp = str(inNode['name'].value()).strip()
                        first = str(inNode['first'].value())
                        last = str(inNode['last'].value())

                        if first == '0.0' and last == '0.0':
                            first = str(int(nuke.root().knob("first_frame").value()))
                            last = str(int(nuke.root().knob("last_frame").value()))

                        try:
                            compNameComp = inNode['fcompname'].value()
                        except:
                            compNameComp = ''

                        if compNameComp == '':
                            compNameComp = nameComp

                        components.append(
                            (fileComp, compNameComp, first, last, nameComp)
                        )

                        availableAssetTypes = ['geo', 'cam']

            rowCount = len(components)

            tableWidget.setRowCount(rowCount)
            if len(components) == 0:
                g.knob('pknob').setEnabled(False)
            else:
                g.knob('pknob').setEnabled(True)

            l = [x[1] for x in components]
            wodup = list(set(l))

            if len(l) != len(wodup):
                g.knob('pknob').setEnabled(False)
                header.setMessage('Components can not have the same name', 'warning')

            rowCntr = 0
            for comp in components:
                cb = QtWidgets.QCheckBox('')
                cb.setChecked(True)
                tableWidget.setCellWidget(rowCntr, 0, cb)

                componentItem = QtWidgets.QTableWidgetItem()
                componentItem.setText(comp[0])
                componentItem.setToolTip(comp[0])
                tableWidget.setItem(rowCntr, 1, componentItem)
                componentItem = QtWidgets.QTableWidgetItem()
                componentItem.setText(comp[1])
                componentItem.setToolTip(comp[1])
                tableWidget.setItem(rowCntr, 2, componentItem)

                try:
                    fileCurrentFrame = nukescripts.replaceHashes(comp[0]) % int(float(comp[2]))
                except:
                    print 'File is not sequence'
                    fileCurrentFrame = comp[0]
                if os.path.isfile(fileCurrentFrame):
                    fileExist = 'T'
                else:
                    fileExist = 'F'

                componentItem = QtWidgets.QTableWidgetItem()
                if fileExist == 'T':
                    componentItem.setBackground(QtGui.QColor(20, 161, 74))
                else:
                    componentItem.setBackground(QtGui.QColor(227, 99, 22))
                componentItem.setToolTip(fileExist)
                tableWidget.setItem(rowCntr, 4, componentItem)

                componentItem = QtWidgets.QTableWidgetItem()
                componentItem.setText(comp[2])
                componentItem.setToolTip(comp[2])
                tableWidget.setItem(rowCntr, 5, componentItem)

                componentItem = QtWidgets.QTableWidgetItem()
                componentItem.setText(comp[3])
                componentItem.setToolTip(comp[3])
                tableWidget.setItem(rowCntr, 6, componentItem)

                componentItem = QtWidgets.QTableWidgetItem()
                componentItem.setText(comp[4])
                componentItem.setToolTip(comp[4])
                tableWidget.setItem(rowCntr, 3, componentItem)

                rowCntr += 1

            g['ftrackassettype'].setValues(availableAssetTypes)

            if inputMissmatch:
                tableWidget.setRowCount(0)
                g['ftrackassettype'].setValues(['Missmatch inputs'])

            if cmdString == '':
                cmdString = 'No inputs connected'

            assetEnums = ['New']
            if nodeAssetType != '':
                # assets = connector.Connector.objectById(os.environ['FTRACK_SHOTID']).getAssets(assetTypes=[g['ftrackassettype'].value()])
                pubto = g.knob('fpubto').getObject().targetTask
                assets = connector.Connector.objectById(pubto).getAssets(assetTypes=[g['ftrackassettype'].value()])
                assets = sorted(assets, key=lambda entry: entry.getName().lower())
                assetEnums = assetEnums + [HelpFunctions.safeString(x.getName()) for x in assets]
                FnAssetAPI.logging.info(assetEnums)
                g['fassetnameexisting'].setValues(assetEnums)

            g = nuke.toNode(HelpFunctions.safeString(thisNodeName))
            g.begin()

            # Add more inputs if full
            realInputCount = 0
            for inputNode in range(g.inputs()):
                if g.input(inputNode):
                    realInputCount += 1
            if realInputCount == g.maxInputs():
                inputNode = nuke.createNode("Input", inpanel=False)
            g.end()
        elif nuke.thisKnob().name() == 'ftrackassettype':
            nodeAssetType = g['ftrackassettype'].value()
            #print nodeAssetType
            assetEnums = ['New']
            if nodeAssetType != '' and nodeAssetType != 'Missmatch inputs':
                # assets = connector.Connector.objectById(os.environ['FTRACK_SHOTID']).getAssets(assetTypes=[nodeAssetType])
                pubto = g.knob('fpubto').getObject().targetTask
                assets = connector.Connector.objectById(pubto).getAssets(assetTypes=[nodeAssetType])
                assetEnums = assetEnums + [HelpFunctions.safeString(x.getName()) for x in assets]
                g['fassetnameexisting'].setValues(assetEnums)


def addFtrackComponentField(n=None):
    if not n:
        n = nuke.thisNode()
    tab = nuke.Tab_Knob('ftracktab', 'ftrack')
    n.addKnob(tab)

    componentName = ''
    if n.Class() in ['Write', 'Read']:
        componentName = 'sequence'
    elif n.Class() in ['WriteGeo']:
        componentName = 'alembic'
    componentKnob = nuke.String_Knob('fcompname', 'componentName', componentName)
    n.addKnob(componentKnob)


def ftrackPublishHieroInit():
    g = nuke.thisNode()
    if 'fpubinit' in g.knobs():
        if g.knob('fpubinit').value() == "False":
            g.removeKnob(g.knob('fpubinit'))
            g.removeKnob(g.knob('User'))
            addPublishKnobsToGroupNode(g)


def getHeaderKnob(node):
    header_object = node.knobs().get('fheader').getObject()
    if header_object:
        return header_object.headerWidget
