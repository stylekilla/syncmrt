from PyQt5 import QtWidgets
import syncmrtWidgets as QsWidgets
from functools import partial
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

	def setPage(self,source,destination):
		# There are multiple image properties pages, so this allows the generic blank one to be set to a specific one.
		# self.stack.page[source] = self.stack.page[destination]
		try:
			self.stack.page[destination] = self.stack.page[source]
			return True
		except:
			return False

	def linkPages(self,destination,source):
		# Get the current item.
		currItem = self.list.currentItem()
		# Set the image properties to xray or ct as needed.
		# Source is where it came from, destination is where it's going to.
		if source == 'X-RAY': source = 'xrayImageProperties'
		elif source == 'CT': source = 'ctImageProperties'
		# Set the page and see if it passed.
		if self.setPage(source,destination):
		# If image prop is open, set new widget.
			if (self.list.currentItem() == self.list.page[destination]) & (self.stack.parent.isVisible() == True):
				self.stack.setCurrentIndex(self.stack.page[source]) 
			elif self.list.currentItem() == self.list.page[destination]:
				# If it is not open, set it without showing it.
				self.stack.setCurrentIndex(self.stack.page[source]) 
				self.stack.parent.setVisible(False)
			else:
				pass


	def previousStack(self,current,previous):
		'''Keep track of the last item pressed when an item is clicked.'''
		self._previousListItem = previous
		# self.showStack(current)

	def showStack(self,listWidgetItem):
		'''Show workspace based on item clicked/called item. If the active one is re-called, toggle the view on/off.'''
		name = None
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