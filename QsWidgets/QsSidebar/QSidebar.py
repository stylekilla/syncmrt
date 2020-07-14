from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

__all__ = ['QSidebarList','QSidebarTabs']

CSS_STYLESHEET = """
QPushButton#treeHeader {
    background: #1A1A1A;
    border-bottom: 1px;
    border-bottom-color: #FFFFFF;
}

QPushButton#treeHeader:hover {
    background: #3A3A3A;
    border-bottom: 1px;
    border-bottom-color: #FFFFFF;
}

QPushButton#treeHeader:pressed {
    background: #3A3A3A;
    border-bottom: 1px;
    border-bottom-color: #FFFFFF;
}
"""

class QSidebarList(QtWidgets.QTreeWidget):
	def __init__(self,frame):
		super().__init__()
		# Make our stylesheet known to all child widgets.
		self.setStyleSheet(CSS_STYLESHEET)
		# Hide arrows and remove indendations.
		self.setIndentation(0)
		self.setHeaderHidden(True)

		# Install self into frame.
		layout = QtWidgets.QVBoxLayout()
		layout.setSpacing(0)
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(self)
		frame.setLayout(layout)
		# Save the frame for later.
		self.frame = frame

	def addSection(self,title,widget):
		# Add a section to the sidebar.
		# Create placeholders.
		item = QtWidgets.QTreeWidgetItem()
		child = QtWidgets.QTreeWidgetItem()
		# Add placeholders to tree.
		self.addTopLevelItem(item)
		item.addChild(child)

		# Create the header label for the section.
		header = QtWidgets.QPushButton(title)
		header.setObjectName('treeHeader')
		header.setContentsMargins(20,0,0,0)

		# Add the widget to the placeholders (always in column 0).
		self.setItemWidget(item,0,header)
		self.setItemWidget(child,0,widget)

		# Signals and slots.
		header.clicked.connect(partial(self.toggleSection,item))

	def toggleSection(self,item):
		# Expand/Collapse the item as required.
		if item.isExpanded():
			self.collapseItem(item)
		else:
			self.expandItem(item)

	def toggleVisibility(self):
		'''Show/hide frane as requested.'''
		self.frame.setVisible(not self.frame.isVisible())



class QSidebarTabs():
	def __init__(self,frame):
		pass