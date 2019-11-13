# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import re
import os

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


class ScriptEditorWidget(QtWidgets.QWidget):
    file_dropped = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ScriptEditorWidget, self).__init__(parent)
        self.file = None
        self.setupUI()

    def setupUI(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._script_editor_tree = ScriptEditorTreeView(self)
        self._script_editor_tree.setSelectionMode(
            QtWidgets.QAbstractItemView.NoSelection)
        self._script_editor_tree.setIndentation(20)
        self._script_editor_tree.setAnimated(True)
        self._script_editor_tree.setHeaderHidden(True)
        self._script_editor_tree.setExpandsOnDoubleClick(True)
        self._script_editor_tree.file_dropped.connect(self._emit_dropped_file)
        main_layout.addWidget(self._script_editor_tree)

        self._option_frame = QtWidgets.QFrame(self)
        option_layout = QtWidgets.QHBoxLayout(self._option_frame)
        option_layout.setContentsMargins(0, 8, 0, 8)
        option_layout.setSpacing(8)
        # filter_lbl = QtGui.QLabel("Filter", self._option_frame)
        css_filter = """
        QLineEdit { border: 1px solid #666;
                    background: #555; color: #000; }
        """

        self._filter_edit = QtWidgets.QLineEdit(self._option_frame)
        self._filter_edit.setMaximumHeight(20)
        # self._filter_edit.setStyleSheet(css_filter)
        self._filter_edit.textChanged.connect(self._set_filter)
        self._previous_occurence = QtWidgets.QPushButton('previous', self._option_frame)
        # self._previous_occurence.setArrowType(QtCore.Qt.LeftArrow)
        # self._previous_occurence.setMaximumWidth(20)
        # self._previous_occurence.setMaximumHeight(20)
        self._next_occurence = QtWidgets.QPushButton('next',self._option_frame)
        # self._next_occurence.setArrowType(QtCore.Qt.RightArrow)
        # self._next_occurence.setMaximumWidth(20)
        # self._next_occurence.setMaximumHeight(20)
        spacer = QtWidgets.QSpacerItem(40, 20,
           QtWidgets.QSizePolicy.Expanding,
           QtWidgets.QSizePolicy.Minimum
        )
        self._collapse_all_btn = QtWidgets.QPushButton(
            "Collapse All", self._option_frame)
        self._collapse_all_btn.setMaximumHeight(20)
        # self._collapse_all_btn.setStyleSheet(css_btn)
        self._collapse_all_btn.clicked.connect(
            self._script_editor_tree.collapseAll)

        self._expand_all_btn = QtWidgets.QPushButton(
            "Expand All", self._option_frame)
        self._expand_all_btn.setMaximumHeight(20)
        # self._expand_all_btn.setStyleSheet(css_btn)
        self._expand_all_btn.clicked.connect(
            self._script_editor_tree.expandAll
        )
        option_layout.addWidget(self._filter_edit)
        option_layout.addWidget(self._previous_occurence)
        option_layout.addWidget(self._next_occurence)
        option_layout.addItem(spacer)
        option_layout.addWidget(self._collapse_all_btn)
        option_layout.addWidget(self._expand_all_btn)

        main_layout.addWidget(self._option_frame)

    def set_file(self, file):
        f = open(file, "r")
        script_str = "".join(f.readlines())
        f.close()

        script = Script(script_str)
        model = ScriptEditorItemModel(script)
        self._script_editor_tree.setModel(model)
        self._script_editor_tree.expandAll()
        self.file = file

    def initiate(self):
        if self._script_editor_tree.model() is not None:
            self._script_editor_tree.model().clear()
        self._set_filter("")
        self.file = None

    def _emit_dropped_file(self, file):
        self.file_dropped.emit(file)

    def set_enabled(self, bool_value):
        self._option_frame.setEnabled(bool_value)

    def _toggle_line_number(self):
        self._script_editor_tree.repaint()

    def _set_filter(self, filter):
        if len(filter) == 0:
            self._script_editor_tree.filter = None
            self._previous_occurence.setEnabled(False)
            self._next_occurence.setEnabled(False)
        else:
            self._script_editor_tree.filter = filter
            self._previous_occurence.setEnabled(True)
            self._next_occurence.setEnabled(True)
        self._script_editor_tree.repaint()

    def _toggle_zoom(self):
        if self.sender() == self._zoom_text_in:
            self._script_editor_tree.font_size += 1
        elif self.sender() == self._zoom_text_out:
            self._script_editor_tree.font_size -= 1
        self._script_editor_tree.repaint()

    @property
    def script_str(self):
        full_lines = []
        if self._script_editor_tree.model() != None:
            for line in self._script_editor_tree.model().script_lines():
                full_lines.append(line.full_line)
        return '\n'.join(full_lines)

    @property
    def script_top_lines(self):
        if self._script_editor_tree.model() != None:
            return self._script_editor_tree.model().script_top_lines()

    @property
    def script_lines(self):
        lines = []
        if self._script_editor_tree.model() != None:
            for line in self._script_editor_tree.model().script_lines():
                lines.append(line)
        return lines


##############################################################################
# SCRIPT LIST
##############################################################################


class Script(list):

    def __init__(self, script_str, tokens_dict=None):
        # curly brackets replacement pattern
        self._bopen_pattern = re.compile("\<\(\$\[BRACKET_OPEN\]\$\)\>")
        self._bclose_pattern = re.compile("\<\(\$\[BRACKET_CLOSE\]\$\)\>")
        self._bopen_replacement = "<($[BRACKET_OPEN]$)>"
        self._bclose_replacement = "<($[BRACKET_CLOSE]$)>"

        self.parse_script_str(script_str, tokens_dict)

    def parse_script_str(self, script_str, tokens_dict):
        # children replacement pattern
        children_pattern = re.compile("\<\(\$\[[0-9]{3}\]\$\)\>")
        self._children_replacement = "<($[%03d]$)>"

        if tokens_dict == None:
            # REGEX to get all the {} tokens
            raw_all_children_pattern = re.compile("\{[^\{\}]*\}")
            # REGEX to get the {} tokens only if it contains at least a "\n"
            # inside
            self._raw_gizmos_children_pattern = re.compile(
                "\{([^\{\}]*\n+[^\{\}]+|[^\{\}]+\n+[^\{\}]*)\}")

            self._tokens_dict = dict()
            self._items_index = 1

            def _replace(match):
                matched = match.group(0)
                if re.search(self._raw_gizmos_children_pattern, matched) != None:
                    replaced = match.expand(
                        self._children_replacement % self._items_index)
                    self._items_index += 1
                    self._tokens_dict[replaced] = matched[1:-1]
                else:
                    replaced = self._bopen_replacement + \
                        matched[1:-1] + self._bclose_replacement
                return replaced

            while re.search(raw_all_children_pattern, script_str) != None:
                script_str = re.sub(
                    raw_all_children_pattern, _replace, script_str)

        else:
            self._tokens_dict = tokens_dict

        tokens = re.findall(children_pattern, script_str)
        if len(tokens) > 0:
            safe_tokens = [
                "\<\(\$\[" + re.sub("[^0-9]", "", t) + "\]\$\)\>" for t in tokens]
            inter_tokens = re.split(
                '|'.join([t for t in safe_tokens]), script_str)

            self._set_lines(inter_tokens[0])
            for i in range(len(tokens)):
                sub_script_list = Script(
                    self._tokens_dict[tokens[i]], self._tokens_dict)
                if len(self) == 0:
                    self.append(ScriptLine(""))
                self[-1].set_children(sub_script_list)
                self._set_lines(inter_tokens[i + 1])

        else:
            self._set_lines(script_str)

    def _set_lines(self, text):
        for element in text.split("\n"):
            if len(element.strip()) > 0:
                element = re.sub(self._bopen_pattern, "{", element)
                element = re.sub(self._bclose_pattern, "}", element)
                self.append(ScriptLine(element))


class ScriptLine(object):

    def __init__(self, line):
        self.full_line = line
        self.clean_line = line.strip()
        self.children = []

        # The line number is set by the model... It's more convenient to let the
        # model deal with the lines counting, because the model has to do fill the
        # item in the correct order whereas the Script list just replace patterns
        # in an arbitrary order. Also because the delegate needs the total number
        # of lines to set the indentation and can access it more easily through the
        # model.
        self.line_number = 0

    def is_layer_addition(self):
        return self.clean_line.startswith('add_layer {')

    def is_comment(self):
        return self.clean_line.startswith('#')

    def stack_pushed(self):
        match = re.search("(?<=push \$)[a-zA-Z0-9]*", self.clean_line)
        if match != None:
            return match.group(0)

    def stack_set(self):
        match = re.search(
            "(?<=set )[a-zA-Z0-9]*(?= \[stack 0\])", self.clean_line)
        if match != None:
            return match.group(0)

    def has_children(self):
        return len(self.children) > 0

    def set_children(self, script_list):
        if len(script_list) > 0:
            # Add the opening bracket to the parent
            self.full_line += " {"
            self.clean_line += " {"

            # Add the content of the group
            for script_line in script_list:
                self.children.append(script_line)

            # Close the bracket..
            end_of_group = re.search("^ *", self.full_line).group() + "}"
            self.children.append(ScriptLine(end_of_group))


##############################################################################
# SCRIPT EDITOR MODELS
##############################################################################


class ScriptEditorItemModel(QtGui.QStandardItemModel):

    def __init__(self, script_list):
        super(ScriptEditorItemModel, self).__init__()
        self.total_line_number = 1
        self._import_lines(script_list)

    def _import_lines(self, script_list, parent=None, level=0):
        index = 0
        for script_line in script_list:
            # Give the correct line number to the script line item
            script_line.line_number = self.total_line_number

            item = ScriptEditorItem(script_line, self.total_line_number, level)
            if parent is None:
                self.setItem(index, item)
            else:
                parent.setChild(index, item)
            self.total_line_number += 1

            if script_line.has_children():
                level_children = level + 1
                self._import_lines(script_line.children, item, level_children)

            index += 1

    def script_lines(self):
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            yield item.script_line
            if item.script_line.has_children():
                for child in item.script_line.children:
                    yield child

    def script_top_lines(self):
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            yield item.script_line


class ScriptEditorItem(QtGui.QStandardItem):

    def __init__(self, script_line, line_number, level):
        super(ScriptEditorItem, self).__init__()
        self.script_line = script_line
        self.line_number = line_number
        self.level = level


##############################################################################
# SCRIPT EDITOR TREE
##############################################################################


class ScriptEditorTreeView(QtWidgets.QTreeView):
    file_dropped = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ScriptEditorTreeView, self).__init__(parent)

        css_tree = """
        QTreeView { background: #444; border: 1px solid #555; }
        QTreeView::branch:has-siblings:!adjoins-item { background: transparent; }
        QTreeView::branch:has-siblings:adjoins-item { background: transparent; }
        QTreeView::branch:!has-children:!has-siblings:adjoins-item { background: transparent; }
        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {
            border-image: none;
            image: url(":ftrack/image/integration/branch-closed");
          }
        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {
            border-image: none;
            image: url(":ftrack/image/integration/branch-open");
          }
        QScrollArea { padding: 3px; border: 0px;
                      background: #252525; }
        QScrollBar { border: 0; background-color: #333;
                     margin: 1px; }
        QScrollBar::handle { background: #222; border: 1px solid #111; }
        QScrollBar::sub-line, QScrollBar::add-line { height: 0px; width: 0px; }
        """
        self.setStyleSheet(css_tree)

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.setDropIndicatorShown(True)

        self._drag_over = False

        # filter to highlight (from the search widget)
        self.filter = None

        self.font_size = 12

        self._delegate = ScriptEditorItemDelegate(self)
        self.setItemDelegate(self._delegate)

    def dropEvent(self, event):
        self._drag_over = False
        if event.mimeData() is None:
            return

        file = event.mimeData().data("text/uri-list")
        if file is None:
            return

        file = file.data().strip()
        if file.startswith("file://"):
            file = file[len("file://"):]

        if os.access(file, os.R_OK) and file.endswith(".gizmo"):
            self.file_dropped.emit(file)

    def dragMoveEvent(self, event):
        event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData() is None:
            event.ignore()
            return

        file = event.mimeData().data("text/uri-list")
        if file is None:
            event.ignore()
            return

        file = file.data().strip()
        if file.startswith("file://"):
            file = file[len("file://"):]

        if os.access(file, os.R_OK) and file.endswith(".gizmo"):
            self._drag_over = True
            event.accept()
            self.repaint()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        return super(ScriptEditorTreeView, self).dragLeaveEvent(event)

    def set_filter(self, filter):
        ''' Set a element to highlight in the tree.
        '''
        if len(str(filter)) == 0:
            self.filter = None
        else:
            self.filter = str(filter)

    def drawBranches(self, painter, rect, index):
        ''' Move the branches on the right to let the space for the line number display.
        '''
        rect.setRight(
                rect.right() + self._delegate.line_numbers_indent + 10
        )
        super(ScriptEditorTreeView, self).drawBranches(painter, rect, index)

    def paintEvent(self, event):
        super(ScriptEditorTreeView, self).paintEvent(event)
        if self._drag_over:
            painter = QtGui.QPainter(self.viewport())
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            rect = self.rect()

            painter.save()

            painter.setBrush(QtGui.QColor(255, 230, 183, 50))
            painter.drawRect(rect)

            painter.restore()

            painter.setPen(
                QtGui.QPen(QtGui.QColor(255, 230, 183), 5, QtCore.Qt.DashLine))
            painter.drawRoundedRect(rect.adjusted(20, 20, -20, -20), 20, 20)

    def viewportEvent(self, event):
        '''
        Catch the click event to override the item "expand/collapse" function which is
        still called in the place it was before moving the branches in the drawBranches method.

        Catch the double-click event to override the item "expand/collapse" function
        which doesn't work after applying the delegate

        '''
        # Click
        if event.type() == 2 and self.model() != None:
            index = self.indexAt(event.pos())
            item = self.model().itemFromIndex(index)
            if item is None:
                return super(ScriptEditorTreeView, self).viewportEvent(event)

            width_button = 10
            indent = self._delegate.line_numbers_indent + \
                item.level * self.indentation() + 15
            if event.pos().x() > indent and event.pos().x() < indent + width_button:
                if self.isExpanded(index):
                    self.collapse(index)
                else:
                    self.expand(index)
                return True

        # Double Click
        elif event.type() == 4:
            index = self.indexAt(event.pos())
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)
            return True

        # Other events...
        return super(ScriptEditorTreeView, self).viewportEvent(event)


class ScriptEditorItemDelegate(QtWidgets.QStyledItemDelegate):

    ''' Delegate object to repaint the tree widget items
    '''

    def __init__(self, parent=None):
        super(ScriptEditorItemDelegate, self).__init__(parent)
        self.line_numbers_indent = 0

        # Fonts
        self._font_default = QtGui.QFont()
        self._font_default.setWeight(QtGui.QFont.Normal)
        self._font_comment = QtGui.QFont()
        self._font_comment.setWeight(QtGui.QFont.Expanded)
        self._font_has_children = QtGui.QFont()
        self._font_has_children.setWeight(QtGui.QFont.DemiBold)

        # Colors
        self._color_default = QtGui.QColor(210, 210, 210)
        self._color_default_value = QtGui.QColor(255, 167, 21)
        self._color_comment = QtGui.QColor(30, 30, 30)
        self._color_layer_addition = QtGui.QColor(217, 60, 60)
        self._color_stacked_pushed = QtGui.QColor(210, 210, 210)
        self._color_stacked_pushed_value = QtGui.QColor(83, 129, 198)
        self._color_has_children = QtGui.QColor(230, 230, 230)
        self._color_line_number = QtGui.QColor(40, 40, 40)
        self._color_selection = QtGui.QColor(255, 230, 183)

    def paint(self, painter, option, index):
        ''' Override the tree widget draw widget function.
        '''
        rect = option.rect

        tree_widget = self.parent()
        model = tree_widget.model()
        item = index.model().itemFromIndex(index)

        line = item.script_line.clean_line
        line_number = item.line_number
        is_title = item.script_line.has_children()
        is_comment = item.script_line.is_comment()

        color_value = self._color_default_value

        if item.script_line.is_comment():
            font = self._font_comment
            color_default = self._color_comment
            highlight_value = False

        elif item.script_line.is_layer_addition():
            font = self._font_default
            color_default = self._color_layer_addition
            highlight_value = False

        elif (item.script_line.stack_pushed() != None
              or item.script_line.stack_set() != None):
            font = self._font_default
            color_default = self._color_stacked_pushed
            color_value = self._color_stacked_pushed_value
            highlight_value = True

        elif item.script_line.has_children():
            font = self._font_has_children
            color_default = self._color_has_children
            highlight_value = True

        else:
            font = self._font_default
            color_default = self._color_default
            highlight_value = True

        font.setPixelSize(tree_widget.font_size)

        # Get the size of the text according to the chosen font
        fm = QtGui.QFontMetrics(font)

        # Separate the line in a list of tuple (text, color) to draw the text
        if item.script_line.has_children() and not tree_widget.isExpanded(index):
            to_write = [(line + "...}", color_default)]
        else:
            to_write = [(line, color_default)]

        if highlight_value:

            # Try to highlight the name and the value(s) if possible
            tuple_split = item.script_line.clean_line.split(" ", 1)
            if len(tuple_split) > 1:
                if tuple_split[-1].strip() not in ["{", "{...}"]:
                    to_write = [(tuple_split[0], color_default),
                                (tuple_split[-1], color_value)]

        # Set line number indentation
        font_line_number = self._font_default
        font_line_number.setPixelSize(tree_widget.font_size)
        fm_line_number = QtGui.QFontMetrics(font_line_number)

        self.line_numbers_indent = fm_line_number.width(
            str(model.total_line_number))

        # Draw the line number if the option has been set
        painter.setPen(
            QtGui.QPen(self._color_line_number, 1, QtCore.Qt.SolidLine))
        painter.setFont(font_line_number)
        painter.drawText(5, rect.top() + 15, str(item.line_number))
        interval_left = rect.left() + 15 + self.line_numbers_indent

        # Draw the filter if we need one
        if tree_widget.filter != None:
            self._color_selection.setAlpha(70)
            elements = re.findall(tree_widget.filter, line, re.IGNORECASE)
            tmp_line = line
            interval_rect = interval_left
            for element in elements:
                prefix, tmp_line = tmp_line.split(element, 1)
                interval_rect += fm.width(prefix)
                width = fm.width(element)
                rect_selection = QtCore.QRect(
                    interval_rect, rect.y(), width, rect.height())
                painter.setBrush(self._color_selection)
                painter.setPen(
                    QtGui.QPen(self._color_selection, 2, QtCore.Qt.SolidLine))
                painter.drawRect(rect_selection)
                interval_rect += width

        # Draw the text
        for tuple_to_write in to_write:
            text, color = tuple_to_write
            pen = QtGui.QPen(color, 1, QtCore.Qt.SolidLine)
            painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.SolidLine))
            painter.setFont(font)
            painter.drawText(interval_left, rect.top() + 15, text)
            interval_left += fm.width(text) + 5

    def sizeHint(self, option, index):
        tree_widget = self.parent()
        font = self._font_has_children
        font.setPixelSize(tree_widget.font_size)
        fm = QtGui.QFontMetrics(font)
        return QtCore.QSize(200, fm.height() + 5)
