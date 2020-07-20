import epics
import numpy as np
import logging
import time
from PyQt5 import QtCore

"""
We don't use the device classes due to a lack of callback functionality and you can't check things like
the connection state of the pv's/device etc. 
Therefore, we implement all that functionality ourselves.
"""

MOTOR_PVS = [
	'VAL', 'DESC', 'RBV', 'PREC', 'DMOV',
	'BDST', 'BACC', 'BVEL',
	'TWV', 'TWF', 'TWR',
	'VELO',
	'LLM', 'HLM', 'HLS', 'LLS','LVIO'
]

class MotorException(Exception):
	""" Raised to indicate a problem with a motor """
	def __init__(self, msg, *args):
		Exception.__init__(self, *args)
		self.msg = msg
	def __str__(self):
		# Debugging logs included.
		logging.debug(self.msg)
		return str(self.msg)

class MotorLimitException(Exception):
	""" Raised to indicate a problem with a motor """
	def __init__(self, msg, *args):
		Exception.__init__(self, *args)
		self.msg = msg
	def __str__(self):
		# Debugging logs included.
		logging.debug(self.msg)
		return str(self.msg)

class epicsMotor(QtCore.QObject):
	"""
	If the motor driver can't do anything, it raises an exception MotorException.
	The caller function should attempt to catch this in the event something goes wrong.
	"""
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	moveFinished = QtCore.pyqtSignal()

	def __init__(self,pvName):
		super().__init__()
		# Save the pv base.
		self.pvBase = pvName
		# Initialisation vars.
		self._connectionStatus = True
		# Add all the pv's.
		self.pv = {}
		for pv in MOTOR_PVS:
			setattr(self,pv,epics.PV("{}.{}".format(self.pvBase,pv),auto_monitor=True,connection_callback=self._connectionMonitor))

	def _connectionMonitor(self,*args,**kwargs):
		"""
		Update the device connection status.
		All PV's must be connected in order for the device to be considered connected.
		If any PV in the device is disconnected, the whole device is demmed disconnected.
		"""
		if ('pvname' in kwargs) and ('conn' in kwargs):
			logging.info("{} connection state is {} ({}).".format(kwargs['pvname'],kwargs['conn'],type(kwargs['conn'])))
			# Update the device connection state (by testing all the devices pv's connection states).
			# Note, we set the current connection status sent to this function as the first state in the teststate list.
			# This is because epics hasn't actually set it's connection status to True/False yet, so if we query the motor
			# with .connected it will not provide the correct response. They only set it after the signal has been sent to us.
			teststate = [kwargs['conn']]
			# Get status of every motor except the one sent to this function.
			for pv in [x for x in MOTOR_PVS if x!=kwargs['pvname'][kwargs['pvname'].find('.')+1:]]:
				testpv = getattr(self,pv)
				teststate.append(testpv.connected)
			logging.critical(teststate)
			self._connectionStatus = all(teststate)

		# Send out an appropriate signal.
		if self._connectionStatus:
			self.connected.emit()
		else:
			self.disconnected.emit()

	def isConnected(self):
		# Return if we are connected or not.
		return self._connectionStatus

	def reconnect(self):
		for pv in MOTOR_PVS:
			epicspv = getattr(self,pv)
			try:
				epicspv.reconnect()
			except:
				raise MotorException("Failed to force {} to reconnect.".format(pv))

	def read(self):
		# Return position of motor.
		if self._connectionStatus:
			return self.RBV.get()
		else:
			raise MotorException("Connection error. Could not read motor position.")

	def write(self,value,mode='absolute'):
		if not self._connectionStatus: 
			raise MotorException("Connection error. Could not write motor position.")

		# Get the current motor position, before any attempt of movement.
		previousPosition = self.RBV.get()

		# Calculate the writevalue.
		if mode == 'absolute':
			writeValue = value
		elif mode == 'relative':
			writeValue = previousPosition + value

		# Write the value if acceptable.
		if self.withinLimits(writeValue):
			# If the value is within the limits, write it.
			self.VAL.put(
				writeValue,
				wait=True,
				callback=self._checkMovement,
				callback_data=[previousPosition,writeValue]
			)
		else:
			# It is outside the limits.
			raise MotorLimitException("Value {} exceeds motor limits.".format(writeValue))

	def withinLimits(self,value):
		print(self.HLM.get())
		return (value <= self.HLM.get() and value >= self.LLM.get())

	def _checkMovement(self,*args,**kwargs):
		# Get the previous and new positions.
		previousPosition, expectedPosition = kwargs['data']
		# Get the current position.
		currentPosition = self.RBV.get()

		if float(abs(expectedPosition - currentPosition)) > (float(self.PREC)+float(self.BDST)):
			# We are outside our precision range and backlash distance.
			raise MotorException("The motor did not stop at the expected position of {}.".format(expectedPosition))

		self.moveFinished.emit()


class detector(QtCore.QObject):
	def __init__(self,pv):
		# Initialise the thread.
		super().__init__()
		# PV Base.
		self._pv = pv
		# PV vars.
		self.pv = {}
		# Connection status per motor.
		self._connected = {}
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pv['CAM:Acquire'] = epics.PV(self._pv+':CAM:Acquire',connection_callback=self._updateConnectionStatus)
		self.pv['CAM:DataType_RBV'] = epics.PV(self._pv+':CAM:DataType_RBV',connection_callback=self._updateConnectionStatus)
		self.pv['IMAGE:ArrayData'] = epics.PV(self._pv+':IMAGE:ArrayData',connection_callback=self._updateConnectionStatus)
		self.pv['IMAGE:ArraySize0_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize0_RBV',connection_callback=self._updateConnectionStatus)
		self.pv['IMAGE:ArraySize1_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize1_RBV',connection_callback=self._updateConnectionStatus)

		# Connection status per motor. Set to false by default.
		for pv in self.pv.values():
			self._connected[pv.pvname] = False

	def reconnect(self):
		# Reconnect the pv's.
		for pv in self.pv.values():
			pv.reconnect()
		# Return if they are now connected or not.
		connected = self.isConnected()
		return connected

	def _updateConnectionStatus(self,pvname,conn,*args,**kwargs):
		# Update connection status per PV.
		self._connected[pvname] = conn

	def isConnected(self):
		# Return True or False for if all the PV's are connected or not.
		return all(self._connected.values())

	def readImage(self):
		if self._connected is False:
			return None
		else:
			# Tell the detector to acquire.
			self.pv['CAM:Acquire'].put(1,wait=True)
			# Sleep for the acquisition period.
			image = self.pv['IMAGE:ArrayData'].get()
			# Grab image shape.
			x = self.pv['IMAGE:ArraySize1_RBV'].get()
			y = self.pv['IMAGE:ArraySize0_RBV'].get()
			logging.info("Flipping RUBY images because it is retarded.")
			return np.flipud(image.reshape(x,y))
			# return np.fliplr(np.flipud(image.reshape(x,y)))
