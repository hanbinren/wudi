
import ftrack

import MaxPlus

import ftrack_connect.util
import ftrack_connect.asset_version_scanner

showAssetManagerAction = None
checkForNewAssetsAndRefreshCallbackId = None

def handleScanResult(result, scannedFtrackHelpers):
    '''Handle scan *result*.'''
    message = []
    for partialResult, ftrackHelper in zip(result, scannedFtrackHelpers):
        if partialResult is None:
            # The version was not found on the server, probably because it has
            # been deleted.
            continue

        scanned = partialResult.get('scanned')
        latest = partialResult.get('latest')
        if scanned['version'] != latest['version']:
            message.append(
                '{0} can be updated from v{1} to v{2}'.format(
                    ftrackHelper, scanned['version'], latest['version']
                )
            )

    if message:
        cmd = 'queryBox "{0}. Open Asset Manager?" title:"{1}"'.format(
            '\n'.join(message), "New assets")
        if MaxPlus.Core.EvalMAXScript(cmd).Get():
            showAssetManagerAction.Execute()

def scanForNewAssets():
    '''Check whether there is any new asset.'''
    checkItems = []
    scannedFtrackHelpers = []

    from ftrack_connect_3dsmax.connector.assethelper import getFtrackAssetVersionsInfo
    for (assetId, assetVersion, assetTake, helperNodeName) in getFtrackAssetVersionsInfo():
        checkItems.append({
            'asset_version_id': assetId,
            'component_name': assetTake
        })
        scannedFtrackHelpers.append(helperNodeName)

    if scannedFtrackHelpers:
        import ftrack_api
        session = ftrack_api.Session(
            auto_connect_event_hub=False,
            plugin_paths=None
        )
        scanner = ftrack_connect.asset_version_scanner.Scanner(
            session=session,
            result_handler=(
                lambda result: ftrack_connect.util.invoke_in_main_thread(
                    handleScanResult,
                    result,
                    scannedFtrackHelpers
                )
            )
        )
        scanner.scan(checkItems)

def checkForNewAssetsAndRefreshAssetManager(code=None):
    '''Check whether there is any new asset and
    refresh the asset manager dialog'''
    scanForNewAssets()

    from ftrack_connect.connector import panelcom
    panelComInstance = panelcom.PanelComInstance.instance()
    panelComInstance.refreshListeners()

def registerMaxOpenFileCallbacks(showAssetManagerDialogAction=None):
    '''Register File Open callbacks, used for refreshing the asset manager
    and updating assets.'''
    if showAssetManagerDialogAction:
        global showAssetManagerAction
        showAssetManagerAction = showAssetManagerDialogAction

    global checkForNewAssetsAndRefreshCallbackId
    checkForNewAssetsAndRefreshCallbackId = MaxPlus.NotificationManager.Register(
        MaxPlus.NotificationCodes.FilePostOpenProcess,
        checkForNewAssetsAndRefreshAssetManager)

def unregisterMaxOpenFileCallbacks():
    '''Unregister File Open callbacks'''
    global checkForNewAssetsAndRefreshCallbackId
    if checkForNewAssetsAndRefreshCallbackId:
        MaxPlus.NotificationManager.Unregister(checkForNewAssetsAndRefreshCallbackId)
        checkForNewAssetsAndRefreshCallbackId = None


class DisableOpenFileCallbacks(object):
    '''Class that disables the File Open callbacks and re-enables them when used
    with Python's with statement.
    '''
    def __enter__(self):
        unregisterMaxOpenFileCallbacks()
        return self

    def __exit__(self, type, value, traceback):
        registerMaxOpenFileCallbacks()
