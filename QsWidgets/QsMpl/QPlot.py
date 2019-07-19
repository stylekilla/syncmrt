import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtGui, QtCore, QtWidgets
from systems.imageGuidance import optimiseFiducials
from functools import partial

__all__ = ['QPlot','QHistogramWindow']

class QPlot:
	'''
	Documentation for now:
	- imageLoad(filename, pixelsize, oreitnation, imagenumber(/2), fileformat): Load image into canvas.
	- imageUpdate(newdata): Send new data to canvas.
	- markerUpdate(): Called from eventFilter (cid: callbackID), appends new markers?
	- markerReset(markerspecifier): Resets the markers (either one or all).
	- eventFilter(event): Based on the event identifier we can tell it to do something.
	'''

	def __init__(self,tableModel):
		self.image = None
		self.plotDimensions = None
		self.pointsX = []
		self.pointsY = []
		self.i = 0
		self.markersMaximum = 0
		self.markersList = []
		self.markersListOptimised = []
		self.markerModel = tableModel
		self._radiographMode = 'sum'
		self._R = np.identity(3)
		self._imagingAngle = 0
		self.mask = None
		self.overlay = {}
		self.machineIsocenter = [0,0]
		self.patientIsocenter = [0,0]
		self.ctd = None
		# Centroid stores the [x,y] coordinate and the current overlay state [True/False].
		# self.ctd = [None,False]

		self.fig = plt.figure()
		self.fig.patch.set_facecolor('#000000')
		self.ax = self.fig.add_axes([0,0,1,1])
		self.ax.set_facecolor('#000000')
		self.ax.title.set_color('#FFFFFF')
		self.ax.xaxis.label.set_color('#FFFFFF')
		self.ax.yaxis.label.set_color('#FFFFFF')
		self.ax.xaxis.set_label_coords(0.5,0.12)
		self.ax.yaxis.set_label_coords(0.12,0.5)
		self.ax.xaxis.label.set_size(20)
		self.ax.yaxis.label.set_size(20)
		# self.ax.yaxis.label.set_rotation(90)
		self.ax.spines['left'].set_visible(False)
		self.ax.spines['top'].set_visible(False)
		self.ax.spines['right'].set_visible(False)
		self.ax.spines['bottom'].set_visible(False)
		self.ax.tick_params('both',which='both',length=7,width=1,pad=-30,direction='in',colors='#FFFFFF')

		# Create a canvas widget for Qt to use.
		self.canvas = FigureCanvas(self.fig)
		# self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
		# self.canvas.setCursor(QtCore.Qt.CrossCursor)
		cursor = mpl.widgets.Cursor(self.ax, useblit=True, color='red', linewidth=2)
		# Refresh the canvas.
		self.canvas.draw()

		self.canvas._pickerActive = False

	def updatePatientIsocenter(self,_x,_y):
		""" Update the patient isocenter and refresh the overlay. """
		self.patientIsocenter = [_x,_y]
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False) 
			self.toggleOverlay(3,True)

	def loadCoordinate(self,name,vector):
		# Pull in DICOM information in XYZ mm and turn it into the current view of the dataset.
		self.coordinate[name] = self._R@np.transpose(np.array(vector))

	def imageLoad(self,array,extent=np.array([-1,1,-1,1])):
		# Clear the canvas and start again:
		self.ax.cla()

		# Always make it float32. Always assume it is a flat 2D array.
		self.data = np.array(array,dtype=np.float32)
		self.extent = extent
		
		self.image = self.ax.imshow(self.data, cmap='bone', extent=self.extent)
		self.ax.set_xlim(extent[0:2])
		self.ax.set_ylim(extent[2:4])
		self.ax.set_aspect("equal", "datalim")
		self.canvas.draw()
		# Start Callback ID
		self.cid = self.canvas.mpl_connect('button_press_event', self.eventFilter)


	def applyWindow(self,imin,imax):
		# Set the color scale to match the window.
		try:
			self.image.set_clim(vmin=imin,vmax=imax)
			self.canvas.draw()
		except:
			pass

	def markerAdd(self,x,y):
		'''Append marker position if it is within the maximum marker limit.'''
		if self.i < self.markersMaximum:
			self.pointsX.append(x)
			self.pointsY.append(y)
			self.i += 1
			self.markerModel.addPoint(self.i,x,y)
			# Re-calculate the centroid.
			if self.i > 1:
				ctd_x = np.sum(self.pointsX)/self.i
				ctd_y = np.sum(self.pointsY)/self.i
				self.ctd = [ctd_x,ctd_y]
				if 'ctd' in self.overlay:
					# Refresh it's position on the screen.
					self.toggleOverlay(0,False)
					self.toggleOverlay(0,True)
			# Plot marker list.
			scatter = self.ax.scatter(x,y,c='r',marker='+',s=50)
			text = self.ax.text(x+1,y-3,self.i,color='r')
			self.markersList += scatter,text
			# Refresh views.
			self.canvas.draw()

	def markerUpdate(self,item):
		'''Redraw all the markers to their updated positions.'''
		# Item = qabstractitemmodel item linking to the marker to be changed.
		if self.markerModel._locked:
			pass
		else:
			for key in self.markerModel.items:
				for value in self.markerModel.items[key]:
					if value == item:
						index1 = self.markerModel.indexFromItem(self.markerModel.items[key][0])
						index2 = self.markerModel.indexFromItem(self.markerModel.items[key][1])
						x = self.markerModel.data(index1)
						y = self.markerModel.data(index2)
						# key is row which x,y is stored.
						scatter = self.ax.scatter(x,y,c='r',marker='+',s=50)
						text = self.ax.text(x+1,y-3,key+1,color='r')
						# Remove old plots.
						self.markersList[key*2].remove()
						self.markersList[key*2+1].remove()
						# Remove from list.
						self.markersList.remove(self.markersList[key*2])
						self.markersList.remove(self.markersList[key*2])
						# Insert new.
						self.markersList[key*2:key*2] = scatter,text
						self.canvas.draw()
						# Update pointsXY lists.
						self.pointsX[key] = x
						self.pointsY[key] = y
						# Re-calculate the centroid.
			if self.i > 1:
				ctd_x = np.sum(self.pointsX)/self.i
				ctd_y = np.sum(self.pointsY)/self.i
				self.ctd[0] = [ctd_x,ctd_y]
				if 'ctd' in self.overlay:
					# Refresh it's position on the screen.
					self.toggleOverlay(0,False)
					self.toggleOverlay(0,True)

	def removeMarker(self,marker=-1):
		'''Clear the specified marker. Else clear all markers.'''
		# Remove all markers: 
		if marker == -1:
			self.i = 0
			self.pointsX = []
			self.pointsY = []
			self.ctd = None
			# Remove the overlays if they exist.
			if 'ctd' in self.overlay:
				self.toggleOverlay(0,False)
				self.overlay['ctd'] = None
			if len(self.markersList) > 0:
				for index in range(len(self.markersList)):
					self.markersList[index].remove()
			self.markersList = []
			# Reset table values.
			self.markerModel.clearMarkers(self.markersMaximum)
			# Set to -2 to remove optimised markers as well.
			marker = -2

		elif marker == -2:
			# Remove optimised markers, if any.
			self.pointsXoptimised = []
			self.pointsYoptimised = []
			if len(self.markersListOptimised) > 0:
				for i in range(len(self.markersListOptimised)):
					self.markersListOptimised[-1].remove()
					del(self.markersListOptimised[-1])

		else: return

		self.canvas.draw()

	def markerOptimise(self,fiducialSize,threshold):
		'''Optimise markers that are selected in plot.'''
		# Remove any existing markers.
		self.removeMarker(marker=-2)

		# Call syncMRT optimise points module. Send points,data,dims,markersize.
		pointsIn = np.column_stack((self.pointsX,self.pointsY))
		extent = self.image.get_extent()
		# points = optimiseFiducials(pointsIn,self.data,extent,fiducialSize,threshold)
		points = optimiseFiducials(pointsIn,np.array(self.data),extent,fiducialSize,threshold)
		self.pointsXoptimised = points[:,0]
		self.pointsYoptimised = points[:,1]

		# Re-plot with optimised points over the top (in blue).
		self.markersListOptimised = []
		for i in range(len(self.pointsXoptimised)):
			x = self.pointsXoptimised[i]
			y = self.pointsYoptimised[i]
			# Plot marker list.
			scatter = self.ax.scatter(x,y,c='b',marker='+',s=50)
			text = self.ax.text(x+1,y-3,i+1,color='b')
			self.markersListOptimised += scatter,text

		self.canvas.draw()

	def markers(self):
		""" Return the points in this plot as a list. """
		return list(zip(self.pointsX,self.pointsY))

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
				# Plot overlay scatter points.
				if self.ctd is not None:
					x,y = self.ctd
					self.overlay['ctd'] = [
							self.ax.scatter(x,y,c='b',marker='+',s=50),
							self.ax.text(x+1,y-3,'ctd',color='b')
						]
			else:
				pass

		elif overlayType == 1:
			# Machine isocenter overlay.
			# Remove overlay lines.
			if 'machIsoH' in self.overlay:
				self.overlay['machIsoH'].remove()
				del(self.overlay['machIsoH'])
			if 'machIsoV' in self.overlay:
				self.overlay['machIsoV'].remove()
				del(self.overlay['machIsoV'])
			if state is True:
				# Plot overlay lines.
				self.overlay['machIsoV'] = self.ax.axvline(self.machineIsocenter[0],c='r',alpha=0.5)
				self.overlay['machIsoH'] = self.ax.axhline(self.machineIsocenter[1],c='r',alpha=0.5)
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
				# Create new patches.
				self.overlay['patIso'] = [
						self.ax.scatter(self.patientIsocenter[0],self.patientIsocenter[1],marker='+',color='y',s=50),
						self.ax.text(self.patientIsocenter[0]+1,self.patientIsocenter[1]-3,'ptv',color='y')
					]
			else:
				pass
		elif overlayType == 3:
			# Remove it first if it already exists.
			if 'beamArea' in self.overlay:
				self.overlay['beamArea'].remove()
				del(self.overlay['beamArea'])
			# Beam area overlay.
			if state is True:
				# Create new patches.
				_maskSize = 5
				_beam = Rectangle((-_maskSize/2,-_maskSize/2), _maskSize, _maskSize,fc='r',ec='none')
				_ptv = Rectangle((self.patientIsocenter[0]-_maskSize/2,self.patientIsocenter[1]-_maskSize/2), _maskSize, _maskSize,fc='y',ec='none')
				pc = PatchCollection([_beam,_ptv],alpha=0.2,match_original=True)
				self.overlay['beamArea'] = self.ax.add_collection(pc)
			else:
				pass
		# Update the canvas.
		self.canvas.draw()

	def setExtent(self,newExtent):
		# Change extent and markers.
		change = newExtent-self.extent

		''' Update markers '''
		# Get values and add changes.
		for i in range(len(self.pointsX)):
			self.pointsX[i] -= change[0]
			self.pointsY[i] -= change[2]

		x,y = self.pointsX,self.pointsY

		# for key,val in self.pointsX.items():
		# 	self.pointsX[key] += change[0]
		# for key,val in self.pointsY.items():
		# 	self.pointsY[key] += change[1]
		# Get new positions
		
		# Remove markers
		self.removeMarker()
		# Add new points
		for i in range(len(x)):
			self.markerAdd(x[i],y[i])

		# Update extent
		self.extent = newExtent
		self.image.set_extent(self.extent)

		# Refresh
		self.canvas.draw()

	def eventFilter(self,event):
		# If mouse button 1 is clicked (left click).
		if (event.button == 1) & (self.canvas._pickerActive):
			self.markerAdd(event.xdata,event.ydata)

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
		# Flattening method buttons.
		self.button = []
		self.button.append(QtWidgets.QRadioButton('Sum'))
		self.button.append(QtWidgets.QRadioButton('Max'))
		options = QtWidgets.QWidget()
		optionsLayout = QtWidgets.QHBoxLayout()
		optionsLayout.addWidget(self.button[0])
		optionsLayout.addWidget(self.button[1])
		options.setLayout(optionsLayout)
		# Layout.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(self.histogram.canvas)
		layout.addWidget(self.range[0])
		layout.addWidget(self.range[1])
		layout.addWidget(options)
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
		for i in range(len(self.button)):
			self.button[i].setEnabled(state)

class Histogram:
	def __init__(self):
		# super().__init__()
		# A figure instance to plot on.
		self.figure = plt.figure()
		# This is the Canvas Widget that displays the `figure`.
		self.canvas = FigureCanvas(self.figure)
		# Add axes for plotting on.
		self.ax = self.figure.add_axes([0,0,1,1])
		# Draw the canvas.
		self.canvas.draw()

	def loadImage(self,data,**kwargs):
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
		# Check for advanced options.
		if self.advanced == True:
			# Add radio buttons for 3d arrays where flattening option can be chosen.
			self.widget['rb_sum'] = QtWidgets.QRadioButton('Sum')
			self.widget['rb_max'] = QtWidgets.QRadioButton('Max')
			self.widget['rb_sum'].toggled.connect(self.updateFlatteningMode)
			self.widget['rb_max'].toggled.connect(self.updateFlatteningMode)
			# Defaults.
			self.widget['rb_sum'].setChecked(True)
			self.widget['rb_max'].setChecked(False)
			# Add to layout.
			layout.addRow(self.widget['rb_sum'],self.widget['rb_max'])
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

	def updateFlatteningMode(self):
		if self.widget['rb_sum'].isChecked() == True:
			mode = 'sum'
		elif self.widget['rb_max'].isChecked() == True:
			mode = 'max'
		self.plot._radiographMode = mode

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