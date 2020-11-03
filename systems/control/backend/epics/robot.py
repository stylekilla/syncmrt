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

__all__ = ['tcp']

TCP_PVS = [
	'TCP_AXIS1',
	'TCP_AXIS2',
	'TCP_AXIS3',
	'TCP_AXIS_RBV1',
	'TCP_AXIS_RBV2',
	'TCP_AXIS_RBV3',
	'TOOL_NO',
	'TOOL_NO_RBV',
	'READ_TCP',
	'SET_TCP',
	'ZERO_TOOL'
]

class RobotException(Exception):
	""" Raised to indicate a problem with a motor """
	def __init__(self, msg, *args):
		Exception.__init__(self, *args)
		self.msg = msg
	def __str__(self):
		# Debugging logs included.
		logging.debug(self.msg)
		return str(self.msg)

class tcp(QtCore.QObject):
	"""
	Set the TCP for the robot.
	"""
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()
	setFinished = QtCore.pyqtSignal()

	def __init__(self,pvName):
		super().__init__()
		# Flag for init completion. Without this, callbacks will run before we've finished setting up and it will crash.
		self._initComplete = False
		# Save the pv base.
		self.pvBase = pvName
		# Initialisation vars.
		self._connectionStatus = True
		# Add all the pv's.
		self.pv = {}
		for pv in TCP_PVS:
			setattr(self,pv,epics.PV("{}:{}".format(self.pvBase,pv),
				auto_monitor=True,
				connection_callback=self._connectionMonitor
				)
			)
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
			for pv in [x for x in TCP_PVS if x!=kwargs['pvname'][kwargs['pvname'].rfind(':')+1:]]:
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

	def reconnect(self):
		for pv in TCP_PVS:
			epicspv = getattr(self,pv)
			try:
				epicspv.reconnect()
			except:
				raise RobotException("Failed to force {} to reconnect.".format(pv))

	def read(self):
		""" Read the current TCP settings on the robot. """
		# Just use whatever tool is selected on the robot.
		self.READ_TCP.put(1,wait=True)
		# Create a quick loop.
		for i in range(1000): pass
		# Return the new values of the TCP axes.
		return np.array([self.TCP_AXIS_RBV1.get(),self.TCP_AXIS_RBV2.get(),self.TCP_AXIS_RBV3.get()])

	def offset(self,offset):
		""" Offset the TCP of the robot such that all movement now happens about that point. """
		# First read the TCP.
		tcp_old = self.read()
		# Calculate the new tcp positions.
		tcp_new = tcp_old + offset
		# Set them.
		self.TCP_AXIS1.put(tcp_new[0],wait=True)
		self.TCP_AXIS2.put(tcp_new[1],wait=True)
		self.TCP_AXIS3.put(tcp_new[2],wait=True)
		# Write it to the robot.
		self.SET_TCP.put(1,wait=True)
		for i in range(20): time.sleep(0.1)
		# Read it back... unecessary but whatevs.
		self.READ_TCP.put(1,wait=True)
		for i in range(20): time.sleep(0.1)
		# Stop the robot to force it to reset it's positions. This brings it into line with the updated coordinate system.
		logging.info("Running motor stop.")
		epics.caput("SR08ID01ROB01:MOTOR_X:STOP",1)
		for i in range(20): time.sleep(0.1)

	def set(self,position):
		""" Offset the TCP of the robot such that all movement now happens about that point. """
		# Set them.
		self.TCP_AXIS1.put(position[0],wait=True)
		self.TCP_AXIS2.put(position[1],wait=True)
		self.TCP_AXIS3.put(position[2],wait=True)
		# Write it to the robot.
		self.SET_TCP.put(1,wait=True)
		# Create a quick loop.
		for i in range(20): time.sleep(0.1)
		self.READ_TCP.put(1,wait=True)

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
