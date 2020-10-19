from systems.control.backend import epics as backend
from PyQt5 import QtCore, QtWidgets
import logging
import numpy as np
from datetime import datetime as dt

"""
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
"""

class detector(QtCore.QObject):
	imageAcquired = QtCore.pyqtSignal()

	def __init__(self,name,pv):
		super().__init__()
		# self._name = str(name)
		self.name = name
		self.pv = pv
		# Row/Col pixel sizes.
		self.pixelSize = [1,1]
		# Bool triggers.
		self.fliplr = False
		self.flipud = False
		# Isocenter as a pixel location in the image.
		self.imageIsocenter = [0,0]
		# Make a buffer. Useful for stitching images.
		self.buffer = []
		# Controllers.
		self._controller = backend.detector(pv)

	def reconnect(self):
		if self._controller is not None:
			self._controller.reconnect()

	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self._controller.isConnected()

	def setParameters(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			backend.set(key,value)

	def acquire(self):
		time = dt.now()
		# HDF5 does not support python datetime objects.
		metadata = {
			'Detector': self.name,
			'Pixel Size': self.pixelSize,
			'Image Isocenter': self.imageIsocenter,
			'Time': time.strftime("%H:%M:%S"),
			'Date': time.strftime("%d/%m/%Y"),
		}
		logging.info("Could be useful to have a flood/dark field image set stored and incorporated.")
		# Acquire a static image.
		return (self._controller.acquire(), metadata)

	def acquireContinous(self,array):
		self.buffer.append(array)