from matplotlib.backend_tools import ToolBase, ToolToggleBase, Cursors
from matplotlib.widgets import RectangleSelector
from PyQt5.QtCore import QObject, pyqtSignal
import logging

import sys, os

# For PyInstaller:
if getattr(sys, 'frozen', False):
	# If the application is run as a bundle, the pyInstaller bootloader extends the sys module by a flag frozen=True and sets the app path into variable _MEIPASS'.
	application_path = sys._MEIPASS
else:
	application_path = os.path.dirname(os.path.abspath(__file__))
resourceFilepath = application_path+'/resources/'


__all__ = ['ToolPickPoint','ToolPickIso','ToolClearPoints','ToolSelectROI']


class ToolPickPoint(ToolToggleBase,QObject):
	""" Marker selection tool. """
	name = 'pick'
	description = 'Pick a point on the image'
	image = '{}/pick.png'.format(resourceFilepath)
	cursor = Cursors.SELECT_REGION
	radio_group = 'default'
	# Qt5 signals.
	newPoint = pyqtSignal(object,float,float)

	def __init__(self, *args):
		ToolToggleBase.__init__(self, *args)
		QObject.__init__(self)
		self._idPress = None

	def enable(self, event):
		"""Connect press/release events and lock the canvas"""
		self.figure.canvas.widgetlock(self)
		# Add marker on button release.
		self._idPress = self.figure.canvas.mpl_connect('button_release_event', self.newMarker)

	def disable(self,*args):
		"""Release the canvas and disconnect press/release events"""
		self.figure.canvas.widgetlock.release(self)
		self.figure.canvas.mpl_disconnect(self._idPress)

	def trigger(self, sender, event, data=None):
		# What happens when it is triggered?
		ToolToggleBase.trigger(self, sender, event, data)

	def newMarker(self, event):
		# Need to emit axis plus location.
		# Store the data.
		if (event.button == 1):
			self.newPoint.emit(event.inaxes,event.xdata,event.ydata)

class ToolPickIso(ToolToggleBase,QObject):
	""" Marker selection tool. """
	name = 'pickIso'
	description = 'Pick the isocenter to treat'
	image = '{}/pickIso.png'.format(resourceFilepath)
	cursor = Cursors.SELECT_REGION
	radio_group = 'default'
	# Qt5 signals.
	newIsocenter = pyqtSignal(object,float,float)

	def __init__(self, *args):
		ToolToggleBase.__init__(self, *args)
		QObject.__init__(self)
		self._idPress = None

	def enable(self, event):
		"""Connect press/release events and lock the canvas"""
		self.figure.canvas.widgetlock(self)
		# Add marker on button release.
		self._idPress = self.figure.canvas.mpl_connect('button_release_event', self.newIso)

	def disable(self,*args):
		"""Release the canvas and disconnect press/release events"""
		self.figure.canvas.widgetlock.release(self)
		self.figure.canvas.mpl_disconnect(self._idPress)

	def trigger(self, sender, event, data=None):
		# What happens when it is triggered?
		ToolToggleBase.trigger(self, sender, event, data)

	def newIso(self, event):
		# Need to emit axis plus location.
		# Store the data.
		if (event.button == 1):
			self.newIsocenter.emit(event.inaxes,event.xdata,event.ydata)

class ToolClearPoints(ToolBase,QObject):
	""" Clear markers tool. """
	name = 'clear'
	description = 'Clear the points in the images'
	image = '{}/clear.svg'.format(resourceFilepath)
	radio_group = 'default'
	default_toggled = False
	# Qt5 signals.
	clearPoints = pyqtSignal()

	def __init__(self, *args):
		# ToolToggleBase.__init__(self, *args)
		QObject.__init__(self)
		self._button_pressed = None
		self._xypress = None
		self._idPress = None
		self._idRelease = None

	def trigger(self, sender, event, data=None):
		self.clearPoints.emit()

class ToolSelectROI(ToolToggleBase,QObject):
	""" ROI selection tool. """
	name = 'roi'
	description = 'Select an ROI on the image.'
	image = '{}/roiSelect.svg'.format(resourceFilepath)
	cursor = Cursors.SELECT_REGION
	radio_group = 'default'
	# Qt5 signals.
	newROI = pyqtSignal(object,float,float,float,float)

	def __init__(self, *args):
		ToolToggleBase.__init__(self, *args)
		QObject.__init__(self)
		self._idPress = None
		# Create the selectors.
		self.selectors = []
		# Cannot create RectangleSelectors here because figure is currently None.
		# for ax in self.figure.axes:
		# 	self.selectors.append(RectangleSelector(ax,self.select,
		# 		drawtype='box', useblit=True, #button=[1, 3],
		# 		minspanx=5, minspany=5, spancoords='pixels', interactive=True,
		# 		rectprops=dict(facecolor='None',edgecolor='red',fill=False)
		# 	))

	def enable(self, event):
		"""Connect press/release events and lock the canvas"""
		# We cannot use the widget lock because this stops the selectors from working.
		# self.figure.canvas.widgetlock(self._roiSelector)
		# Create selectors.
		for ax in self.figure.axes:
			self.selectors.append(RectangleSelector(ax,self.select,
				drawtype='box', useblit=True, #button=[1, 3],
				minspanx=5, minspany=5, spancoords='pixels', interactive=True,
				rectprops=dict(facecolor='None',edgecolor='red',fill=False)
			))
		# Make them active.
		for selector in self.selectors:
			selector.set_active(True)
		# New ROI signal on button release.
		self._idPress = self.figure.canvas.mpl_connect('button_release_event', self.newROI)

	def disable(self,*args):
		"""Release the canvas and disconnect press/release events"""
		# We cannot use the widget lock because this stops the selectors from working.
		# self.figure.canvas.widgetlock.release(self._roiSelector)
		# Make them inactive and remove them from the plot.
		for selector in self.selectors:
			# Set to invisible.
			selector.set_visible(False)
			# Must re-draw to remove rectangle from plot.
			self.figure.canvas.draw_idle()
			selector.set_active(False)
		# Delete them.
		self.selectors = []
		# Disconnect the trigger.
		self.figure.canvas.mpl_disconnect(self._idPress)

	def select(self,eclick,erelease):
		x1, y1 = eclick.xdata, eclick.ydata
		x2, y2 = erelease.xdata, erelease.ydata
		# eclick.inaxes
		print(x1,y1,x2,y2)

	def trigger(self, sender, event, data=None):
		# What happens when it is triggered?
		ToolToggleBase.trigger(self, sender, event, data)

	def newROI(self,eclick,erelease):
		# Need to emit axis plus location.
		x1, y1 = eclick.xdata, eclick.ydata
		x2, y2 = erelease.xdata, erelease.ydata
		# Store the data.
		print(x1,y1,x2,y2)
		if (event.button == 1):
			self.newROI.emit(eclick.inaxes,x1,x2,y1,y2)

	def enableROISelector(self):
		""" Create an ROI selector in each axis. """
		self._roiSelector.enable()

	def disableROISelector(self):
		""" Disable the tool. """
		self._roiSelector.disable()