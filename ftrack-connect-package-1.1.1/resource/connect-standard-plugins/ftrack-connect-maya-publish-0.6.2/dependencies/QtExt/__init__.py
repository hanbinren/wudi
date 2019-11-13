# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import logging

logger = logging.getLogger(__name__)

try:
    # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Setup logging.
logger.addHandler(NullHandler())

# Provide default resolution order for Qt
_default_resolution_older_ = os.pathsep.join(['PySide', 'PySide2'])
os.environ.setdefault('QT_PREFERRED_BINDING', _default_resolution_older_)

from Qt import __binding__
import Qt


def is_webwidget_supported():
    '''Return True if either QtWebEngineWidgets or QtWebKitWidgets is available.'''
    try:
        from Qt import QtWebEngineWidgets
        return True
    except ImportError:
        pass

    try:
        from Qt import QtWebKitWidgets
        return True
    except ImportError:
        pass

    return False


class QtExtError(Exception):
    '''Custom QtExt Exception'''


class QtWebCompat(Qt.QtCore.QObject):
    '''Compatibility class container for QtWeb Components'''


class QtWebMeta(type(Qt.QtCore.QObject)):
    '''Base Metaclas for for QtWeb Components'''

    def __new__(cls, name, bases, attrs):

        def get_framework():
            '''Check for available frameworks'''

            try:
                # QtWebKitWidgets -- qt < 5.6 webkit
                from Qt import QtWebKitWidgets

                return {
                    'webkit': True,
                    'webpage': QtWebKitWidgets.QWebPage,
                    'webview': QtWebKitWidgets.QWebView
                }
            except ImportError:
                pass

            try:
                # QtWebEngineWidgets -- qt >= 5.6 webengine
                from Qt import QtWebEngineWidgets

                return {
                    'webkit': False,
                    'webpage': QtWebEngineWidgets.QWebEnginePage,
                    'webview': QtWebEngineWidgets.QWebEngineView
                }

            except ImportError:
                pass

            try:
                # QtWebKit -- qt4 webkit
                from Qt import QtWebKit
                return {
                    'webkit': True,
                    'webpage': QtWebKit.QWebPage,
                    'webview': QtWebKit.QWebView
                }
            except ImportError:
                pass

        framework = get_framework()

        if not framework:
            logger.warning(
                'No QtWebKit / QtWebKitWidgets / QtWebEngineWidgets found'
            )
            return

        module = framework.get(name.lower())
        meta_bases = (module, bases[0])

        instance = super(QtWebMeta, cls).__new__(
            cls, name, meta_bases, attrs
        )

        setattr(
            instance, 'webkit', framework.get('webkit')
        )

        return instance


class WebPage(Qt.QtCore.QObject):
    '''Provide compatiblity access to WebPage setProxy method'''

    __metaclass__ = QtWebMeta

    def setProxy(self, proxy):
        if self.webkit:
            self.networkAccessManager().setProxy(
                proxy
            )

        raise QtExtError(
            'Sorry, WebPage.setProxy is not available.'
        )


class WebView(Qt.QtCore.QObject):
    '''Provide compatiblity access to evaluateJavaScript method'''

    __metaclass__ = QtWebMeta

    def evaluateJavaScript(self, javascript):
        if self.webkit:
            self.page().mainFrame().evaluateJavaScript(
                javascript
            )

        else:
            self.page().evaluateJavaScript(
                javascript
            )


def _pyqt4_():
    import Qt

    # Monkey Patch for forward compatibility
    def setSectionResizeMode(self, *args, **kwargs):
        return self.setResizeMode(*args, **kwargs)

    Qt.QtWidgets.QHeaderView.setSectionResizeMode = setSectionResizeMode

    # Remap QtSortFilterProxyModel from PyQt4.QtGui To PyQt4.QtCore.
    Qt.QtCore.QSortFilterProxyModel = Qt.QtGui.QSortFilterProxyModel

    # Provide a generic QtWebCompat entry for compatibilty purposes
    setattr(Qt, QtWebCompat.__name__, QtWebCompat)
    Qt.QtWebCompat.QWebView = WebView
    Qt.QtWebCompat.QWebPage = WebPage

    # Add new method to check compatiblity
    Qt.is_webwidget_supported = is_webwidget_supported

    return Qt


def _pyqt5_():
    import Qt

    # Monkey Patch for backward compatibility
    def setResizeMode(self, *args, **kwargs):
        return self.setSectionResizeMode(*args, **kwargs)

    Qt.QtWidgets.QHeaderView.setResizeMode = setResizeMode

    # provide mocked UnicodeUTF8 For backward compatibility
    Qt.QtWidgets.QApplication.UnicodeUTF8 = -1

    old_translate_fn = Qt.QtWidgets.QApplication.translate

    def translate(context, key, disambiguation=None, encoding=None, n=0):
        return old_translate_fn(context, key, disambiguation, n)

    Qt.QtWidgets.QApplication.translate = staticmethod(translate)

    # Provide a generic QtWebCompat entry for compatibilty purposes
    setattr(Qt, QtWebCompat.__name__, QtWebCompat)
    Qt.QtWebCompat.QWebView = WebView
    Qt.QtWebCompat.QWebPage = WebPage

    # Add new method to check compatiblity
    Qt.is_webwidget_supported = is_webwidget_supported

    return Qt


def _pyside_():
    import Qt

    # Monkey Patch for forward compatibility
    def setSectionResizeMode(self, *args, **kwargs):
        return self.setResizeMode(*args, **kwargs)

    Qt.QtWidgets.QHeaderView.setSectionResizeMode = setSectionResizeMode

    # Provide a generic QtWebCompat entry for compatibilty purposes
    setattr(Qt, QtWebCompat.__name__, QtWebCompat)
    Qt.QtWebCompat.QWebView = WebView
    Qt.QtWebCompat.QWebPage = WebPage

    # Add new method to check compatiblity
    Qt.is_webwidget_supported = is_webwidget_supported

    return Qt


def _pyside2_():
    import Qt

    # Monkey Patch for backward compatibility
    def setResizeMode(self, *args, **kwargs):
        return self.setSectionResizeMode(*args, **kwargs)

    Qt.QtWidgets.QHeaderView.setResizeMode = setResizeMode

    # provide mocked UnicodeUTF8 For backward compatibility
    Qt.QtWidgets.QApplication.UnicodeUTF8 = -1

    old_translate_fn = Qt.QtWidgets.QApplication.translate

    def translate(context, key, disambiguation=None, encoding=None, n=0):
        return old_translate_fn(context, key, disambiguation, n)

    Qt.QtWidgets.QApplication.translate = staticmethod(translate)

    # Provide a generic QtWebCompat entry for compatibilty purposes
    setattr(Qt, QtWebCompat.__name__, QtWebCompat)
    Qt.QtWebCompat.QWebView = WebView
    Qt.QtWebCompat.QWebPage = WebPage

    # Add new method to check compatiblity
    Qt.is_webwidget_supported = is_webwidget_supported

    return Qt


mapping = {
    'PyQt4': _pyqt4_,
    'PySide': _pyside_,
    'PyQt5': _pyqt5_,
    'PySide2': _pyside2_
}

patch_qt = mapping.get(__binding__)
sys.modules['QtExt'] = patch_qt()
