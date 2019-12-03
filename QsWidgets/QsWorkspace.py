# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
from QsWidgets import QsMpl
from systems.imageGuidance import nonOrthogonalImaging
import numpy as np
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
	newIsocenter = QtCore.pyqtSignal(float,float,float)

	def __init__(self):
		# Start as a blank layout.
		super().__init__(QtCore.Qt.Vertical)
		# Create the tables first.
		self.tableView = (QtWidgets.QTableView(),QtWidgets.QTableView())
		self.tableModel = (QPlotTableModel(),QPlotTableModel())
		# Set the models (Assume model[0] == QPlot.axis[0]).
		self.tableView[0].setModel(self.tableModel[0])
		self.tableView[1].setModel(self.tableModel[1])
		# Create a marker tracker for each plot.
		self.markerTracker = [markerTracker(),markerTracker()]
		self.plot = QsMpl.QPlot()
		# Internal vars.
		self._maxMarkers = 0
		self.plotView = [None,None]
		# Signals.
		for i, model in enumerate(self.tableModel):
			model.itemChanged.connect(partial(self.updateMarkersFromModel,i))
		# Configure table views.
		for i, view in enumerate(self.tableView):
			view.setAlternatingRowColors(True)
			view.setModel(self.tableModel[i])
			view.setColumnWidth(0,200)
			view.verticalHeader().setDefaultSectionSize(20)
			view.verticalHeader().hide()
			view.horizontalHeader().setStretchLastSection(True)
		# Signals.
		self.plot.newMarker.connect(self.addMarker)
		self.plot.clearMarkers.connect(self.clearMarkers)
		self.plot.newIsocenter.connect(self.newIsocenter.emit)

		# Create table widget.
		self.table = QtWidgets.QWidget()
		self.tableLayout = QtWidgets.QHBoxLayout()
		# Populate table widget.
		self.tableLayout.addWidget(self.tableView[0])
		self.tableLayout.addWidget(self.tableView[1])
		self.table.setLayout(self.tableLayout)

		# Add widgets.
		self.addWidget(self.plot)
		self.addWidget(self.table)
		# Set default sizes.
		self.setSizes([300,100])

	def addMarker(self,idx,x,y):
		""" Marker has been added to the plot. """
		# Add it to the marker tracker.
		n, ctd = self.markerTracker[idx].addPoint(x,y)
		# Tell the axes what the centroid is.
		self.plot.setCentroid(idx,ctd)
		# When it's added to the tracker it should be added to the table.
		self.tableModel[idx].addPoint(n,x,y)

	def updateMarkersFromModel(self,modelIndex):
		""" Takes the table model and updates the markers in the plot accordingly. """
		markers = self.tableModel[modelIndex].getMarkers()
		self.plot.markerUpdate(modelIndex,markers)

	def clearMarkers(self):
		""" Remove all the markers. """
		self.markerTracker[0].clearPoints()
		self.markerTracker[1].clearPoints()
		self.tableModel[0].clearPoints()
		self.tableModel[1].clearPoints()

	def getMarkers(self,raw=False):
		""" Get the marker values from each plot, adjusted for the view of each plot. """
		points = np.zeros((self._maxMarkers,3))
		# Get the raw data and the angles of the image frames.
		markers0 = np.array(self.tableModel[0].getMarkers())
		markers1 = np.array(self.tableModel[1].getMarkers())
		if raw:
			# If we want just the raw points, take them.
			points[:,0] = markers0[:,0]
			# See if we have two sets of points.
			allZeroes = not markers1.any()
			if allZeroes:
				# Only one dataset, take that only.
				points[:,1] = markers0[:,1]
			else:
				# Reconcile both datasets.
				points[:,1] = (markers0[:,1] + markers1[:,1])/2
				points[:,2] = markers1[:,2]
		else:
			# Else, adjust the points for the views.
			theta0 = self.plotView[0]
			theta1 = self.plotView[1]
			# Check to see if there are any markers in the second dataset.
			# allZeroes = not markers1.any()
			allZeroes = (theta1 == None) | (not markers1.any())
			if allZeroes:
				# Only one dataset, take that only.
				points[:,:2] = markers0
			else: 
				# Two datasets, mix them.
				points = nonOrthogonalImaging.calculate(markers0,markers1,theta0,theta1)

		return points

	def updateIsocenter(self,x,y,z):
		"""
		Update the patient isocenter in the plot environment.

		Parameters
		----------
		x : float
			The X value of the isocenter.
		y : float
			The Y value of the isocenter.
		z : float
			The Z value of the isocenter.
		"""
		# Send to plot.
		self.plot.updatePatientIsocenter(x,y,z)

	def getIsocenter(self,raw=False):
		""" 
		Get the isocenter value from each plot, adjusted for the view of each plot. 

		Parameters
		----------
		raw : bool
			If True, grabs the raw points. If False (default), it adjusts the points according to the views of the datasets.

		Returns
		-------
		isocenter : [x,y,z]
			A list of three points representing the cartesian XYZ isocenter.
		"""
		# Get the raw data and the angles of the image frames.
		iso = self.plot.getIsocenter()
		if raw:
			return iso
		else:
			iso0 = [iso[0],iso[1]]
			iso1 = [iso[2],iso[1]]
			theta0 = self.plotView[0]
			theta1 = self.plotView[1]
			# Reconcile the two datasets.
			isocenter = nonOrthogonalImaging.calculate(iso0,iso1,theta0,theta1)

		return isocenter

	def loadImages(self,images):
		"""
		Load up to two images in plot.

		Parameters
		----------
		images : list
			A list containing up to two items of syncmrt.file.image.Image2D
		"""
		# Basic data santisation.
		if len(images) > 2:
			raise Exception("Number of input images must be 1 or 2, instead {} images were received.".format(len(images)))
		# Clear the markers.
		self.clearMarkers()
		# Load the images into the QPlot.
		self.plot.loadImages(images)
		# Iterate over input data.
		for i, image in enumerate(images):
			self.tableModel[i].setLabels(image.view)
			self.plotView[i] = image.imagingAngle

		if i == 0:
			# One plot, hide the table.
			self.tableView[1].setVisible(False)
		else:
			# Two plots, show both.
			self.tableView[1].setVisible(True)

	def clearPlot(self):
		"""
		Clears the plot environment of all data.
		"""
		self.plot.clear()

	def pickIsocenter(self):
		""" Trigger the pick isocenter tool. """
		self.plot.pickIsocenter()

	def getPlotHistogram(self):
		""" 
		Get the plot histograms. 

		Returns
		-------
			histograms : list
				A list of all the histograms.
		"""
		return self.plot.getHistograms()

	def reset(self):
		"""
		Reset the plot environment (remove images, markers etc.)
		"""
		pass

	def setMaskSize(self,size):
		""" Set each plot's mask size. """
		self.plot.setMaskSize(size)

	def set(self,setting,value):
		if setting == 'maxMarkers':
			self._maxMarkers = value
			self.tableModel[0].setMarkerRows(value)
			self.tableModel[1].setMarkerRows(value)
			self.plot.markersMaximum = value
		elif setting == 'patIso':
			self.plot.patientIsocenter = value
		elif setting == 'patMask':
			# Only show the mask in the first view. There is none to show in the second view.
			self.plot.mask = value
		elif setting == 'markerCtd':
			self.plot.ctd = value
		else:
			pass

	def toggleOverlay(self,overlay,state):
		""" Toggle an overlay on or off. """
		self.plot.toggleOverlay(overlay,state)

	def toggleImageSettings(self):
		self.toggleSettings.emit()

class markerTracker:
	""" A simple point tracker class. """
	def __init__(self):
		# X and Y points to track.
		self.x = []
		self.y = []

	def addPoint(self,x,y):
		""" Add the points to the list. """
		# Append the points.
		self.x.append(x)
		self.y.append(y)
		# Calculate the new centroid.
		self.ctd = (np.sum(self.x)/len(self.x), np.sum(self.y)/len(self.y))
		# Return the number of points currently in the list.
		return len(self.x), self.ctd

	def clearPoints(self):
		""" Clear the points. """
		self.x = []
		self.y = []

	def getPoints(self):
		return (x,y)

	def getCentroid(self):
		return self.ctd

	def count(self):
		return len(x)


class QPlotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	# itemChanged = QtCore.pyqtSignal(list)
	# centroidChanged = QtCore.pyqtSignal(list)

	def __init__(self,labels={}):
		# Initialise the standard item model first.
		super().__init__()
		# Set column and row count.
		self.setColumnCount(3)
		self.setMarkerRows(0)
		self.items = {}
		self.setHorizontalHeaderLabels([
			labels.get('title','Undefined'),
			labels.get('xLabel','Horizontal'),
			labels.get('yLabel','Vertical')
		])
		# Math stuff. Tracking points.
		self.points = []
		self.ctd = None

	def count(self):
		"""
		Return the number of points currently in the table.

		Returns
		-------
			int : number of points
		"""
		return len(self.points)

	def addPoint(self,row,x,y):
		"""
		Write a point to the model. This is specified by the point number (identifier), and it's x and y coord.
		"""
		# Block signals until we are done.
		self.blockSignals(True)
		# Create an item for marker name.
		column0 = QtGui.QStandardItem()
		column0.setData('Marker '+str(row),QtCore.Qt.DisplayRole)
		column0.setEditable(False)
		# Create an item for marker x pos.
		column1 = QtGui.QStandardItem()
		column1.setData(float(x),QtCore.Qt.DisplayRole)
		# Create an item for marker y pos.
		column2 = QtGui.QStandardItem()
		column2.setData(float(y),QtCore.Qt.DisplayRole)
		# Keep a reference to the items.
		self.items[row-1] = [column1, column2]
		# Make the data row.
		data = [column0, column1, column2]
		# Set the data in the table model.
		for index, element in enumerate(data):
			self.setItem(row-1,index,element)
		# Tell the view that we changed the model.
		self.blockSignals(False)
		self.layoutChanged.emit()

	def getMarkers(self):
		""" Return the points held by the table. """
		pointsList = []
		self.rowCount()
		for i in range(self.rowCount()):
			try:
				x = float(self.item(i,1).text())
				y = float(self.item(i,2).text())
				pointsList.append([x,y])
			except:
				pass
		return pointsList

	def setMarkerRows(self,rows):
		""" Defines the maximum number of rows according to the maximum number of markers. """
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
			'View: '+labels.get('title','Undefined'),
			'Horizontal',
			'Vertical'
		])

	def clearPoints(self):
		""" Clear the model of all it's rows and re-add empty rows in their place. """
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(currentRows)