from PyQt5 import QtWidgets
import syncmrtWidgets as QsWidgets
import logging

class Sidebar:
	def __init__(self,stackFrame,listFrame):
		# The stack widget.
		self.stack = QsWidgets.QsStackedWidget(stackFrame)
		# List of widgets in the stack.
		self.widget = {}
		# The list widget for the items in the stack.
		self.list = QsWidgets.QsListWidget(listFrame)
		# Set the previous list item to None.
		self._previousListItem = None
		# Signal and slots connections for selecting items in list widget.
		self.list.currentItemChanged.connect(self.previousStack)
		self.list.itemPressed.connect(self.showStack)

	def addPage(self,name,widget,addStack=True,addList=True,before=None,after=None):
		'''Before and after must be names of other pages.'''
		# If no widget assign a blank one.
		if widget == None: widget = QtWidgets.QWidget()
		self.widget[name] = widget
		# Add to list and stack.
		if addStack: self.stack.addPage(name,widget,before=before,after=after)
		if addList: self.list.addPage(name,before=before,after=after)
		# Return the widget if wanted.
		return widget

	def getPage(self,name):
		# Return the widget attached to the page (via the index).
		return self.stack.widget(self.stack.page[name])

	def setPage(self,destination,source):
		# There are multiple image properties pages, so this allows the generic blank one to be set to a specific one.
		self.stack.page[destination] = self.stack.page[source]

	def previousStack(self,current,previous):
		'''Keep track of the last item pressed when an item is clicked.'''
		self._previousListItem = previous
		# self.showStack(current)

	def showStack(self,listWidgetItem):
		'''Show workspace based on item clicked/called item. If the active one is re-called, toggle the view on/off.'''
		name = None
		print(listWidgetItem)
		if type(listWidgetItem) == str:
			# We have a name.
			name = listWidgetItem
		else:
			# Find name in dictionary that matches listWidgetItem.
			for key, value in self.list.page.items():
				if value == listWidgetItem:
					name = key

		if name is None: return

		if self.list.currentItem() == self._previousListItem:
			self.stack.parent.setVisible(not self.stack.parent.isVisible())
		else:
			self.stack.setCurrentIndex(self.stack.page[name])
			self.stack.parent.setVisible(True)
			self._previousListItem = listWidgetItem 

	def getListItem(self,key):
		return self.list.page[key]