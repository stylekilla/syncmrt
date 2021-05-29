from systems.control.backend import epics as backend
from PyQt5 import QtCore, QtWidgets
import logging
import numpy as np
from datetime import datetime as dt
from functools import partial

"""
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
"""

class detector(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()
	detectorReady = QtCore.pyqtSignal()
	imageAcquired = QtCore.pyqtSignal(str)

	def __init__(self,
				name,
				config,
				backendThread=None
			):
		super().__init__()
		# self._name = str(name)
		self.name = name
		# Config.
		self.config = config
		# Row/Col pixel sizes.
		self.pixelSize = [1,1]
		# Isocenter as a pixel location in the image.
		self.imageIsocenter = [0,0]
		# Make a buffer of images. 
		# Should be in the format { uid: (image,metadata) }.
		self.buffer = {}
		# Epics backend controller.
		self.controller = backend.detector(config)
		# Move to thread if specified.
		if backendThread is not None:
			self.controller.moveToThread(backendThread)
		# Signals.
		self.controller.connected.connect(self.connected.emit)
		self.controller.disconnected.connect(self.disconnected.emit)
		self.controller.detectorReady.connect(self.detectorReady.emit)

	def reconnect(self):
		if self.controller is not None:
			self.controller.reconnect()

	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self.controller.isConnected()

	def setParameters(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			backend.set(key,value)

	def setupDynamicScan(self,distance,speed,uid):
		""" Passthrough function: Set the detector up for a dynamic scan. """
		# Create an entry into the buffer.
		self.buffer[uid] = None
		# Set the scan up.
		self.controller.setupDynamicScan(distance,speed,uid)

	def acquire(self,mode,uid,metadata):
		""" Passthrough function: Acquire an image. """
		# Get the acquire mode.
		if mode not in ['static','dynamic']:
			raise TypeError(f"Unknown acquire mode: {mode}.")
		# If all good, acquire the image.
		self.controller.imageAcquired.connect(self._acquireFinished)
		try:
			self.controller.acquire(mode,uid,metadata)
		except:
			self.error.emit()

	def _acquireFinished(self,uid):
		""" Return an image. """
		# Get the current time.
		time = dt.now()
		# HDF5 does not support python datetime objects.
		metadata = {
			'Detector': self.name,
			'Time': time.strftime("%H:%M:%S"),
			'Date': time.strftime("%d/%m/%Y"),
		}
		# Get the image from the detector.
		self.buffer[uid] = self.controller.getImage(uid)
		# Update the metadata with the detector metadata (extent).
		metadata.update(self.buffer[uid][1])
		# Tell the world we have an image that is acquired (and finalized).
		self.imageAcquired.emit(uid)

	def getImage(self,uid):
		# Return the data.
		return self.buffer[uid]
