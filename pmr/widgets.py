#!python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QHeaderView, QTreeWidget

# Copied from https://stackoverflow.com/questions/6625188/qtreeview-horizontal-scrollbar-problems
class QScrollableTreeWidget(QTreeWidget):
    '''
    :mod:`QTreeWidget`-based widget marginally improving upon the stock
    :mod:`QTreeWidget` functionality.

    This application-specific widget augments the stock :class:`QTreeWidget`
    with additional support for horizontal scrollbars, automatically displaying
    horizontal scrollbars for all columns whose content exceeds that column's
    width. For unknown reasons, the stock :class:`QTreeWidget` intentionally
    omits this functionality.
    '''

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Header view for this tree.
        header_view = self.header()

        # To display a horizontal scrollbar instead of an ellipse when resizing
        # a column smaller than its content, resize that column's section to its
        # optimal size. For further details, see the following FAQ entry:
        #     https://wiki.qt.io/Technical_FAQ#How_can_I_ensure_that_a_horizontal_scrollbar_and_not_an_ellipse_shows_up_when_resizing_a_column_smaller_than_its_content_in_a_QTreeView_.3F
        header_view.setSectionResizeMode(QHeaderView.ResizeToContents)

        # By default, all trees contain only one column. Under the safe
        # assumption this tree will continue to contain only one column, prevent
        # this column's content from automatically resizing to the width of the
        # viewport rather than this column's section (as requested by the prior
        # call). This unfortunate default overrides that request.
        header_view.setStretchLastSection(False)

    def setColumnCount(self, column_count: int) -> None:
        super().setColumnCount(column_count)

        # If this tree now contains more than one column, permit the last such
        # column's content to automatically resize to the width of the viewport.
        if column_count != 1:
            self.header().setStretchLastSection(True)
