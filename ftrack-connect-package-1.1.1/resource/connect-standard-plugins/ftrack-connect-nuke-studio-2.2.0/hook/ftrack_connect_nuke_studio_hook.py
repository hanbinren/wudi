# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import getpass
import sys
import pprint
import logging
import re

import ftrack_api
import ftrack_connect.application

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_nuke_studio_path = os.path.join(cwd, '..',  'resource')
sys.path.append(sources)

import ftrack_connect_nuke_studio


class LaunchAction(object):
    '''ftrack connect nuke studio discover and launch action.'''

    identifier = 'ftrack-connect-launch-nuke-studio'

    def __init__(self, applicationStore, launcher, session):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        *session* should be an instance of
        :class:`ftrack_api.Session`.

        '''
        super(LaunchAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher
        self.session = session

    def is_valid_selection(self, selection):
        '''Return true if the selection is valid.'''
        if len(selection) != 1:
            return False

        entity = selection[0]
        task = self.session.get('Context', entity['entityId'])

        if task.entity_type != 'Project':
            return False

        return True

    def register(self):
        '''Override register to filter discover actions on logged in user.'''
        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

        self.session.event_hub.subscribe(
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
        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'description': application.get('description', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle launch *event*.'''

        context = event['data'].copy()
        context['source'] = event['source']

        applicationIdentifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            applicationIdentifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect nuke studio',
            version=ftrack_connect_nuke_studio.__version__
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name',
                'variant': 'version',
                'description': 'description',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Nuke.*', 'NukeStudio\d[\w.]+.app'],
                label='Nuke Studio',
                variant='{version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio',
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            # Specify custom expression for Nuke Studio to ensure the complete
            # version number (e.g. 9.0v3) is picked up including any special
            # builds (e.g. 9.0FnAssetAPI.000013a).
            nuke_version_expression = re.compile(
                r'(?P<version>[\d.]+[vabc]+[\dvabc.]*)'
            )

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
                versionExpression=nuke_version_expression,
                label='Nuke Studio',
                variant='{version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio',
                launchArguments=['--studio']
            ))

        elif sys.platform == 'linux2':

            applications.extend(self._searchFilesystem(
                versionExpression=r'Nuke(?P<version>.*)\/.+$',
                expression=['/', 'usr', 'local', 'Nuke.*', 'Nuke\d.+'],
                label='Nuke Studio',
                variant='{version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio',
                launchArguments=['--studio']
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Launch nuke studio.'''

    def __init__(self, applicationStore, session):
        self.session = session
        super(ApplicationLauncher, self).__init__(applicationStore)


    def _getApplicationEnvironment(self, application, context):
        '''Modify and return environment with nuke studio added.'''
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(
            application, context
        )

        application_hooks_path = os.path.abspath(
            os.path.join(
                cwd, '..', 'application_hook'
            )
        )

        environment = ftrack_connect.application.appendPath(
            application_hooks_path, 'FTRACK_EVENT_PLUGIN_PATH', environment
        )

        environment = ftrack_connect.application.appendPath(
            ftrack_connect_nuke_studio_path, 'HIERO_PLUGIN_PATH', environment
        )

        environment = ftrack_connect.application.appendPath(
            sources, 'PYTHONPATH', environment
        )

        entity = context['selection'][0]
        project = self.session.get('Project', entity['entityId'])

        environment['FTRACK_CONTEXTID'] = project['id']

        return environment


def register(session, **kw):
    '''Register hooks for ftrack connect legacy plugins.'''

    logger = logging.getLogger(
        'ftrack_plugin:ftrack_connect_nuke_studio_hook.register'
    )

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    applicationStore = ApplicationStore()

    launcher = ApplicationLauncher(applicationStore, session)

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher, session)
    action.register()
