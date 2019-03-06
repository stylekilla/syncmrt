from PyQt5 import QtWidgets, QtGui, QtCore, uic
from functools import partial
import numpy as np

# imports for class plot():
from syncmrtBackend import widgets
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

resourceFilepath = "resources/"


'''
PLOTTING
- class: workEnvironment
- class: plot
- class: navigationBar
- class: plotTableModel
'''

class environment:
	'''Select the work environment out of the stacked widget via the toolbar buttons.'''
	def __init__(self,toolbar,stack):
		self.stack = stack
		self.stackPage = {}
		self.button = {}

		# Dict of workspace widgets.
		self.workspaceWidget = {}

		layout = QtWidgets.QHBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignLeft)
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)

		self.toolbarLayout = layout
		toolbar.setLayout(self.toolbarLayout)

		self.toolbarLayout.addStretch()

	def addWorkspace(self,name,alignment=None):
		'''Add environments to work environment. Can be in form of list.'''
		if name in self.stackPage:
			# Do nothing if it already exists.
			return

		size = QtCore.QSize()
		size.setHeight(30)
		size.setWidth(75)

		if type(name) == list:
			# Enumerate list and add workspaces.
			for index, name in enumerate(name):
				button = QtWidgets.QToolButton()
				button.setText(name)
				button.setFixedSize(size)
				if alignment is not None:
					self.toolbarLayout.addWidget(button)
				else:
					self.toolbarLayout.insertWidget(0,button)
				self.button[name] = button

				page = QtWidgets.QWidget()
				self.stack.addWidget(page)
				self.stackPage[name] = page

				index = self.stack.indexOf(page)
				self.button[name].clicked.connect(partial(self.showWorkspace,index))
		else:
			# Assume singular workspace addition.
			button = QtWidgets.QToolButton()
			button.setText(name)
			button.setFixedSize(size)
			if alignment is not None:
				self.toolbarLayout.addWidget(button)
			else:
				self.toolbarLayout.insertWidget(0,button)
			self.button[name] = button

			page = QtWidgets.QWidget()
			self.stack.addWidget(page)
			self.stackPage[name] = page

			index = self.stack.indexOf(page)
			button.clicked.connect(partial(self.showWorkspace,index))

	def showWorkspace(self,index):
		self.stack.setCurrentIndex(index)

class plot:
	'''
	All things plot. Navbars, plot canvas, table view/model (x2)
	'''
	def __init__(self,widget):
		self.layout = QtWidgets.QGridLayout(widget)
		self.model0 = plotTableModel()
		self.model90 = plotTableModel()
		self.plot0 = widgets.mpl.plot(self.model0)
		self.plot90 = widgets.mpl.plot(self.model90)
		self.nav0 = navigationBar(self.plot0.canvas,widget)
		self.nav90 = navigationBar(self.plot90.canvas,widget)

		self.table0 = QtWidgets.QTableView()
		self.table0.setAlternatingRowColors(True)
		self.table0.setModel(self.model0)
		self.table0.setColumnWidth(0,200)
		self.table0.verticalHeader().setDefaultSectionSize(20)
		self.table0.verticalHeader().hide()
		self.table0.horizontalHeader().setStretchLastSection(True)

		self.table90 = QtWidgets.QTableView()
		self.table90.setAlternatingRowColors(True)
		self.table90.setModel(self.model90)
		self.table90.setColumnWidth(0,200)
		self.table90.verticalHeader().setDefaultSectionSize(20)
		self.table90.verticalHeader().hide()
		self.table90.horizontalHeader().setStretchLastSection(True)

		# Add widgets to layout.
		self.layout.addWidget(self.nav0,0,0)
		self.layout.addWidget(self.plot0.canvas,1,0)
		self.layout.addWidget(self.table0,2,0)
		self.layout.addWidget(self.nav90,0,1)
		self.layout.addWidget(self.plot90.canvas,1,1)
		self.layout.addWidget(self.table90,2,1)

		self.nav0.actionClearMarkers.triggered.connect(partial(self.plot0.markerRemove,-1))
		self.nav0.actionPickMarkers.triggered.connect(self.nav0.pick)
		self.nav90.actionClearMarkers.triggered.connect(partial(self.plot90.markerRemove,-1))
		self.nav90.actionPickMarkers.triggered.connect(self.nav90.pick)

		# Enable point updating through editing table values.
		self.model0.itemChanged.connect(self.plot0.markerUpdate)
		self.model90.itemChanged.connect(self.plot90.markerUpdate)

		# Blank Qt cursor in figures.
		self.plot0.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
		self.plot90.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

	# def setWindows(self,windows):
	# 	'''Set windows for all plots. Take windows as list of lists with upper and lower limits per window [[upper,lower],].'''
	# 	self.plot0.imageWindow(windows)
	# 	self.plot90.imageWindow(windows)

	def setRadiographMode(self,mode):
		'''Set radiograph mode to 'sum' or 'max.''' 
		self.plot0._radiographMode = mode
		self.plot90._radiographMode = mode

	def settings(self,setting,value):
		if setting == 'maxMarkers':
			self.plot0.markerModel.setMarkerRows(value)
			self.plot90.markerModel.setMarkerRows(value)
			self.plot0.markersMaximum = value
			self.plot90.markersMaximum = value
		else:
			pass

	def updatePatientIsocenter(self,newIsoc):
		# Update value in plot.
		self.plot0.patientIsocenter = newIsoc
		self.plot90.patientIsocenter = newIsoc
		# Refresh plot by toggling overlay off/on.
		self.plot0.toggleOverlay(2,False)
		self.plot90.toggleOverlay(2,False)
		self.plot0.toggleOverlay(2,True)
		self.plot90.toggleOverlay(2,True)

class plotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they 
	are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(3)
		self.setMarkerRows(0)
		# self.markers = {}
		self.items = {}
		self._locked = False

		self.setHorizontalHeaderLabels(['#','x','y'])
		# Set column 0 editable(false)

	def addPoint(self,row,x,y):
		'''Write a point to the model. This is specified by the point number (identifier), and it's x and y coord.'''
		self._locked = True
		column0 = QtGui.QStandardItem()
		column0.setData('Marker '+str(row),QtCore.Qt.DisplayRole)
		column0.setEditable(False)

		column1 = QtGui.QStandardItem()
		column1.setData(float(x),QtCore.Qt.DisplayRole)

		column2 = QtGui.QStandardItem()
		column2.setData(float(y),QtCore.Qt.DisplayRole)

		self.items[row-1] = [column1, column2]
		# self.markers[row-1] = [x,y]

		data = [column0, column1, column2]

		for index, element in enumerate(data):
			self.setItem(row-1,index,element)

		self.layoutChanged.emit()
		self._locked = False

	def removePoint(self,index):
		'''Remove a specific point in the list.'''
		pass

	def setMarkerRows(self,rows):
		'''Defines the maximum number of rows according to the maximum number of markers.'''
		current = self.rowCount()
		difference = abs(current-rows)

		if rows < current:
			self.removeRows(current-1-difference, difference)
		elif rows > current:
			self.insertRows(current,difference)
		else:
			pass

		self.layoutChanged.emit()

	def clearMarkers(self,newRows):
		'''Clear the model of all it's rows and re-add empty rows in their place.'''
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(newRows)

class navigationBar(NavigationToolbar2QT):
	def __init__(self,canvas,parent):
		NavigationToolbar2QT.__init__(self,canvas,parent)
		self.canvas = canvas

		actions = self.findChildren(QtWidgets.QAction)
		toolsBlacklist = ['Customize','Forward','Back','Subplots','Save']
		for a in actions:
			if a.text() in toolsBlacklist:
				self.removeAction(a)

		# Remove the labels (x,y,val).
		self.locLabel.deleteLater()

		self.actionPickMarkers = self.addAction('Pick')
		self.actionClearMarkers = self.addAction('Clear')
		self.actionImageSettings = self.addAction('Image Settings')
		self.insertSeparator(self.actionImageSettings)
		self.actionPickMarkers.setCheckable(True)

		# Pick should disable when ZOOM or PAN is enabled.

	def set_message(self, s):
		# Set empty message method to stop it from trying to use self.locLabel
		pass 

	def pick(self):
		if self._active == 'PICK':
			self._active = None
		else:
			self._active = 'PICK'

		if self._idPress is not None:
			self._idPress = self.canvas.mpl_disconnect(self._idPress)
			self.mode = ''

		if self._active:
			self.canvas._pickerActive = True
			self._idPress = self.canvas.mpl_connect(
				'button_press_event', self.press_pick)
			self.canvas.widgetlock(self)
		else:
			self.canvas.widgetlock.release(self)
			self.canvas._pickerActive = False

	def press_pick(self, event):
		"""the press mouse button in pick mode callback"""

		if event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return

		self.press(event)
		self.release(event)

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