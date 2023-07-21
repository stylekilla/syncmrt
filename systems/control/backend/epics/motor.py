import epics
import numpy as np
import logging
from PyQt5 import QtCore
import time
from systems.control.hardware.motor import MotorException, MotorLimitException

"""
We don't use the device classes due to a lack of callback functionality and you can't check things like
the connection state of the pv's/device etc. 
Therefore, we implement all that functionality ourselves.
"""

__all__ = ['motor','velocityController']

MOTOR_PVS = [
	'VAL', 'DESC', 'RBV', 'PREC', 'DMOV',
	'BDST', 'BACC', 'BVEL', 'MOVN',
	'TWV', 'TWF', 'TWR',
	'VELO',
	'LLM', 'HLM', 'HLS', 'LLS','LVIO'
]

class motor(QtCore.QObject):
	"""
	If the motor driver can't do anything, it raises an exception MotorException.
	The caller function should attempt to catch this in the event something goes wrong.
	"""
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()
	moveStarted = QtCore.pyqtSignal(float,float)
	position = QtCore.pyqtSignal(float)
	moveFinished = QtCore.pyqtSignal()

	def __init__(self,pvName):
		super().__init__()
		# Flag for init completion. Without this, callbacks will run before we've finished setting up and it will crash.
		self._initComplete = False
		# Triggers for movement. Movement set means we have told the motor to move from within this class.
		self._movementSet = False
		self._movementStarted = False
		# Save the pv base.
		self.pvBase = pvName
		# Initialisation vars.
		self._connectionStatus = True
		# Add all the pv's.
		self.pv = {}
		for pv in MOTOR_PVS:
			setattr(self,pv,epics.PV("{}.{}".format(self.pvBase,pv),
				auto_monitor=True,
				connection_callback=self._connectionMonitor
				)
			)
		# Add callback for positioning monitoring.
		self.RBV.add_callback(self._positionMonitor)
		# Add a callback for motion monitoring.
		self.MOVN.add_callback(self._movingMonitor)
		self.DMOV.add_callback(self._doneMovingMonitor)
		# Flag for init completion.
		self._initComplete = True

	def _connectionMonitor(self,*args,**kwargs):
		"""
		Update the device connection status.
		All PV's must be connected in order for the device to be considered connected.
		If any PV in the device is disconnected, the whole device is demmed disconnected.
		"""
		if not self._initComplete:
			# We haven't finished setting up the motor yet, don't do anything.
			return

		if ('pvname' in kwargs) and ('conn' in kwargs):
			# Update the device connection state (by testing all the devices pv's connection states).
			teststate = [kwargs['conn']]
			# N.B. Epics hasn't actually updated the pv.connected state of the motor sent to this function yet.
			# So instead, get status of every motor except the one sent to this function.
			for pv in [x for x in MOTOR_PVS if x!=kwargs['pvname'][kwargs['pvname'].find('.')+1:]]:
				testpv = getattr(self,pv)
				teststate.append(testpv.connected)
			self._connectionStatus = all(teststate)

		# Send out an appropriate signal.
		if self._connectionStatus:
			self.connected.emit()
		else:
			self.disconnected.emit()

	def _positionMonitor(self,*args,**kwargs):
		# Update the device's position.
		if ('pvname' in kwargs) and ('value' in kwargs):
			self.position.emit(float(kwargs['value']))

	def _movingMonitor(self,*args,**kwargs):
		""" MOVN watch dog. """
		# If it is moving and we have a move set, then we can say we have started the move.
		if bool(kwargs['value']) and self._movementSet: 
			self._movementStarted = True

	def _doneMovingMonitor(self,*args,**kwargs):
		""" A watchdog for movement. This callback is triggered by DMOV. """
		# If we have set a movement, have started the movement, and have finished it...
		if bool(kwargs['value']) and self._movementSet and self._movementStarted:
			# We are done moving... check it.
			self._checkMovement()
			# Reset the flags.
			self._movementSet = False
			self._movementStarted = False

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

		logging.debug(f"{self.pvBase}: Moving from {previousPosition:.3f} to {writeValue:.3f}.")

		if np.absolute(previousPosition - writeValue) < 0.002:
			# Do nothing.
			time.sleep(0.25)
			self.moveFinished.emit()
			return
		# Write the value if acceptable.
		if self.withinLimits(writeValue):
			# If the value is within the limits, write it.
			self.VAL.put(writeValue)
			# Say we have set the move.
			self._movementSet = True
			# Emit the move started signal.
			self.moveStarted.emit(float(previousPosition),float(writeValue))
		else:
			# It is outside the limits.
			raise MotorLimitException(f"{self.pvBase}: Value {writeValue:.3f} exceeds motor limits.")

	def withinLimits(self,value):
		return (value <= self.HLM.get() and value >= self.LLM.get())

	def _checkMovement(self,*args,**kwargs):
		# If we are done moving... get the write value and current positions.
		# previousPosition, expectedPosition = kwargs['data']

		# Clear the DMOV callbacks.
		# self.DMOV.clear_callbacks()
		# Get the expected and current positions.
		expectedPosition = self.VAL.get()
		currentPosition = self.RBV.get()

		if float(abs(expectedPosition - currentPosition)) > (10**(float(self.PREC.get()))+float(self.BDST.get())):
			# We are outside our precision range and backlash distance.
			# raise MotorException("The motor did not stop at the expected position of {:.3f}.".format(expectedPosition))
			logging.warning("{} did not stop at the expected position of {:.3f}. Instead stopped at {:.3f}.".format(self.pvBase,expectedPosition,currentPosition))
			self.error.emit()
		else:
			# Else we are successfull.
			time.sleep(0.25)
			self.moveFinished.emit()


# WORKPOINT_PVS = [
# 	'TCPAXIS1',
# 	'TCPAXIS2',
# 	'TCPAXIS3',
# 	'TOOL_NO',
# 	'TOOL_NO_RBV',
# 	'READ_TCP',
# 	'SET_TCP',
# 	'ZERO_TOOL',
# 	'ZERO_BASE',
# 	'MXA_STATUS',
# ]

# class workpoint(QtCore.QObject):
# 	"""
# 	This class allows us to set a workpoint on our device.
# 	Typically, this is used with robots and the workpoint = TCP.
# 	"""
# 	connected = QtCore.pyqtSignal()
# 	disconnected = QtCore.pyqtSignal()
# 	moveStarted = QtCore.pyqtSignal(float,float)
# 	position = QtCore.pyqtSignal(float)
# 	moveFinished = QtCore.pyqtSignal()

# 	def __init__(self,pvName):
# 		super().__init__()
# 		# Flag for init completion. Without this, callbacks will run before we've finished setting up and it will crash.
# 		self._initComplete = False
# 		# Save the pv base.
# 		self.pvBase = pvName
# 		# Initialisation vars.
# 		self._connectionStatus = True
# 		# Add all the pv's.
# 		self.pv = {}
# 		for pv in WORKPOINT_PVS:
# 			setattr(self,pv,epics.PV("{}.{}".format(self.pvBase,pv),
# 				auto_monitor=True,
# 				connection_callback=self._connectionMonitor
# 				)
# 			)
# 		# Add callback for positioning monitoring.
# 		# self.RBV.add_callback(self._positionMonitor)
# 		# Flag for init completion.
# 		self._initComplete = True

# 	def _connectionMonitor(self,*args,**kwargs):
# 		"""
# 		Update the device connection status.
# 		All PV's must be connected in order for the device to be considered connected.
# 		If any PV in the device is disconnected, the whole device is demmed disconnected.
# 		"""
# 		if not self._initComplete:
# 			# We haven't finished setting up the motor yet, don't do anything.
# 			return

# 		if ('pvname' in kwargs) and ('conn' in kwargs):
# 			# Update the device connection state (by testing all the devices pv's connection states).
# 			teststate = [kwargs['conn']]
# 			# N.B. Epics hasn't actually updated the pv.connected state of the motor sent to this function yet.
# 			# So instead, get status of every motor except the one sent to this function.
# 			for pv in [x for x in WORKPOINT_PVS if x!=kwargs['pvname'][kwargs['pvname'].find('.')+1:]]:
# 				testpv = getattr(self,pv)
# 				teststate.append(testpv.connected)
# 			self._connectionStatus = all(teststate)

# 		# Send out an appropriate signal.
# 		if self._connectionStatus:
# 			self.connected.emit()
# 		else:
# 			self.disconnected.emit()

# 	def isConnected(self):
# 		# Return if we are connected or not.
# 		return self._connectionStatus

# 	def reconnect(self):
# 		for pv in WORKPOINT_PVS:
# 			epicspv = getattr(self,pv)
# 			try:
# 				epicspv.reconnect()
# 			except:
# 				raise MotorException("Failed to force {} to reconnect.".format(pv))


VELOCITY_PVS = ['Velocity','Acceleration']

class velocityController(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	speedChanged = QtCore.pyqtSignal(float,float)
	error = QtCore.pyqtSignal()

	def __init__(self,ports):
		super().__init__()
		self._initComplete = False
		self._connectionStatus = False
		# Setup the Epics PVs.
		self.pv = {}
		# Requires:
		# Velocity, Acceleration
		for key,val in ports.items():
			if key in VELOCITY_PVS:
				setattr(self,key,epics.PV(val,
					auto_monitor=True,
					connection_callback=self._connectionMonitor
					)
				)

		# Add callback for value monitoring.
		self.Velocity.add_callback(self._velocityMonitor)
		self.Acceleration.add_callback(self._velocityMonitor)
		# Finished initialisation.
		self._initComplete = True

	def _connectionMonitor(self,*args,**kwargs):
		"""
		Update the device connection status.
		All PV's must be connected in order for the device to be considered connected.
		If any PV in the device is disconnected, the whole device is demmed disconnected.
		"""
		if not self._initComplete:
			# We haven't finished setting up the motor yet, don't do anything.
			return

		if ('pvname' in kwargs) and ('conn' in kwargs):
			# Update the device connection state (by testing all the devices pv's connection states).
			teststate = [kwargs['conn']]
			# N.B. Epics hasn't actually updated the pv.connected state of the motor sent to this function yet.
			# So instead, get status of every motor except the one sent to this function.
			searchPV = kwargs['pvname']
			for key,val in self.pv.items():
				if val == searchPV:
					searchPVkey = val
			# List of PV's that aren't the one sent to this function.
			for pv in [val for key,val in self.pv if key != searchPVkey]:
				testpv = getattr(self,pv)
				teststate.append(testpv.connected)
			self._connectionStatus = all(teststate)

		# Send out an appropriate signal.
		if self._connectionStatus:
			self.connected.emit()
		else:
			self.disconnected.emit()

	def isConnected(self):
		# Return if we are connected or not.
		return self._connectionStatus

	def setSpeed(self,value):
		""" Set the velocity. """
		logging.debug(f"Setting velocity to {value}.")
		self.Velocity.put(float(value))

	def getSpeed(self):
		""" Get the velocity. """
		return self.Velocity.get()

	def setAcceleration(self,value):
		""" Set the acceleration. """
		self.Acceleration.put(float(value))

	def getAcceleration(self,value):
		""" Get the acceleration. """
		return self.Acceleration.get()

	def _velocityMonitor(self,*args,**kwargs):
		""" Update the (velocity,acceleration). """
		if ('pvname' in kwargs) and ('value' in kwargs):
			try:
				velocity = float(self.Velocity.get())
				acceleration = float(self.Acceleration.get())
			except:
				velocity = -1
				acceleration = -1
			# Emit the signal.
			self.speedChanged.emit(velocity,acceleration)

	def reconnect(self):
		for pv in VELOCITY_PVS:
			epicspv = getattr(self,pv)
			try:
				epicspv.reconnect()
			except:
				raise MotorException("Failed to force {} to reconnect.".format(pv))