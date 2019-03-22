from PyQt5 import QtWidgets, QtGui, QtCore, uic
from functools import partial
import numpy as np

# from widgets import *

class environment:
	'''Select the work environment out of the stacked widget via the toolbar buttons.'''
	def __init__(self,toolbar,stack):
		# Stack widget.
		self.stack = stack
		# Page in stack (stored as index (int)).
		self.page = {}
		# Button for stack page.
		self.button = {}
		# Toolbar Layout.
		layout = QtWidgets.QHBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignLeft)
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		# Add toolbar layout to toolbar.
		self.toolbarLayout = layout
		toolbar.setLayout(self.toolbarLayout)
		# Stretch end of toolbar.
		self.toolbarLayout.addStretch()

	def addPage(self,name,widget,alignment=None):
		'''Add environments to work environment.'''
		if name in self.page:
			# Do nothing if it already exists.
			return
		# Specify the button size.
		size = QtCore.QSize()
		size.setHeight(30)
		size.setWidth(75)

		# if type(name) == str:
		# 	# Single entry as a string, make it a list.
		# 	name = [name]
		# if type(name) != list:
		# 	# Didn't get a list... why?
		# 	print('workspace.environment.addPage: Expected list, but got '+type(name))
		# 	return -1
		# Enumerate list and add workspaces.
		# for index, name in enumerate(name):

		# Create a button.
		button = QtWidgets.QToolButton()
		button.setText(name)
		button.setFixedSize(size)
		# The alignment specifies the left or the right hand side the bar.
		if alignment is not None:
			self.toolbarLayout.addWidget(button)
		else:
			self.toolbarLayout.insertWidget(0,button)
		# Add the button to the workspace.
		self.button[name] = button
		# Add widget to the stack.
		self.stack.addWidget(widget)
		# Get the index of the widget.
		index = self.stack.indexOf(widget)
		# Link the button and page name to the widget position in the stack.
		self.page[name] = index
		self.button[name].clicked.connect(partial(self.showPage,index))
		# Return the widget if wanted.
		return widget

	def showPage(self,index):
		self.stack.setCurrentIndex(index)

'''
PROPERTY MANAGER
- class: propertyManager (QTreeView)
- class: propertyModel (QStandardItemModel)
'''

class propertyManager(QtWidgets.QTreeView):
	'''
	Property manager that stores variable/name for all variables. 
	This is a tree view, the model comes from propertyModel.
	'''
	def __init__(self,frame,model):
		'''Send the frame location to sit the tree in along with the model to populate the tree with.'''
		super().__init__()
		# self.setHeaderLabel('Property Editor')
		self.setMinimumSize(250,800)
		self.setMaximumWidth(600)
		# self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setRootIsDecorated(True)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setModel(model)

		# Set layout and add propertyManager as widget to frame layout.
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		frame.setLayout(layout)

	def toggleFrame(self,frame):
		'''Show/hide frane as requested.'''
		frame.setVisible(not frame.isVisible())

class propertyModel(QtGui.QStandardItemModel):
	'''
	Categories (such as Xray/CT/RtPlan) will be parents of their variables.
	Children will be attached with sub children for broken down variables.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(2)
		self.setRowCount(0)
		self.setHorizontalHeaderLabels(['Property','Value'])
		# Section holds Root (top level) items. Index holds index of all sub-items.
		self.section = {}
		# index[name][variable][sub-variable] returns QModelIndex.
		self.index = {}

	def addSection(self,name):
		'''Add new section to model. Model section introduces list of all items inside.'''
		item = QtGui.QStandardItem()
		item.setData(name,QtCore.Qt.DisplayRole)
		self.appendRow(item)
		self.section[name] = item

		# have a custom delegate for styling...
		self.index[name] = {}
		self.index[name]['root'] = self.indexFromItem(item)

	def addVariable(self,name,variable,value):
		'''Takes single and multiple variables, adds to parent item (name).'''
		if type(value) is not str:
			# Convert to 3dec places, assuming it's a number
			value = np.around(value,decimals=3)

		if type(variable) is list:
			# Multiple Entry
			prop = QtGui.QStandardItem()
			prop.setData(variable[0],QtCore.Qt.DisplayRole)
			prop.setEditable(False)

			descr = QtGui.QStandardItem()
			descr.setEditable(False)

			self.section[name].appendRow([prop,descr])
			self.index[name][variable[0]] = {}
			self.index[name][variable[0]][0] = self.indexFromItem(descr)

			string = ''

			for i in range(len(value)):
				var = QtGui.QStandardItem()
				var.setData(variable[i+1],QtCore.Qt.DisplayRole)
				var.setEditable(False)

				val = QtGui.QStandardItem()
				val.setData(value[i],QtCore.Qt.DisplayRole)
				val.setEditable(True)

				prop.appendRow([var,val])

				string += str(value[i])+','

				self.index[name][variable[0]][variable[i+1]] = self.indexFromItem(val)

			string = string[:-1]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemVariable = QtGui.QStandardItem()
			itemVariable.setData(variable,QtCore.Qt.DisplayRole)
			itemVariable.setEditable(False)

			itemValue = QtGui.QStandardItem()
			itemValue.setData(value,QtCore.Qt.DisplayRole)
			itemValue.setEditable(True)

			self.section[name].appendRow([itemVariable,itemValue])
			self.index[name][variable] = self.indexFromItem(itemValue)

	def updateVariable(self,name,variable,value):
		'''Find variable and update value.'''
		if type(variable) is list:
			# Multiple Entry
			descr = self.itemFromIndex(self.index[name][variable[0]][0])

			# item description
			string = ''

			for i in range(len(value)):
				val = self.itemFromIndex(self.index[name][variable[0]][variable[i+1]])
				val.setData(value[i],QtCore.Qt.DisplayRole)

				string += str(value[i])+','

			string = string[:-1]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemValue = self.itemFromIndex(self.index[name][variable])
			itemValue.setData(value,QtCore.Qt.DisplayRole)

class variablePane:
	'''
	Create variable viewing pane based of a tree widget. You will have collapsible tables to view your information in.
	'''
	def __init__(self,tree):
		'''Main tree Widget settings (sits within frame).'''
		tree.setHeaderLabel('Property Editor')
		tree.setMinimumSize(250,800)
		tree.setMaximumWidth(500)
		tree.setIndentation(0)
		tree.setRootIsDecorated(True)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		tree.setSizePolicy(sizePolicy)

	def addTable(self,tree,name,model):
		'''Add a table of data based of variableModel() class.'''
		category = QtWidgets.QTreeWidgetItem()
		category.setFirstColumnSpanned(True)
		category.setText(0,name)

		child = QtWidgets.QTreeWidgetItem()

		view = QtWidgets.QTreeView()
		view.setModel(model)
		view.setAlternatingRowColors(True)
		view.setMinimumSize(250,0)
		view.setMaximumWidth(500)
		tree.setRootIsDecorated(True)
		view.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		# verticalHeader = QtWidgets.QHeaderView(QtCore.Qt.Vertical)
		# verticalHeader.setDefaultSectionSize(20)
		# view.setVerticalHeader(verticalHeader)
		# view.verticalHeader().hide()

		category.addChild(child)
		tree.addTopLevelItem(category)
		tree.setItemWidget(child,0,view)
		tree.expandItem(category)

class variableModel(QtGui.QStandardItemModel):
	'''
	A model class based of a standard item model that enables you to add single and multiple data points.
	This is used in conjunction with a viewer in the GUI to display the model data.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(2)
		self.setRowCount(0)
		self.setHorizontalHeaderLabels(['Property','Value'])

	def addTableRow(self,variable,value):
		'''Add a table row of data with a label (static) and the value (editable).'''
		# Rows are appended to the end of the table.
		column1 = QtGui.QStandardItem()
		column1.setData(variable,QtCore.Qt.DisplayRole)
		column1.setEditable(False)

		column2 = QtGui.QStandardItem()
		column2.setData(value,QtCore.Qt.DisplayRole)
		column2.setEditable(True)

		self.appendRow([column1, column2])

	def addMultiVariable(self,variable,value):
		'''Add multiple variables to the model, the Variable/Value should be a list of vars.'''
		# Variable should have 1 more entry than value.
		prop = QtGui.QStandardItem()
		prop.setData(variable[0],QtCore.Qt.DisplayRole)
		prop.setEditable(False)

		descr = QtGui.QStandardItem()
		descr.setEditable(False)

		self.appendRow([prop,descr])

		string =''

		for i in range(len(value)):
			var = QtGui.QStandardItem()
			var.setData(variable[i+1],QtCore.Qt.DisplayRole)
			var.setEditable(False)

			val = QtGui.QStandardItem()
			val.setData(value[i],QtCore.Qt.DisplayRole)
			val.setEditable(True)

			prop.appendRow([var,val])

			string += str(value[i])+','

		string = string[:-1]
		descr.setData(string,QtCore.Qt.DisplayRole)

'''
LOGFILES
- class logFile(): Keep a logfile in a class. Execute as self.logFile = logFile().
- method log(logwindow, message, rank): Print logs in the application. Called from the application window.
- class: logFile
- meth: log
'''

class logFile:
	def __init__(self):
		self.message = ()
		self.rank = ()

	def addLog(self,message,rank):
		self.message.append(message)
		self.rank.append(rank)

	def resetLog():
		self.message = ()
		self.rank = ()

def log(window,message,rank):
	if rank == 'error':
		window.setTextColor(QtCore.Qt.red)
		window.setFontWeight(QtGui.QFont.Medium)
		window.append(message)
	elif rank == 'warning':
		window.setTextColor(QtCore.Qt.red)
		window.append(message)
	elif rank == 'event':
		window.setTextColor(QtCore.Qt.black)
		window.append(message)
	else:
		window.setTextColor(QtCore.Qt.gray)
		window.append(message)

'''
WIDGET TOGGLES
- meth: widgetToggle
'''
def widgetToggle(widget):
	'''Set state to opposite of current visibility state.'''
	state = widget.isVisible()
	widget.setVisible(not state)