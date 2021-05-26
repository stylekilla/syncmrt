from tools import math
from systems.control.backend import epics as backend
from PyQt5 import QtCore
import numpy as np
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
				name,axis,order,
				pv=None,
				backendThread=None,
				mrange=np.array([-np.inf,np.inf]),
				direction=1,
				frame=1,
				size=np.array([0,0,0]),
				workDistance=np.array([0,0,0]),
				stageLocation=0
			):
		super().__init__()
		# Expecting axis to be between 0 and 5.
		# Axis can be 0,1,2 to represent x,y,z.
		# Type is 0 (translation) or 1 (rotation).
		if axis < 3: 
			self._axis = axis
			self._type = 0
		elif axis > 2: 
			self._axis = axis - 3
			self._type = 1
		# Motor order.
		self._order = order
		# Motor name.
		self.name = name
		# PV Base.
		self.pv = pv
		# Direction is +1 (forward) or -1 (reverse) for natural motor movement.
		self._direction = direction
		# Frame of reference local (0) or global (1).
		self._frame = frame
		# Does it affect the stage location? No (0), Yes (1).
		self._stage = stageLocation
		# Stage size.
		self._size = size
		# Define a work point for the motor, this will be non-zero if it has a fixed mechanical working point. This is nominally the isocenter of the machine.
		self._workDistance = workDistance
		self._workPoint = np.array([0,0,0])
		# Upper and lower limits of motor movement.
		self._range = mrange

		# Backend Controller.
		self._controller = backend.motor(self.pv)
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
		
		logging.info("Loading motor {} on aixs {} with PV {}".format(name,axis,pv))

	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self._controller.isConnected()

	def setUi(self,ui):
		# Connect user interface.
		self._ui = motor.ui(ui)

	def setPosition(self,position):
		position *= self._direction
		# If we are not already at the position, then try to go there.
		if position != self._controller.read():
			try:
				self._controller.write(position,mode='absolute')
			except:
				self.error.emit()
		else:
			self.moveFinished.emit()

	def shiftPosition(self,position):
		position *= self._direction
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
			return math.transform.rotation(self._axis,value,self._workPoint), math.transform.rotation(self._axis,-self._controller.read(),self._workPoint)

	def calculateWorkPoint(self,pstage,dstage,offset):
		if self._frame == 0:
			# Find hardware specific position in stage.
			pmotor = pstage - dstage + offset
			# Find work point related to hardware.
			self._workPoint = pstage - dstage + pmotor + self._size + self._workDistance

	def setWorkPoint(self,workpoint):
		# This is useful for robotic arms that do movements in global space.
		if self._frame == 1:
			# Can only be set if work distances are zero and it is a rotation.
			self._workPoint = workpoint

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

	def __init__(self,ports):
		super().__init__()
		# Send the velocity/acceleration ports through to the controller.
		self._controller = backend.velocityController(ports)

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