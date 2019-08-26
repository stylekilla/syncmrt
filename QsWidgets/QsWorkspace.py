# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
from QsWidgets import QsMpl
# Matplotlib widgets.
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import logging
from functools import partial

# For PyInstaller:
import sys, os
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
image_path = application_path+'synctools/QsWidgets/QsMpl/images/'

class QPlotEnvironment(QtWidgets.QSplitter):
	"""
	An advanced widget specifically designed for plotting with MatPlotLib in Qt5.
	It has a navbar, plot and table.
	"""
	toggleSettings = QtCore.pyqtSignal()
	subplotAdded = QtCore.pyqtSignal(int)
	subplotRemoved = QtCore.pyqtSignal(int)

	def __init__(self):
		# Start as a blank layout.
		super().__init__(QtCore.Qt.Horizontal)
		# self.layout = QtWidgets.QHBoxLayout()
		# self.layout.setContentsMargins(0,0,0,0)
		# self.setLayout(self.layout)
		# Empty lists.
		self.navbar = []
		self.plot = []
		self.tableModel = []
		self.tableView = []
		self.histogram = []
		# Internal vars.
		self._maxMarkers = 0

	def loadImages(self,image):
		'''Load up to 2 images and send to subplots.'''
		logging.debug("Loading image set {}.".format(image))
		if self.count() != len(image):
			self.createSubplots(len(image))
		for i in range(len(image)):
			self.plot[i].imageLoad(image[i].pixelArray,image[i].extent)
			self.plot[i]._imagingAngle = image[i].imagingAngle
			self.tableModel[i].setLabels(image[i].view)
			self.histogram[i].setTitle('View: '+image[i].view['title'])
			self.histogram[i].setData(image[i].pixelArray)
			self.histogram[i].setEnabled(True)

	def createSubplots(self,amount):
		nplots = self.count()
		# Data length check.
		if amount == 0:
			self.reset()
			return
		elif amount not in {1,2}:
			logging.critical('Attempting to create {} subplots. Only 1 or 2 subplots is supported.'.format(amount))
			return
		# Find out how many plots are needed.
		difference = nplots-amount
		if difference < 0:
			logging.info("Creating additional subplots.")
			self.addSubplot(difference*-1)
		elif difference > 0:
			logging.info("Removing excess subplots.")
			self.removeSubplot(difference)
		else:
			pass

	def addSubplot(self,amount):
		if amount not in {1,2}:
			logging.critical('Can only create a maximum of 2 subplots, attempted to create {}.'.format(len(image)))
		for i in range(amount):
			subplotWidget = QtWidgets.QWidget()
			# A table model is required for the table view.
			self.tableModel.append(QPlotTableModel())
			self.tableView.append(QtWidgets.QTableView())
			# The plot needs the table model for data.
			self.plot.append(QsMpl.QPlot(self.tableModel[-1]))
			# On model change update the plot markers.
			self.tableModel[-1].itemChanged.connect(self.plot[-1].markerUpdate)
			# The navbar needs the plot widget and the parent widget.
			self.navbar.append(QNavigationBar(self.plot[-1].canvas))
			self.navbar[-1].toggleImageSettings.connect(self.toggleImageSettings)
			self.navbar[-1].clearAll.connect(self.plot[-1].removeMarker)
			# Configure table view.
			self.tableView[-1].setAlternatingRowColors(True)
			self.tableView[-1].setModel(self.tableModel[-1])
			self.tableView[-1].setColumnWidth(0,200)
			self.tableView[-1].verticalHeader().setDefaultSectionSize(20)
			self.tableView[-1].verticalHeader().hide()
			self.tableView[-1].horizontalHeader().setStretchLastSection(True)
			# Create layout for subplot widget.
			subplotLayout = QtWidgets.QVBoxLayout()
			subplotLayout.setContentsMargins(0,0,0,0)
			# Add widgets to layout.
			subplotLayout.addWidget(self.navbar[-1])
			# QSplitter for resizing between plot and table.
			splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
			splitter.addWidget(self.plot[-1].canvas)
			splitter.addWidget(self.tableView[-1])
			# Set stretch factors.
			splitter.setSizes([200,100])
			# Add splitter to layout.
			subplotLayout.addWidget(splitter)
			# Add layout to widget.
			subplotWidget.setLayout(subplotLayout)
			# Add widget to plotenvironment.
			# self.layout.addWidget(subplotWidget)
			self.addWidget(subplotWidget)
			# Create a histogram widget for the plot.
			self.histogram.append(QsMpl.QHistogramWindow())
			self.histogram[-1].setEnabled(False)
			# When histogram changed then update plot.
			self.histogram[-1].windowUpdated.connect(partial(self.plot[-1].applyWindow))
			# Send a signal to say a subplot was added.
			self.set('maxMarkers',self._maxMarkers)
			# self.subplotAdded.emit(self.count())
		# Set max markers.

	def removeSubplot(self,amount):
		# Take the layout item, get the widget of the item and remove it.
		# item = self.layout.takeAt(self.layout.count()-1)
		# item.widget().setParent(None)
		# Remove the widgets from the lists.
		for i in range(amount):
			# Remove the widget.
			count = self.count()
			self.widget(self.count()-1).setParent(None)
			self.subplotRemoved.emit(count)
			# Delete the widgets from the list.
			del(self.navbar[-1])
			del(self.plot[-1])
			del(self.tableModel[-1])
			del(self.tableView[-1])
			# Remove the histogram.
			self.histogram[-1].setParent(None)
			del(self.histogram[-1])

	def getPlotHistogram(self):
		return self.histogram

	def reset(self):
		for i in reversed(range(self.count())): 
			self.widget(i).setParent(None)
		self.navbar = []
		self.plot = []
		self.tableModel = []
		self.tableView = []
		self.histogram = []

	def setRadiographMode(self,mode):
		'''Set radiograph mode to 'sum' or 'max.''' 
		self.plot[i]._radiographMode = mode

	def set(self,setting,value):
		if setting == 'maxMarkers':
			self._maxMarkers = value
			for i in range(len(self.plot)):
				self.plot[i].markerModel.setMarkerRows(value)
				self.plot[i].markersMaximum = value
		elif setting == 'patIso':
			self.plot[0].patientIsocenter = [value[1],value[0]]
			self.plot[1].patientIsocenter = [value[2],value[0]]
		elif setting == 'patMask':
			# Only show the mask in the first view. There is none to show in the second view.
			for i in range(len(self.plot)):
				self.plot[i].mask = value
		elif setting == 'markerCtd':
			self.plot[0].ctd = [value[1],value[0]]
			self.plot[1].ctd = [value[2],value[0]]
		else:
			pass

	def toggleOverlay(self,overlay,state):
		for i in range(len(self.plot)):
			self.plot[i].toggleOverlay(overlay,state)

	def toggleImageSettings(self):
		self.toggleSettings.emit()

	def updateIsocenter(self,x,y,z):
		""" Update the isocenter in each plot. """
		for i in range(len(self.plot)):
			if i == 0: self.plot[i].updatePatientIsocenter(x,y)
			elif i == 1: self.plot[i].updatePatientIsocenter(z,y)

	def resetWidget(self):
		# Removes all widgets and items associated with the layout. Essentially creates a new one.
		self.__init__()

class QPlotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they 
	are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	def __init__(self,labels={}):
		# Initialise the standard item model first.
		super().__init__()
		# Set column and row count.
		self.setColumnCount(3)
		self.setMarkerRows(0)
		self.items = {}
		self._locked = False
		self.setHorizontalHeaderLabels([
			labels.get('title','-'),
			labels.get('xLabel','-'),
			labels.get('yLabel','-')
		])

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

	def setLabels(self,labels):
		# Set the column header labels.
		self.setHorizontalHeaderLabels([
			'View: '+labels.get('title','Unknown?'),
			labels.get('xLabel','X?'),
			labels.get('yLabel','Y?')
		])

	def clearMarkers(self,newRows):
		'''Clear the model of all it's rows and re-add empty rows in their place.'''
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(newRows)

class QNavigationBar(NavigationToolbar2QT):
	clearAll = QtCore.pyqtSignal()
	toggleImageSettings = QtCore.pyqtSignal()

	def __init__(self,canvas):
		self.toolitems = (
				('Home', 'Reset original view', 'home', 'home'),
				('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
				('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
				('Pick', 'Click to select marker', 'help', 'pick'),
				('Clear', 'Clear all the markers', 'help', 'clear'),
				# ('Settings', 'Show the image settings', 'help', 'settings'),
				(None, None, None, None),
				('Save', 'Save the figure', 'filesave', 'save_figure'),
			)
		self.basedir = image_path
		NavigationToolbar2QT.__init__(self,canvas,parent=None)
		self.canvas = canvas

		# actions = self.findChildren(QtWidgets.QAction)
		# toolsBlacklist = ['Customize','Forward','Back','Subplots','Save']
		# toolsBlacklist = ['Customize','Forward','Back','Subplots']
		# for a in actions:
			# if a.text() in toolsBlacklist:
				# self.removeAction(a)

		# Remove the labels (x,y,val).
		self.locLabel.deleteLater()
		# Add my own actions to the toolbar.
		# self._actions['pick'] = self.addAction('pick')
		# self._actions['pick'].setCheckable(True)
		# self._actions['clear'] = self.addAction('clear')
		# self._actions['settings'] = self.addAction('settings')
		# self.insertSeparator(self._actions['settings'])

		# Pick should disable when ZOOM or PAN is enabled.

	def _update_buttons_checked(self):
		# sync button checkstates to match active mode
		self._actions['pan'].setChecked(self._active == 'PAN')
		self._actions['zoom'].setChecked(self._active == 'ZOOM')
		self._actions['pick'].setChecked(self._active == 'PICK')
		if self._active == 'PICK':
			self.canvas._pickerActive = True
		else:
			self.canvas._pickerActive = False

	def set_message(self, s):
		# Set empty message method to stop it from trying to use self.locLabel
		pass 

	def pick(self,*args):
		if self._active == 'PICK':
			self._active = None
		else:
			self._active = 'PICK'
		if self._idPress is not None:
			self._idPress = self.canvas.mpl_disconnect(self._idPress)
			self.mode = ''
		if self._active:
			# Set the cursor.
			self.canvas._pickerActive = True
			self._idPress = self.canvas.mpl_connect(
				'button_press_event', self.press_pick)
			self.canvas.widgetlock(self)
		else:
			self.canvas.widgetlock.release(self)
		self._update_buttons_checked()

	def press_pick(self, event):
		"""the press mouse button in pick mode callback"""
		if event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return
		# Press and then release the button.
		self.press(event)
		self.release(event)

	def clear(self):
		self.clearAll.emit()
	
	def settings(self):
		self.toggleImageSettings.emit()