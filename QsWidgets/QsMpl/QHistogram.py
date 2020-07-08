import matplotlib as mpl
mpl.use('Qt5Agg')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, FigureManagerQT

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial
import logging

__all__ = ['QHistogramWindow']

CENTER_HEADING = """
QGroupBox::title {
	subcontrol-origin: margin;
	subcontrol-position: top;
}
"""

class QHistogramWindow(QtWidgets.QGroupBox):
	# Send a signal with the new window (min, max) range.
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
		# Set enabled to false by default.
		self.setEnabled(False)
		# When sliders change update histogram.
		for i in range(len(self.range)):
			self.range[i].valueChanged.connect(self.updateHistogram)
			self.range[i].sliderReleased.connect(self.updatePlot)

	def updateHistogram(self):
		self.histogram.update(self.range[0].value(), self.range[1].value())

	def updatePlot(self):
		self.windowUpdated.emit(self.range[0].value(), self.range[1].value())

	def setData(self,data):
		# Set enabled to true - we have data.
		self.setEnabled(True)
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

	def clear(self):
		""" Clear the histogram axes. """
		# Remove all data.
		self.histogram.clear()
		# Set enabled to false.
		self.setEnabled(False)

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
		# Clear the axes and start again.
		self.clear()
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
		# Update the canvas.
		self.canvas.draw()

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

	def clear(self):
		""" Clear the histogram data. """
		self.ax.cla()

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