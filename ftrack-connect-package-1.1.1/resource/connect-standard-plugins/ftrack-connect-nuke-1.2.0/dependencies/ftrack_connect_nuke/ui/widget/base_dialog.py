# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import getpass

import ftrack

from ftrack_connect.ui.widget import header
from ftrack_connect_nuke.ui.controller import Controller
from ftrack_connect.ui.widget import overlay as _overlay
from ftrack_connect.connector import HelpFunctions

import FnAssetAPI
from FnAssetAPI import specifications
from FnAssetAPI.ui.dialogs import TabbedBrowserDialog
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


class FtrackPublishLocale(specifications.LocaleSpecification):
    _type = "ftrack.publish"


class BaseDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, disable_tasks_list=False):
        super(BaseDialog, self).__init__(parent=parent)
        self.current_task = ftrack.Task(
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
        )
        self._tasks_dict = {}
        self.disable_tasks_list = disable_tasks_list
        self._user = ftrack.User(os.getenv('LOGNAME'))
        self.initiate_tasks()

        self._current_scene = None

    def setupUI(self):
        # css_task_global = """
        # QFrame { padding: 3px; border-radius: 4px;
        #          background: #252525; color: #FFF; }
        # """
        self.global_css = """
        QSplitter QFrame {
            padding: 3px;
            border-radius: 1px;
            background: #222;
            color: #FFF;
            font-size: 13px;
        }
        """
        self.base_margin = QtCore.QMargins()
        self.base_margin.setTop(11)
        self.base_margin.setBottom(11)
        self.base_margin.setRight(11)
        self.base_margin.setLeft(11)
        self.container_margin = QtCore.QMargins()
        self.container_margin.setTop(5)
        self.container_margin.setBottom(5)
        self.container_margin.setRight(0)
        self.container_margin.setLeft(0)

        self.global_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.global_layout)
        self.global_layout.setContentsMargins(self.base_margin)
        self.global_layout.setSpacing(0)

        # -- CONTAINERS -- #
        self.header_container = QtWidgets.QFrame(self)
        self.main_container = QtWidgets.QFrame(self)
        self.footer_container = QtWidgets.QFrame(self)

        # self.header_container.setStyleSheet("background-color:black;")
        # self.main_container.setStyleSheet("background-color:grey;")
        # self.footer_container.setStyleSheet("background-color:blue;")

        # -- CONTAINERS LAYOUT -- #
        self.header_container_layout = QtWidgets.QVBoxLayout()
        self.main_container_layout = QtWidgets.QVBoxLayout()
        self.footer_container_layout = QtWidgets.QHBoxLayout()

        self.header_container_layout.setContentsMargins(self.container_margin)
        self.main_container_layout.setContentsMargins(self.container_margin)
        self.footer_container_layout.setContentsMargins(self.container_margin)

        # Main Container wrapper for loading scree
        self.busy_overlay = LoadingOverlay(self)
        self.busy_overlay.hide()

        self.header_container_layout.setAlignment(QtCore.Qt.AlignTop)

        self.footer_container_layout.setAlignment(QtCore.Qt.AlignBottom)
        self.footer_container.setMaximumHeight(50)

        # -- CONTAINER LAYOUT ASSIGN -- #
        self.header_container.setLayout(self.header_container_layout)
        self.main_container.setLayout(self.main_container_layout)
        self.footer_container.setLayout(self.footer_container_layout)

        # -- CONTAINER ASSIGNMENT TO MAIN -- #
        self.global_layout.addWidget(self.header_container)
        self.global_layout.addWidget(self.main_container)
        self.global_layout.addWidget(self.footer_container)

        # -- HEADER -- #
        self.header = header.Header(getpass.getuser(), self.header_container)
        # self.header_container.setStyleSheet("background-color:black;")
        self.header_container_layout.addWidget(self.header)

        # Taks main container
        self.tasks_frame = QtWidgets.QFrame(self.header_container)
        self.tasks_frame_layout = QtWidgets.QHBoxLayout()
        self.tasks_frame.setLayout(self.tasks_frame_layout)

        self.tasks_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_frame_layout.setAlignment(QtCore.Qt.AlignTop)

        self.tasks_main_container = QtWidgets.QWidget(self.tasks_frame)
        self.tasks_main_container_layout = QtWidgets.QVBoxLayout()
        self.tasks_main_container.setLayout(self.tasks_main_container_layout)

        self.tasks_frame_layout.addWidget(self.tasks_main_container)
        self.main_container_layout.addWidget(self.tasks_frame)

        # Task browser widget
        self.tasks_browse_widget = QtWidgets.QWidget(self.tasks_main_container)
        self.tasks_browse_widget_layout = QtWidgets.QHBoxLayout()
        self.tasks_browse_widget.setLayout(self.tasks_browse_widget_layout)
        self.tasks_browse_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.tasks_main_container_layout.addWidget(self.tasks_browse_widget)

        # Task browser - placeholder label
        self.tasks_browse_label = QtWidgets.QLabel(
            'My Tasks',
            self.tasks_browse_widget)
        self.tasks_browse_label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Maximum
        )
        if self.disable_tasks_list:
            self.tasks_browse_label.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self.tasks_browse_label)

        # Task browser - combo
        self.task_label = QtWidgets.QLabel()
        self.task_label.setMinimumHeight(23)
        self.task_label.setText(
            HelpFunctions.getPath(self.current_task, slash=True)
        )
        if self.disable_tasks_list:
            self.task_label.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self.task_label)

        # Task browser - button
        self._tasks_btn = QtWidgets.QPushButton("Browse all tasks...")
        self._tasks_btn.setMinimumWidth(125)
        self._tasks_btn.setMaximumWidth(125)
        if self.disable_tasks_list:
            self._tasks_btn.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self._tasks_btn)

        if self.disable_tasks_list:
            self.tasks_frame.setHidden(True)

        # Footer
        self._save_btn = QtWidgets.QPushButton("Save", self.footer_container)
        self._cancel_btn = QtWidgets.QPushButton("Cancel", self.footer_container)
        self.footer_spacer = QtWidgets.QSpacerItem(
            0,
            0,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )

        self.footer_container_layout.addItem(self.footer_spacer)
        self.footer_container_layout.addWidget(self._cancel_btn)
        self.footer_container_layout.addWidget(self._save_btn)

        self._connect_base_signals()
        self.set_loading_screen(True)

        self.modify_layouts(
            self.tasks_main_container,
            margin=(0, 0, 0, 0)
        )

    def append_css(self, css):
        self.setStyleSheet(self.styleSheet() + css)

    def set_css(self, parent):
        css = '''
        QFrame {
            /*background-color: #444;*/
        }
        QPushButton, QComboBox, QCheckBox {
            color: none;
            background: none;
            background-color: none;
        }
        QTabBar::tab {
            padding: 6px 10px;
            background: #333;
            border-radius: 0px;
        }
        QTabBar::tab:selected {
            background: #333;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:hover {
            background: #444;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
        QLineEdit {
            background-color: none;
            background: none;
        }
        #ftrack-edit-field {
            background-color: #333333;
        }
        QTreeView {
            background: #333333;
            margin: 0px;
            padding-top: 3px;
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
            border-bottom-right-radius: 4px;
            border-bottom-left-radius: 4px;
        }
        QTreeView::item {
            background: none;
        }
        QTreeView::item:selected {
            background: #dde4cb;
        }
        QTreeView::branch:has-siblings:!adjoins-item {
            background: #555;
        }
        QTreeView::branch:has-siblings:adjoins-item {
            background: #555;
        }
        QTreeView::branch:!has-children:!has-siblings:adjoins-item {
            background: #555;
        }
        QTreeView::branch:has-children:!has-siblings:closed {
            background: #555;
        }
        QScrollBar {
            border: 0;
            border-radius: 6px;
            background-color: #333;
            margin: 0px;
        }
        QScrollBar::handle {
            background: #222;
            border: 0px solid #111;
        }
        QScrollBar::sub-line, QScrollBar::add-line {
            height: 0px;
            width: 0px;
        }
        QTabWidget::pane {
            border-top: 1px solid #333;
            top: -2px;
        }
        QGraphicsView {
            background-color: #000;
            border: none;
        }
        '''
        parent.setStyleSheet(css)

    def modify_layouts(self, parent, margin, spacing=None, alignment=None):
        for child in parent.findChildren(QtWidgets.QLayout):
            if spacing:
                child.setSpacing(spacing)
            child.setContentsMargins(*margin)
            if alignment:
                child.setAlignment(alignment)

    def _connect_base_signals(self):
        self._tasks_btn.clicked.connect(self.browse_all_tasks)
        self._save_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)

    def display_tasks_frame(self, toggled):
        self.tasks_frame.setVisible(toggled)
        self._display_tasks_list = toggled

    def _get_tasks(self):
        pass

    def _get_task_parents(self, task):
        task = ftrack.Task(task)
        parents = [t.getName() for t in task.getParents()]
        parents.reverse()
        parents.append(task.getName())
        parents = ' / '.join(parents)
        return parents

    def browse_all_tasks(self):
        session = FnAssetAPI.SessionManager.currentSession()
        context = session.createContext()
        context.access = context.kWrite
        context.locale = FtrackPublishLocale()
        spec = specifications.ImageSpecification()
        task = ftrack.Task(os.environ['FTRACK_TASKID'])
        spec.referenceHint = task.getEntityRef()
        spec.referenceHint = ftrack.Task(os.environ['FTRACK_TASKID']).getEntityRef()
        browser = TabbedBrowserDialog.buildForSession(spec, context)
        browser.setWindowTitle(FnAssetAPI.l("Publish to"))
        browser.setAcceptButtonTitle("Set")
        if not browser.exec_():
            return ''

        targetTask = browser.getSelection()[0]
        task = ftrack.Task(targetTask.split('ftrack://')[-1].split('?')[0])
        self.set_task(task)
        self.update_task_global()

    def update_task_global(self):
        self.update_task()
        if not self.current_task:
            error = "You don't have any task assigned to you."
            self.header.setMessage(error, 'error')
            self.set_empty_task_mode(True)

    def update_task(self):
        self._validate_task()

    def set_enabled(self, bool_result):
        if not self._save_btn.isEnabled() == bool_result:
            self._save_btn.setEnabled(bool_result)

    def set_task(self, task):
        if task is None:
            return
        self.current_task = task
        self._validate_task()
        self.task_label.setText(
            HelpFunctions.getPath(self.current_task, slash=True)
        )

    def initiate_tasks(self):
        self._tasks_dict = dict()

        # self.set_loading_mode(True)

        # Thread that...
        self._controller = Controller(self._get_tasks)
        self._controller.completed.connect(self.set_tasks)
        self._controller.start()

    def set_tasks(self):
        # self.set_loading_mode(False)
        self.update_task_global()
        self.set_loading_screen(False)

    def set_warning(self, msg, detail=None):
        self.header.setMessage(msg + (detail or ''), 'warning')

    def _validate_task(self):
        if not self.current_task:
            return
        user_tasks = [t.getId() for t in self._user.getTasks()]
        task_in_user = self.current_task.getId() in user_tasks

        if not task_in_user:
            warning = (
                'This task is not assigned to you. You might need to ask your '
                'supervisor to assign you to this task before publishing '
                'any asset.'
            )
            self.set_warning(warning)
            return False
        else:
            self.header.dismissMessage()
            self.set_enabled(True)
            return True

    def set_loading_screen(self, active=False):
        self.busy_overlay.setVisible(active)


class LoadingOverlay(_overlay.BusyOverlay):
    '''Custom reimplementation for style purposes'''

    def __init__(self, parent=None):
        '''Initiate and set style sheet.'''
        super(LoadingOverlay, self).__init__(parent=parent)

        self.setStyleSheet('''
            BlockingOverlay {
                background-color: rgba(58, 58, 58, 200);
                border: none;
            }

            BlockingOverlay QFrame#content {
                padding: 0px;
                border: 80px solid transparent;
                background-color: transparent;
                border-image: none;
            }

            BlockingOverlay QLabel {
                background: transparent;
            }
        ''')
