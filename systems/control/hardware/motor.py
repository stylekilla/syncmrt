from tools import math
from systems.control.backend.epics import controls
from PyQt5 import QtCore
import numpy as np
import logging

"""
Motor should run on it's own QThread.
Motor will emit finished signal after move is completed.
Should only use motor.read() and motor.write() methods.
"""

class motor(QtCore.QObject):
	finished = QtCore.pyqtSignal()

	def __init__(self,name,axis,order,
				pv=None,
				direction=1,
				mrange=np.array([-np.inf,np.inf]),
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
		# Interfaces (Qt and Epics).
		self._workerThread = None
		self._ui = None
		self._controller = controls.motor(self.pv)
		logging.info("Loading motor {} on aixs {} with PV {}".format(name,axis,pv))

	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self._controller.isConnected()

	def setUi(self,ui):
		# Connect user interface.
		self._ui = motor.ui(ui)

	def setPosition(self,position):
		position *= self._direction
		self._controller.write(position,mode='absolute')
		# Once finished, emit signal.
		self.finished.emit()

	def shiftPosition(self,position):
		position *= self._direction
		self._controller.write(position,mode='relative')
		# Once finished, emit signal.
		self.finished.emit()

	def readPosition(self):
		return self._controller.read()

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
		self._controller.reconnect()