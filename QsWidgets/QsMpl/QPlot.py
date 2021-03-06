import matplotlib as mpl
mpl.use('Qt5Agg')
mpl.rcParams['toolbar'] = 'toolmanager'
mpl.rcParams['datapath'] = './QsWidgets/QsMpl/mpl-data'

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, FigureManagerQT
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from .tools import ToolPickPoint, ToolPickIso, ToolClearPoints
from .QHistogram import QHistogramWindow

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from systems.imageGuidance import optimiseFiducials
from functools import partial
import logging

__all__ = ['QPlot']


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
		# Reference to ax.imshows().
		self.images = {}
		# Set up marker tracking.
		self.markers = {}
		self.markersMaximum = 0
		self.ctd = [None,None]
		# Set up histograms dict for axes.
		self.histograms = {}

		# Create 2 axes.
		self.ax = self.fig.subplots(1,2,gridspec_kw={'hspace':0,'wspace':0,'left':0,'right':1,'bottom':0,'top':1},sharey=False)
		for idx, ax in enumerate(self.ax):
			# Set up tracking for markers in the axes.
			self.markers[ax] = []
			# Set up histogram connections.
			self.histograms[ax] = QHistogramWindow()
			self.histograms[ax].windowUpdated.connect(partial(self.applyWindow,ax))
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
		self.clear()
		# Remove all previous images.
		for key in self.images:
			# Remove the imshow.
			self.images[key].remove()
		# Remove the stored references.
		self.images.clear()
		# Remove all previous markers.
		for ax in self.ax:
			del self.markers[ax][:]

		for i, image in enumerate(images):
			# Load the image. Assumes 2D array, forces 32-bit floats.
			self.images[self.ax[i]] = self.ax[i].imshow(np.array(image.pixelArray,dtype=np.float32), cmap='bone', extent=image.extent)
			# Setup the axes.
			self.ax[i].set_xlim(image.extent[0:2])
			self.ax[i].set_ylim(image.extent[2:4])
			self.ax[i].set_aspect("equal", "datalim")
			# Setup the histogram data.
			self.histograms[self.ax[i]].setData(image.pixelArray)
			self.histograms[self.ax[i]].setTitle('View: '+image.view['title'])

		if i == 0:
			# Only one image.
			self.ax[0].set_position([0,0,1,1])
			self.ax[1].set_position([0.9999,0.9999,0.0001,0.0001])
			self.ax[1].set_visible(False)
		else:
			# Show two images.
			self.ax[0].set_position([0,0,0.5,1])
			self.ax[1].set_position([0.5,0,0.5,1])
			self.ax[1].set_visible(True)

		self.canvas.draw()

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

	def getHistograms(self):
		""" Return a list of histograms. """
		return list(self.histograms.values())

	def applyWindow(self,axes,imin,imax):
		# Set the color scale to match the window.
		if imin < imax:
			self.images[axes].set_clim(vmin=imin,vmax=imax)
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

	def markerUpdate(self,axesIndex,markerLocations):
		""" Update all the markers. """
		# Get the desired axes.
		ax = self.ax[axesIndex]
		# Create a new centroid.
		centroid = np.array([0,0]).astype(float)
		# Clear the markers and add the new ones.
		for pos, marker in enumerate(self.markers[ax]):
			marker[0].remove()
			marker[1].remove()
			x,y = markerLocations[pos]
			marker[0] = ax.scatter(x,y,c='r',marker='+',s=50)
			marker[1] = ax.text(x+1,y,pos+1,color='r')
			centroid += np.array([x,y]).astype(float)
		# Calculate new centroid.
		centroid = centroid/len(centroid)
		# Set the centroid.
		self.setCentroid(axesIndex,centroid)
		# Refresh the canvas.
		self.canvas.draw()

	def removeMarkers(self):
		""" 
		Clear all markers in all axes.

		Parameters
		----------
		plot : int
			Can take values of -1 (both plots) or plot 1 or 2.
		"""
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
			# Clear the plot.
			ax.cla()
			# Clear the histogram.
			self.histograms[ax].clear()
		# Remove all references to ax.imshows.
		self.images.clear()
		# Refresh the canvas.
		self.canvas.draw()

	def updatePatientIsocenter(self,x,y,z):
		""" Update the patient isocenter in 3D. """
		self.patientIsocenter = [x,y,z]
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False)
			self.toggleOverlay(3,True)

	def getIsocenter(self):
		""" Return the patient isocenter. """
		return self.patientIsocenter

	def toggleOverlay(self,overlayType,state=False):
		'''
		Single overlay function with various types.
			0: Centroid overlay
			1: Machine Isocenter overlay
			2: Patient Isocenter overlay
			3: Beam area overlay
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
				if type(self.ctd[0]) != type(None):
					x,y = self.ctd[0]
					self.overlay['ctd'].append(self.ax[0].scatter(x,y,c='b',marker='+',s=50))
					self.overlay['ctd'].append(self.ax[0].text(x+1,y-3,'ctd',color='b'))
				if type(self.ctd[1]) != type(None):
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
			# Overlay of the beam field.
			# Remove it first if it already exists.
			if 'beamArea' in self.overlay:
				for obj in reversed(self.overlay['beamArea']):
					obj.remove()
				del(self.overlay['beamArea'])
			if state is True:
				self.overlay['beamArea'] = []
				# Create new patches.
				_beam = Rectangle((-self.maskSize/2,-self.maskSize/2), self.maskSize, self.maskSize,fc='r',ec='none',alpha=0.2)
				_ptv1 = Rectangle((self.patientIsocenter[0]-self.maskSize/2,self.patientIsocenter[1]-self.maskSize/2), self.maskSize, self.maskSize,fc='none',ec='y',ls='--',alpha=1.0)
				_ptv2 = Rectangle((self.patientIsocenter[2]-self.maskSize/2,self.patientIsocenter[1]-self.maskSize/2), self.maskSize, self.maskSize,fc='none',ec='y',ls='--',alpha=1.0)
				# Different patch collection for each plot.
				pc1 = PatchCollection([_beam,_ptv1],match_original=True)
				pc2 = PatchCollection([_beam,_ptv2],match_original=True)
				# Add the collections to the axes.
				self.overlay['beamArea'].append(self.ax[0].add_collection(pc1))
				self.overlay['beamArea'].append(self.ax[1].add_collection(pc2))
			else:
				pass
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