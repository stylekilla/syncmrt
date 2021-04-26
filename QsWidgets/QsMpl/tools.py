from matplotlib.backend_tools import ToolBase, ToolToggleBase, Cursors
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


__all__ = ['ToolPickPoint','ToolPickIso','ToolClearPoints']


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