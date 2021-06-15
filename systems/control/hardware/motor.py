from tools import math
from PyQt5 import QtCore
import numpy as np
import importlib
import logging

"""
Motor should run on it's own QThread.
Motor will emit finished signal after move is completed.
Should only use motor.read() and motor.write() methods.
"""

__all__ = ['motor','velocityController']

class motor(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	position = QtCore.pyqtSignal(float)
	moveStarted = QtCore.pyqtSignal(float,float)
	moveFinished = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()

	def __init__(self,
				config,
				backend,
				backendThread=None,
			):
		super().__init__()
		self.config = config
		self.name = self.config.port
		self.description = self.config.description
		# Backend Controller.
		backend = importlib.import_module(f"systems.control.backend.{backend}")
		# Expecting axis to be between 0 and 5.
		# Axis can be 0,1,2 to represent x,y,z.
		# Type is 0 (translation) or 1 (rotation).
		if self.config.axis < 3: 
			self._axis = self.config.axis
			self._type = 0
		elif self.config.axis > 2: 
			self._axis = self.config.axis - 3
			self._type = 1
		# Motor order.
		self._order = self.config.order
		# Port.
		self.port = self.config.port

		# Backend Controller.
		self._controller = backend.motor(self.port)
		# Move to thread if specified.
		if backendThread is not None:
			self._controller.moveToThread(backendThread)
		# Signals.
		self._controller.connected.connect(self.connected.emit)
		self._controller.disconnected.connect(self.disconnected.emit)
		self._controller.error.connect(self.error.emit)
		self._controller.position.connect(self.position.emit)
		self._controller.moveStarted.connect(self.moveStarted.emit)
		self._controller.moveFinished.connect(self.moveFinished.emit)
		
	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self._controller.isConnected()

	def setPosition(self,position):
		try:
			self._controller.write(position,mode='absolute')
		except:
			self.error.emit()

	def shiftPosition(self,position):
		try:
			self._controller.write(position,mode='relative')
		except:
			self.error.emit()

	def readPosition(self):
		try:
			value = self._controller.read()
		except:
			value = np.NaN

		return value

	def transform(self,value):
		# If we are a translation motor, return a translation transfrom.
		if self._type == 0:
			return math.transform.translation(self._axis,value)
		if self._type == 1:
			value += self._controller.read()
			return math.transform.rotation(self._axis,value), math.transform.rotation(self._axis,-self._controller.read())

	def reconnectControls(self):
		try:
			self._controller.reconnect()
		except:
			self.error.emit()


class velocityController(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	speedChanged = QtCore.pyqtSignal(float,float)
	error = QtCore.pyqtSignal()

	def __init__(self,config,backend,backendThread=None):
		super().__init__()
		self.config = config
		# Backend Controller.
		backend = importlib.import_module(f"systems.control.backend.{backend}")
		# Send the velocity/acceleration ports through to the controller.
		self._controller = backend.velocityController(config)
		# Move to thread if specified.
		if backendThread is not None:
			self._controller.moveToThread(backendThread)

	def setSpeed(self,value):
		""" Passthrough function: Set the motor speed. """
		self._controller.setSpeed(value)

	def getSpeed(self):
		""" Passthrough function: Get the motor speed. """
		return self._controller.getSpeed()

	def setAcceleration(self,value):
		""" Passthrough function: Set the motor acceleration. """
		self._controller.setAcceleration(value)

	def getAcceleration(self):
		""" Passthrough function: Get the motor acceleration. """
		return self._controller.getAcceleration()

	def reconnectControls(self):
		try:
			self._controller.reconnect()
		except:
			self.error.emit()