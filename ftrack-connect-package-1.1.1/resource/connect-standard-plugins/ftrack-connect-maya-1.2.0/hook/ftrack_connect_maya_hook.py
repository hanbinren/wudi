# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import re
import os
from distutils.version import LooseVersion

import ftrack
import ftrack_connect.application

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_maya_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
sys.path.append(sources)

import ftrack_connect_maya


class LaunchApplicationAction(object):
    '''Discover and launch maya.'''

    identifier = 'ftrack-connect-launch-maya'

    def __init__(self, application_store, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchApplicationAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.application_store = application_store
        self.launcher = launcher

    def is_valid_selection(self, selection):
        '''Return true if the selection is valid.'''
        if (
            len(selection) != 1 or
            selection[0]['entityType'] != 'task'
        ):
            return False

        entity = selection[0]
        task = ftrack.Task(entity['entityId'])

        if task.getObjectType() != 'Task':
            return False

        return True

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.plugin.debug-information',
            self.get_version_information
        )

    def discover(self, event):
        '''Return discovered applications.'''

        if not self.is_valid_selection(
            event['data'].get('selection', [])
        ):
            return

        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            application_identifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'icon': application.get('icon', 'default'),
                'variant': application.get('variant', None),
                'applicationIdentifier': application_identifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        # Prevent further processing by other listeners.
        event.stop()

        if not self.is_valid_selection(
            event['data'].get('selection', [])
        ):
            return

        application_identifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            application_identifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect maya',
            version=ftrack_connect_maya.__version__
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _checkMayaLocation(self):
        prefix = None

        maya_location = os.getenv('MAYA_LOCATION')

        if maya_location and os.path.isdir(maya_location):
            prefix = maya_location.split(os.sep)
            prefix[0] += os.sep

        return prefix

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']
            maya_location = self._checkMayaLocation()
            if maya_location:
                prefix = maya_location

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'maya.+', 'Maya.app'],
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']
            maya_location = self._checkMayaLocation()
            if maya_location:
                prefix = maya_location

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'Maya.+', 'bin', 'maya.exe'],
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        elif 'linux' in sys.platform:
            prefix = ['/', 'usr', 'autodesk', 'maya.+']
            maya_location = self._checkMayaLocation()
            if maya_location:
                prefix = maya_location

            maya_version_expression = re.compile(
                r'maya(?P<version>\d{4})'
            )

            applications.extend(self._searchFilesystem(
                expression=prefix + ['bin', 'maya$'],
                versionExpression=maya_version_expression,
                label='Maya',
                applicationIdentifier='maya_{version}',
                icon='maya',
                variant='{version}'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Custom launcher to modify environment before launch.'''

    def __init__(self, application_store, plugin_path):
        '''.'''
        super(ApplicationLauncher, self).__init__(application_store)

        self.plugin_path = plugin_path

    def _getApplicationEnvironment(
        self, application, context=None
    ):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(application, context)

        entity = context['selection'][0]
        task = ftrack.Task(entity['entityId'])
        taskParent = task.getParent()

        try:
            environment['FS'] = str(int(taskParent.getFrameStart()))
        except Exception:
            environment['FS'] = '1'

        try:
            environment['FE'] = str(int(taskParent.getFrameEnd()))
        except Exception:
            environment['FE'] = '1'

        environment['FTRACK_TASKID'] = task.getId()
        environment['FTRACK_SHOTID'] = task.get('parent_id')

        maya_connect_scripts = os.path.join(self.plugin_path, 'scripts')
        maya_connect_plugins = os.path.join(self.plugin_path, 'plug_ins')

        environment = ftrack_connect.application.appendPath(
            maya_connect_scripts,
            'PYTHONPATH',
            environment
        )
        environment = ftrack_connect.application.appendPath(
            maya_connect_scripts,
            'MAYA_SCRIPT_PATH',
            environment
        )
        environment = ftrack_connect.application.appendPath(
            maya_connect_plugins,
            'MAYA_PLUG_IN_PATH',
            environment
        )

        environment = ftrack_connect.application.appendPath(
            sources,
            'PYTHONPATH',
            environment
        )

        if application['version'] < LooseVersion('2017'):
            environment['QT_PREFERRED_BINDING'] = 'PySide'
        else:
            environment['QT_PREFERRED_BINDING'] = 'PySide2'

        return environment


def register(registry, **kw):
    '''Register hooks.'''
    # Validate that registry is the event handler registry. If not,
    # assume that register is being called to regiter Locations or from a new
    # or incompatible API, and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        return

    # Create store containing applications.
    application_store = ApplicationStore()

    # Create a launcher with the store containing applications.
    launcher = ApplicationLauncher(
        application_store, plugin_path=os.getenv(
            'FTRACK_CONNECT_MAYA_PLUGINS_PATH',
            ftrack_connect_maya_resource_path
        )
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchApplicationAction(application_store, launcher)
    action.register()
