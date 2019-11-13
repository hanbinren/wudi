# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import MaxPlus

import math

from .utils import evalMAXScript

def exocortexAlembicAvailable():
    '''Check if Exocortex Crate Alembic plugin is available.
    Currently, we check if the AlembicCameraProperties modifier exists.
    '''
    return evalMAXScript(
        'findItem modifier.classes AlembicCameraProperties != 0').Get()

def exocortexExportAlembic(filePath, options):
    '''Export an Alembic archive.'''
    jobArgs = []

    if options.get('alembicExportMode') == 'Selection':
        jobArgs.append('exportSelected=true')

        # Check if the selection is empty and abort if it is.
        if MaxPlus.SelectionManager.GetNodes().GetCount() == 0:
            raise RuntimeError('Selection is empty')
    else:
        jobArgs.append('exportSelected=false')

    if options.get('alembicNormalsWrite'):
        jobArgs.append('normals=true')
    else:
        jobArgs.append('normals=false')

    if options.get('alembicUVWrite'):
        jobArgs.append('uvs=true')
    else:
        jobArgs.append('uvs=false')

    if options.get('alembicFlattenHierarchy'):
        jobArgs.append('flattenHierarchy=true')
    else:
        jobArgs.append('flattenHierarchy=false')

    if options.get('alembicAnimation'):
        jobArgs.append('in={0}'.format(options['frameStart']))
        jobArgs.append('out={0}'.format(options['frameEnd']))
        steps = options.get('samplesPerFrame', 1.0)
        jobArgs.append('subStep={0}'.format(int(math.ceil(steps))))
    else:
        jobArgs.append('in=0')
        jobArgs.append('out=0')

    argsString = ';'.join(jobArgs)
    cmd = 'ExocortexAlembic.createExportJobs(@"filename={0};{1}")'.format(
        filePath, argsString)

    evalMAXScript(cmd)

def exocortexImportAlembic(filePath, options):
    '''Import an Alembic archive into the current scene.'''
    jobArgs = []

    if options.get('alembicCreateTimeControl'):
        jobArgs.append('loadTimeControl=true')
    else:
        jobArgs.append('loadTimeControl=false')

    jobArgs.append('normals=true')
    jobArgs.append('uvs=true')

    if 'alembicObjectDuplication' in options:
        jobArgs.append('objectDuplication={0}'.format(
            options['alembicObjectDuplication'].lower()))

    if options.get('alembicAttachToExisting'):
        jobArgs.append('attachToExising=true')
    else:
        jobArgs.append('attachToExisting=false')

    # Select all objects in the scene.
    evalMAXScript('select objects')

    argsString = ';'.join(jobArgs)
    cmd = 'ExocortexAlembic.createImportJob(@"filename={0};{1}")'.format(
        filePath, argsString)
    evalMAXScript(cmd)

    # Invert selection.
    evalMAXScript('max select invert')

    # Return the arguments used to import the asset.
    return argsString
