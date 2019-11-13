# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import MaxPlus

from .assethelper import getAssetFilePath
from .utils import evalMAXScript

def importSceneXRef(filePath, parentHelperNodeName):
    '''Import a Max scene file as a Scene XRef asset and parent it
    under an existing helper node.'''
    cmd = '''
    n = getNodeByName "{0}" exact:true
    scn = xrefs.addNewXRefFile @"{1}"
    scn.parent = n
    '''.format(parentHelperNodeName, filePath)
    evalMAXScript(cmd)

def reimportSceneXRef(ftrackAssetHelper):
    '''Reimport a Scene XRef asset represented by a ftrackAssetHelper object.'''
    importSceneXRef(getAssetFilePath(ftrackAssetHelper), ftrackAssetHelper.Name)

def updateSceneXRef(newFilePath, ftrackAssetHelper):
    '''Update a Scene XRef asset.'''
    cmd = '''
    numSceneRefs = xrefs.getXRefFileCount()
    for i = 1 to numSceneRefs do (
        sceneRef = xrefs.getXrefFile i
        if sceneRef.parent.Name == "{0}" do sceneRef.filename = @"{1}"
    )'''.format(ftrackAssetHelper.Name, newFilePath)
    evalMAXScript(cmd)

def deleteSceneXRef(ftrackAssetHelper):
    '''Delete a Scene XRef asset.'''
    cmd = '''
    numSceneRefs = xrefs.getXRefFileCount()
    for i = 1 to numSceneRefs do (
        sceneRef = xrefs.getXrefFile i
        if sceneRef.parent.Name == "{0}" do (
            delete sceneRef
            exit
        )
    )'''.format(ftrackAssetHelper.Name)
    evalMAXScript(cmd)

def sceneXRefImported(ftrackAssetHelper):
    '''Check if a Scene XRef exists under the ftrackAssetHelper node.'''
    cmd = '''
    result = false
    numSceneRefs = xrefs.getXRefFileCount()
    for i = 1 to numSceneRefs do (
        sceneRef = xrefs.getXrefFile i
        if sceneRef.parent.Name == "{0}" do (
            result = true
        )
    )
    result
    '''.format(ftrackAssetHelper.Name)
    return MaxPlus.Core.EvalMAXScript(cmd).Get()

def importObjXRefs(filePath):
    '''Import all the objects in a Max scene file as Object XRefs and parent
    them under an existing helper node.'''
    cmd = '''
    filename = @"{0}"
    xRefObjs = getMAXFileObjectNames filename
    newObjs =  xrefs.addnewXrefObject filename xRefObjs dupMtlNameAction: #autoRename
    select newObjs
    '''.format(filePath)
    evalMAXScript(cmd)
