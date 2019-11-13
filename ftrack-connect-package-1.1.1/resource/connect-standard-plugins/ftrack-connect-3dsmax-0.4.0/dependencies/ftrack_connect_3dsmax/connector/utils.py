# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import MaxPlus

def evalMAXScript(cmd):
    '''Evaluate a string using MAXScript.'''
    return MaxPlus.Core.EvalMAXScript(cmd)

def getUniqueNodeName(nodeName):
    '''Return a unique scene name for the given *nodeName*'''

    # Max starts naming objects from 001.
    i = 1
    nodeFmtString = nodeName + '%03d'
    while True:
        uniqueNodeName = nodeFmtString % i
        if not MaxPlus.INode.GetINodeByName(uniqueNodeName):
            return uniqueNodeName

        i = i + 1

    return uniqueNodeName

def getTimeRange():
    start = evalMAXScript('animationRange.start')
    end = evalMAXScript('animationRange.end')
    return (start, end)

def mergeMaxFile(filePath):
    '''Import a Max scene into the current scene.'''
    return evalMAXScript(
        'mergemaxfile @"{0}" #autoRenameDups #neverReparent #select'.format(filePath))

def selectAll():
    evalMAXScript('select $*')

def deselectAll():
    MaxPlus.SelectionManager.ClearNodeSelection()

def saveSelection():
    return MaxPlus.SelectionManager.GetNodes()

def restoreSelection(savedSelection):
    MaxPlus.SelectionManager.SelectNodes(savedSelection)

def addNodeToSelection(node):
    '''Add a node to the current selection.'''
    MaxPlus.SelectionManager.SelectNode(node, False)

def selectionEmpty():
    return MaxPlus.SelectionManager.GetNodes().GetCount() == 0

def selectOnlyCameras():
    cmd ='''
    selectedCameras = #()
    for obj in selection do (
        if SuperClassOf obj == camera do (
            append selectedCameras obj
        )
    )
    max select none
    select selectedCameras
    '''
    evalMAXScript(cmd)

def createSelectionSet(setName):
    '''Create a new selection set containing the selected nodes.'''
    evalMAXScript('selectionSets["{0}"] = selection'.format(setName))

def _collectChildrenNodes(n, nodes):
	for c in n.Children:
		_collectChildrenNodes(c, nodes)

	nodes.append(n)

def collectChildrenNodes(node):
    '''Return a list of all children of a node.'''
    childNodes = []
    for c in node.Children:
        _collectChildrenNodes(c, childNodes)

    return childNodes

def deleteAllChildren(node):
    '''Delete all children nodes of a node.'''
    allChildren = collectChildrenNodes(node)
    nodesToDelete = MaxPlus.INodeTab()
    for node in allChildren:
        nodesToDelete.Append(node)

    node.DeleteNodes(nodesToDelete)

def addAllChildrenToSelection(parentNode):
    '''Add all children of a node to the current selection.'''
    newSel = MaxPlus.SelectionManager.GetNodes()
    nodesToSelect = collectChildrenNodes(parentNode)
    for node in nodesToSelect:
        newSel.Append(node)

    MaxPlus.SelectionManager.SelectNodes(newSel)
