# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

# Setup logging for ftrack.
# TODO: Check with The Foundry if there is any better way to customise logging.
from . import logging as _logging
_logging.setup()

import hiero
from .plugin import Plugin as _Plugin
plugin = _Plugin()
