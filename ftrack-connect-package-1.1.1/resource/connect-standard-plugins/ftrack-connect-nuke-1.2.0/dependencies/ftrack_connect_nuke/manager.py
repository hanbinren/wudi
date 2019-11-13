# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from ftrack_connect_foundry import manager

class ManagerInterface(manager.ManagerInterface):
    def initialize(self):
        '''Prepare for interaction with the current host.'''
        super(ManagerInterface, self).initialize()

