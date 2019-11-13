# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import re

from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


class CommentWidget(QtWidgets.QFrame):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(CommentWidget, self).__init__(parent)

        css_comment_frame = """
        QFrame { 4px; background: #222; color: #FFF; }
        QLabel { padding: 0px; background: none; }
        QTextEdit { border: 3px solid #252525; background: #444; }
        QScrollBar { border: 0;
                     background-color: #333; margin: 1px;}
        QScrollBar::handle {background: #222; border: 1px solid #111;}
        QScrollBar::sub-line, QScrollBar::add-line {height: 0px; width: 0px;}
        """

        self.setMinimumWidth(600)
        # self.setMaximumHeight(100)
        self.setStyleSheet(css_comment_frame)

        layout = QtWidgets.QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel("Comment", self)
        self._edit_field = QtWidgets.QTextEdit(self)
        self._edit_field.setObjectName('ftrack-edit-field')
        self._edit_field.textChanged.connect(self._validate_comment)
        layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, label)
        layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self._edit_field)

    @property
    def text(self):
        return self._edit_field.toPlainText()

    def set_text(self, msg):
        self._edit_field.blockSignals(True)
        self._edit_field.setPlainText(msg)
        self._edit_field.blockSignals(False)

    def setFocus(self):
        self._edit_field.setFocus()

    def _validate_comment(self):
        self._edit_field.blockSignals(True)

        text = self._edit_field.toPlainText()
        good_text = ""
        tmp_cursor = self._edit_field.textCursor()
        position_cursor = tmp_cursor.position()

        pattern_NL = re.compile('\n')
        pattern_Space = re.compile('\s')
        pattern_BadChar = re.compile('[^a-zA-Z0-9\!\?\'\"@£$\,\(\)\&.-]')

        for letter in text:
            if re.search(pattern_NL, letter):
                good_text += letter
            elif re.search(pattern_Space, letter):
                good_text += ' '
            elif re.search(pattern_BadChar, letter) is None:
                good_text += letter

        self._edit_field.setPlainText(good_text)
        length_diff = len(text) - len(good_text)
        tmp_cursor.setPosition(position_cursor - length_diff)
        self._edit_field.setTextCursor(tmp_cursor)

        self._edit_field.blockSignals(False)
        self.changed.emit()
