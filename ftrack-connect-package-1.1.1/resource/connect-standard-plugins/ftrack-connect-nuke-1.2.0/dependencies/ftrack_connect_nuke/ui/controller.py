#!/usr/bin/env python
# -*- coding: utf-8 -*-


import FnAssetAPI
from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets

class WorkerSignal(QtCore.QObject):
    finished = QtCore.Signal(bool, str)


class Worker(QtCore.QRunnable):

    def __init__(self, callback, args, kwargs):
        super(Worker, self).__init__()
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self.signal = WorkerSignal()

    def run(self, *args):
        try:
            self._callback(*self._args, **self._kwargs)
        except Exception as err:
            logging.debug(str(err))
            self.signal.finished.emit(False, str(err))
        else:
            self.signal.finished.emit(True, "")


class Controller(QtCore.QObject):
    completed = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, func, args=None, kwargs=None):
        ''' initiate a new instance '''
        super(Controller, self).__init__()
        args = args or ()
        kwargs = kwargs or {}
        self.worker = Worker(func, args, kwargs)
        self.worker.signal.finished.connect(self._emit_signal)

    def _emit_signal(self, success, error_message):
        if success:
            self.completed.emit()
        else:
            self.error.emit(error_message)

    def start(self):
        QtCore.QThreadPool.globalInstance().start(self.worker)
