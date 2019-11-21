import matplotlib as mpl
mpl.use('Qt5Agg')
mpl.rcParams['toolbar'] = 'toolmanager'
mpl.rcParams['datapath'] = './QsWidgets/QsMpl/mpl-data'

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, FigureManagerQT
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from .tools import ToolPickPoint, ToolPickIso, ToolClearPoints

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from systems.imageGuidance import optimiseFiducials
from functools import partial
import logging

__all__ = ['QPlot','QHistogramWindow']


class QPlot(QtWidgets.QWidget):
	# Signal that emits the index of the axes that (x,y) originate from as well as (x,y) themselves.
	newMarker = QtCore.pyqtSignal(int,float,float)
	# New isocenter.
	newIsocenter = QtCore.pyqtSignal(float,float,float)
	# Clear all the markers.
	clearMarkers = QtCore.pyqtSignal()

	def __init__(self):
		"""
		QPlot is designed to interface with syncmrt.file.image.Image2D objects.

		Parameters
		----------
		tableModel : QsWorkspace.QPlotTableModel object
			A table model must be provided for the storage of marker locations.
		"""
		super().__init__()
		# Create the figure/canvas.
		self.fig = plt.figure(constrained_layout=True)
		self.fig.patch.set_facecolor('#000000')
		# Create the canvas.
		self.canvas = FigureCanvasQTAgg(self.fig)
		# Create the figure manager.
		self.figureManager = FigureManagerQT(self.canvas,1)
		# Create the toolbar manager.
		self.toolbarManager = self.figureManager.toolbar.toolmanager
		# Create the toolbar
		self.toolbar = self.figureManager.toolbar
		# Set up marker tracking.
		self.markers = {}
		self.markersMaximum = 0
		self.ctd = [None,None]

		# Create 2 axes.
		self.ax = self.fig.subplots(1,2,gridspec_kw={'hspace':0,'wspace':0})
		for idx, ax in enumerate(self.ax):
			# Set up tracking for markers in the axes.
			self.markers[ax] = []
			# Set up the axes.
			ax.set_facecolor('#000000')
			ax.title.set_color('#FFFFFF')
			ax.xaxis.label.set_color('#FFFFFF')
			ax.yaxis.label.set_color('#FFFFFF')
			ax.xaxis.set_label_coords(0.5,0.12)
			ax.yaxis.set_label_coords(0.12,0.5)
			ax.xaxis.label.set_size(20)
			ax.yaxis.label.set_size(20)
			ax.yaxis.label.set_rotation(90)
			ax.spines['left'].set_visible(False)
			ax.spines['top'].set_visible(False)
			ax.spines['right'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.tick_params('both',which='both',length=7,width=1,pad=-35,direction='in',colors='#FFFFFF')

		# Remove useless tools.
		items = list(self.toolbar._toolitems.keys())
		for item in items:
			self.toolbar.remove_toolitem(item)

		# Populate the toolbar manager.
		self.toolbarManager.add_tool('home','ToolHome')
		self.toolbarManager.add_tool('zoom','ToolZoom')
		self.toolbarManager.add_tool('pan','ToolPan')
		self.toolbarManager.add_tool('pick',ToolPickPoint)
		self.toolbarManager.add_tool('pickIso',ToolPickIso)
		self.toolbarManager.add_tool('clear',ToolClearPoints)

		# Populate the toolbar.
		self.toolbar.add_tool('home',"default")
		self.toolbar.add_tool('zoom',"default")
		self.toolbar.add_tool('pan',"default")
		self.toolbar.add_tool('pick',"default")
		self.toolbar.add_tool('clear',"default")

		# Get the layout.
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		self.setLayout(layout)

		# Get tools.
		pick = self.toolbarManager.get_tool('pick')
		clear = self.toolbarManager.get_tool('clear')
		pickIso = self.toolbarManager.get_tool('pickIso')

		# Connect tool signals.
		pick.newPoint.connect(self.addMarker)
		clear.clearPoints.connect(self.removeMarkers)
		pickIso.newIsocenter.connect(self._updateIsocenter)

		# Reference to object lists. To reset these, use `del list[:]`.
		self.images = []
		# Refresh the canvas.
		self.canvas.draw()

		# self._radiographMode = 'sum'
		# self._R = np.identity(3)
		# self._imagingAngle = 0
		# self.mask = None
		self.maskSize = 20.0
		self.overlay = {}
		self.machineIsocenter = [0,0,0]
		self.patientIsocenter = [0,0,0]

	def loadImages(self,images):
		"""
		Load up to 2 images into the plot environment.

		Parameters
		----------
		images : list
			A list containing up to two items of syncmrt.file.image.Image2D
		"""
		# Clear the axes.
		for ax in self.ax:
			ax.cla()
		# Remove all previous images.
		for image in self.images:
			image.remove()
		del self.images[:]
		# Remove all previous markers.
		for ax in self.ax:
			del self.markers[ax][:]

		# Create new empty list to store images/axes into.
		self.images = [None]*len(images)
		for i, image in enumerate(images):
			# Load the image. Assumes 2D array, forces 32-bit floats.
			self.images[i] = self.ax[i].imshow(np.array(image.pixelArray,dtype=np.float32), cmap='bone', extent=image.extent)
			# Setup the axes.
			self.ax[i].set_xlim(image.extent[0:2])
			self.ax[i].set_ylim(image.extent[2:4])
			self.ax[i].set_aspect("equal", "datalim")

	def pickIsocenter(self):
		""" Trigger the pick isocenter tool. """
		self.toolbarManager.trigger_tool('pickIso')

	def _updateIsocenter(self,ax,x,y):
		""" Update the patient isocenter with mouse click in plot. """
		# Get the axis index that it originated from.
		index = np.argwhere(self.ax == ax)[0][0]
		if index == 0:
			self.patientIsocenter[0:2] = [x,y]
		elif index == 1:
			self.patientIsocenter[1:3] = [y,x]
		# Update the overlays.
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False) 
			self.toggleOverlay(3,True)
		# Emit the signal to say we have a new iso.
		x,y,z = list(map(float,self.patientIsocenter))
		self.newIsocenter.emit(x,y,z)

	def updatePatientIsocenter(self,x,y,z):
		""" Update the patient isocenter and refresh the overlay. """
		self.patientIsocenter = [x,y,z]
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False) 
			self.toggleOverlay(3,True)

	def applyWindow(self,imin,imax):
		# Set the color scale to match the window.
		if imin < imax:
			for image in self.images:
				image.set_clim(vmin=imin,vmax=imax)
			self.canvas.draw()
		else:
			return

	def addMarker(self,ax,x,y):
		""" Append marker position if it is within the maximum marker limit."""
		n = len(self.markers[ax])
		if n < self.markersMaximum:
			# Plot marker list.
			scatter = ax.scatter(x,y,c='r',marker='+',s=50)
			text = ax.text(x+1,y,n+1,color='r')
			self.markers[ax].append([scatter,text])
			# Refresh views.
			self.canvas.draw()
			# Emit signal for new marker.
			index = np.argwhere(self.ax == ax)[0][0]
			self.newMarker.emit(index,x,y)

	def setCentroid(self,axes,ctd):
		""" Set the centroid of a given axes. """
		self.ctd[axes] = ctd
		# If it's currently an overlay, then toggle it off and on.
		if 'ctd' in self.overlay:
			# Refresh it's position on the screen.
			self.toggleOverlay(0,False)
			self.toggleOverlay(0,True)

	def markerUpdate(self,markers):
		'''Redraw all the markers to their updated positions.'''
		# markers = table.getPoints()
		for ax in self.ax:
			for pos, marker in enumerate(self.markers[ax]):
				# marker[0].remove()
				# marker[1].remove()
				x,y = markers[pos]
				marker[0] = ax.scatter(x,y,c='r',marker='+',s=50)
				marker[1] = ax.text(x+1,y,pos+1,color='r')
		# Refresh the canvas.
		self.canvas.draw()
		# If it's currently an overlay, then toggle it off and on.
		if 'ctd' in self.overlay:
			# Refresh it's position on the screen.
			self.toggleOverlay(0,False)
			self.toggleOverlay(0,True)

	def removeMarkers(self):
		""" Clear the specified marker. Else clear all markers. """
		# Remove stuff from plots.
		for ax in self.ax:
			for pos, marker in enumerate(self.markers[ax]):
				marker[0].remove()
				marker[1].remove()
			# Reset the list to empty.
			self.markers[ax] = []
			# Reset centroid.
			self.ctd = [None,None]
			# If it's currently an overlay, then toggle it off and on.
			if 'ctd' in self.overlay:
				# Refresh it's position on the screen.
				self.toggleOverlay(0,False)
				self.toggleOverlay(0,True)
		# Refresh the canvas.
		self.canvas.draw()
		# Emit the signal to tell everything else we're done.
		self.clearMarkers.emit()

	def clear(self):
		""" Clears all images in the plot. """
		for ax in self.ax:
			ax.cla()

	def updatePatientIsocenter(self,x,y,z):
		""" Update the patient isocenter in 3D. """
		self.patientIsocenter = [x,y,z]
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False)
			self.toggleOverlay(3,True)

	def toggleOverlay(self,overlayType,state=False):
		'''
		Single overlay function with various types.
			- 0: Centroid overaly
			- 1: Machine Isocenter overlay
			- 2: Patient Isocenter overlay
		'''
		if overlayType == 0:
			# Centroid overlay.
			# Remove overlay lines if they exist.
			if 'ctd' in self.overlay:
				if self.overlay['ctd'] is not None:
					for obj in self.overlay['ctd']:
						obj.remove()
				del(self.overlay['ctd'])
			if state is True:
				self.overlay['ctd'] = []
				# Plot overlay scatter points.
				if self.ctd[0] != None: 
					x,y = self.ctd[0]
					self.overlay['ctd'].append(self.ax[0].scatter(x,y,c='b',marker='+',s=50))
					self.overlay['ctd'].append(self.ax[0].text(x+1,y-3,'ctd',color='b'))
				if self.ctd[1] != None: 
					x,y = self.ctd[1]
					self.overlay['ctd'].append(self.ax[1].scatter(x,y,c='b',marker='+',s=50))
					self.overlay['ctd'].append(self.ax[1].text(x+1,y-3,'ctd',color='b'))
			else:
				pass

		elif overlayType == 1:
			# Machine isocenter overlay.
			# Remove overlay lines.
			if 'machIsoH' in self.overlay:
				for obj in self.overlay['machIsoH']:
					obj.remove()
				del(self.overlay['machIsoH'])
			if 'machIsoV' in self.overlay:
				for obj in self.overlay['machIsoV']:
					obj.remove()
				del(self.overlay['machIsoV'])
			if state is True:
				self.overlay['machIsoV'] = []
				self.overlay['machIsoH'] = []
				# Plot overlay lines.
				self.overlay['machIsoV'].append(self.ax[0].axvline(self.machineIsocenter[0],c='r',alpha=0.5))
				self.overlay['machIsoV'].append(self.ax[1].axvline(self.machineIsocenter[2],c='r',alpha=0.5))
				self.overlay['machIsoH'].append(self.ax[0].axhline(self.machineIsocenter[1],c='r',alpha=0.5))
				self.overlay['machIsoH'].append(self.ax[1].axhline(self.machineIsocenter[1],c='r',alpha=0.5))
			else:
				pass
		elif overlayType == 2:
			# Overlay of the patient iso.
			# Remove the overlay lines.
			if 'patIso' in self.overlay:
				for obj in reversed(self.overlay['patIso']):
					obj.remove()
				del(self.overlay['patIso'])
			if state is True:
				self.overlay['patIso'] = []
				# Plot patient iso.
				self.overlay['patIso'].append(self.ax[0].scatter(self.patientIsocenter[0],self.patientIsocenter[1],marker='+',color='y',s=50))
				self.overlay['patIso'].append(self.ax[0].text(self.patientIsocenter[0]+1,self.patientIsocenter[1]+1,'ptv',color='y'))
				self.overlay['patIso'].append(self.ax[1].scatter(self.patientIsocenter[2],self.patientIsocenter[1],marker='+',color='y',s=50))
				self.overlay['patIso'].append(self.ax[1].text(self.patientIsocenter[2]+1,self.patientIsocenter[1]+1,'ptv',color='y'))
			else:
				pass
		elif overlayType == 3:
			# Remove it first if it already exists.
			# if 'beamArea' in self.overlay:
			# 	for obj in reversed(self.overlay['beamArea']):
			# 		obj.remove()
			# 	del(self.overlay['beamArea'])
			# # Beam area overlay.
			# if state is True:
			# 	self.overlay['beamArea'] = []
			# 	# Create new patches.
			# 	_beam = Rectangle((-self.maskSize/2,-self.maskSize/2), self.maskSize, self.maskSize,fc='r',ec='none')
			# 	_ptv = Rectangle((self.patientIsocenter[0]-self.maskSize/2,self.patientIsocenter[1]-self.maskSize/2), self.maskSize, self.maskSize,fc='y',ec='none')
			# 	pc = PatchCollection([_beam,_ptv],alpha=0.2,match_original=True)
			# 	for ax in self.ax:
			# 		self.overlay['beamArea'].append(ax.add_collection(pc))
			# else:
				# pass
			pass
		# Update the canvas.
		self.canvas.draw()

	def setMaskSize(self,size):
		""" Set the mask size and toggle the overlay if it is enabled. """
		self.maskSize = size
		self.toggleOverlay(3,'beamArea' in self.overlay)
		self.toggleOverlay(3,'beamArea' in self.overlay)

	def eventFilter(self,event):
		# If mouse button 1 is clicked (left click).
		if (event.button == 1):
			# event.inaxes is the axes the click originated from
			# event.xdata is the data point w.r.t. the active axes.
			self.markerAdd(event.inaxes,event.xdata,event.ydata)

CENTER_HEADING = """
QGroupBox::title {
	subcontrol-origin: margin;
	subcontrol-position: top;
}
"""

class QHistogramWindow(QtWidgets.QGroupBox):
	windowUpdated = QtCore.pyqtSignal(int,int)

	def __init__(self):
		super().__init__()
		# Create histogram plot.
		self.histogram = Histogram()
		# Sliders.
		self.range = []
		self.range.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
		self.range.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
		# Layout.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(self.histogram.canvas)
		layout.addWidget(self.range[0])
		layout.addWidget(self.range[1])
		# Set layout.
		self.setLayout(layout)
		self.setStyleSheet(CENTER_HEADING)

		# When sliders change update histogram.
		for i in range(len(self.range)):
			self.range[i].valueChanged.connect(self.updateHistogram)
			self.range[i].sliderReleased.connect(self.updatePlot)

	def updateHistogram(self):
		self.histogram.update(self.range[0].value(), self.range[1].value())

	def updatePlot(self):
		self.windowUpdated.emit(self.range[0].value(), self.range[1].value())

	def setData(self,data):
		# Give histogram the data to work with.
		self.histogram.loadImage(data)
		# Give the slider widgets a max and min value to work with.
		vmin = np.min(data)
		vmax = np.max(data)
		for i in range(len(self.range)):
			self.range[i].setMinimum(vmin)
			self.range[i].setMaximum(vmax)
		self.range[0].setValue(vmin)
		self.range[1].setValue(vmax)

	def setEnabled(self,state):
		for i in range(len(self.range)):
			self.range[i].setEnabled(state)

class Histogram:
	def __init__(self):
		# super().__init__()
		# A figure instance to plot on.
		self.figure = plt.figure()
		# This is the Canvas Widget that displays the `figure`.
		self.canvas = FigureCanvasQTAgg(self.figure)
		# Add axes for plotting on.
		self.ax = self.figure.add_axes([0,0,1,1])
		# Draw the canvas.
		self.canvas.draw()

	def loadImage(self,data,**kwargs):
		self.ax.cla()
		# Data min and max.
		dmin = np.min(data)
		dmax = np.max(data)
		# Take the data and make a histogram.
		nbins = kwargs.get('nbins',64)
		histogramValues,_,_ = self.ax.hist(data.ravel(),facecolor='k',alpha=0.5,bins=nbins)
		self.hmax = np.max(histogramValues)
		# Draw lines over the plot.
		self.ax.plot([dmin,dmax],[0,self.hmax],'k-',lw=1)
		self.ax.plot([dmax,dmax],[0,self.hmax],'k--',lw=1)

	def update(self,rmin,rmax):
		'''Update the histogram scale line to match the sliders.'''
		# Remove old lines.
		for i in range(len(self.ax.lines)):
			# This will recursively remove the first line until there are no lines left.
			self.ax.lines[0].remove()
		# Add new lines.
		self.ax.plot([rmin,rmax],[0,self.hmax],'k-', lw=1)
		self.ax.plot([rmax,rmax],[0,self.hmax],'k--', lw=1)
		# Redraw.
		self.canvas.draw()

class QsWindow:
	def __init__(self,parent,plot,advanced=False):
		# Must pass a parent plot to it (MPL2DFigure).
		self.parent = parent
		self.plot = plot
		self.advanced = advanced
		# Set the size.
		# sizePolicy = QtWidgets.QSizePolicy.Minimum
		# self.parent.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
		# self.parent.setContentsMargins(0,0,0,0)
		self.parent.setMaximumSize(500,170)
		# Get image details from parent.
		self.dataMin = 0
		self.dataMax = 0
		# Create a layout.
		layout = QtWidgets.QFormLayout()
		# Create widgets.
		self.histogram = histogram(plot)
		self.widget = {}
		# Min Slider.
		self.widget['sl_min'] = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.widget['sl_min'].setTracking(False)
		self.widget['sl_min'].setEnabled(False)
		# Max Slider.
		self.widget['sl_max'] = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.widget['sl_max'].setTracking(False)
		self.widget['sl_max'].setEnabled(False)
		# Labels.
		lb_min = QtWidgets.QLabel('Min')
		lb_max = QtWidgets.QLabel('Max')
		# Connect buttons.
		self.widget['sl_min'].valueChanged.connect(self.updateWindow)
		self.widget['sl_max'].valueChanged.connect(self.updateWindow)
		# Assign layout.
		layout.addRow(self.histogram.canvas)
		layout.addRow(lb_min,self.widget['sl_min'])
		layout.addRow(lb_max,self.widget['sl_max'])
		# # Check for advanced options.
		# if self.advanced == True:
		# 	# Add radio buttons for 3d arrays where flattening option can be chosen.
		# 	self.widget['rb_sum'] = QtWidgets.QRadioButton('Sum')
		# 	self.widget['rb_max'] = QtWidgets.QRadioButton('Max')
		# 	self.widget['rb_sum'].toggled.connect(self.updateFlatteningMode)
		# 	self.widget['rb_max'].toggled.connect(self.updateFlatteningMode)
		# 	# Defaults.
		# 	self.widget['rb_sum'].setChecked(True)
		# 	self.widget['rb_max'].setChecked(False)
		# 	# Add to layout.
		# 	layout.addRow(self.widget['rb_sum'],self.widget['rb_max'])
		# Set layout.
		self.parent.setLayout(layout)

	def refreshControls(self):
		# Get image details from parent.
		self.dataMin = np.min(self.plot.data3d)
		self.dataMax = np.max(self.plot.data3d)
		# Slider Min Controls
		self.widget['sl_min'].setMinimum(self.dataMin)
		self.widget['sl_min'].setMaximum(self.dataMax-1)
		self.widget['sl_min'].setValue(self.dataMin)
		# Slider Max Controls
		self.widget['sl_max'].setMinimum(self.dataMin+1)
		self.widget['sl_max'].setMaximum(self.dataMax)
		self.widget['sl_max'].setValue(self.dataMax)
		# Enable Sliders
		self.widget['sl_min'].setEnabled(True)
		self.widget['sl_max'].setEnabled(True)
		# Refresh histogram.
		self.histogram.refresh()

	# def updateFlatteningMode(self):
	# 	if self.widget['rb_sum'].isChecked() == True:
	# 		mode = 'sum'
	# 	elif self.widget['rb_max'].isChecked() == True:
	# 		mode = 'max'
	# 	self.plot._radiographMode = mode

	def updateWindow(self):
		if self.plot.image == None:
			# If there is no image yet loaded, do nothing.
			return

		# Get minimum and maximum values from sliders.
		minimum = self.widget['sl_min'].value()
		maximum = self.widget['sl_max'].value()
		# Calculate scale.
		scale = (self.dataMax-self.dataMin) / (maximum-minimum)
		# Find shifted maximum.
		# shift = minimum - self.dataMin
		# maximum_shifted = maximum - np.absolute(minimum)
		shift = -minimum
		maximum_shifted = maximum + shift
		# Copy array data.
		self.plot.data = np.array(self.plot.data3d)
		# Shift array.
		self.plot.data += shift
		# Set every negative value to zero.
		# self.plot.data[self.plot.data < self.dataMin] = self.dataMin
		self.plot.data[self.plot.data < 0] = 0
		# Set everything above the maximum value to max.
		self.plot.data[self.plot.data > maximum_shifted] = maximum_shifted
		# Scale data.
		self.plot.data *= scale
		# Shift back to original position.
		self.plot.data += self.dataMin
		# Check for advanced options.
		if self.advanced == True:
			# Check plot number.
			if self.plot.imageIndex == 0:
				direction = 2
			elif self.plot.imageIndex == 1:
				direction = 1
			# Check flattening mode.
			if self.plot._radiographMode == 'max':
				self.plot.data = np.amax(self.plot.data,axis=direction)
			elif self.plot._radiographMode == 'sum':
				self.plot.data = np.sum(self.plot.data,axis=direction)
			else:
				pass
		# Set data.
		self.plot.image.set_data(self.plot.data)
		# Redraw canvas.
		self.plot.canvas.draw()
		# Update histogram overlay.
		self.histogram.update(minimum,maximum)
		# Restrict the value of each slider?? So that one can't go past the other.