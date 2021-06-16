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

__all__ = ['source']

SOURCE_PVS = ['On','Off','Status','ShutterOpen','ShutterClose','ShutterStatus']

class source(QtCore.QObject):
	# Beam signals.
	on = QtCore.pyqtSignal()
	off = QtCore.pyqtSignal()
	state = QtCore.pyqtSignal(bool)
	# Shutter signals.
	shutterOpen = QtCore.pyqtSignal()
	shutterClosed = QtCore.pyqtSignal()
	shutterState = QtCore.pyqtSignal(bool)
	# Connection signals.
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()

	def __init__(self,name,ports):
		super().__init__()
		# Set the name.
		self.name = str(name)
		self.ports = ports
		# Flag for init completion. Without this, callbacks will run before we've finished setting up and it will crash.
		self._initComplete = False
		# Initialisation vars.
		self._connectionStatus = False
		# Add all the pv's.
		for name,port in self.ports.items():
			if name in SOURCE_PVS:
				setattr(self,name,epics.PV(port,
					auto_monitor=True,
					connection_callback=self._connectionMonitor
					)
				)
		# Add callback for source monitoring.
		self.Status.add_callback(self._beamStatusMonitor)
		self.ShutterStatus.add_callback(self._shutterStatusMonitor)
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
			callbackPV = kwargs['pvname']
			for name,port in self.ports.items():
				if port == callbackPV:
					callbackPVname = name
			# List of PV's that aren't the one sent to this function.
			for pv in [key for key,val in self.ports.items() if key != callbackPVname]:
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

	def _beamStatusMonitor(self,*args,**kwargs):
		# Update the device's position.
		if ('pvname' in kwargs) and ('value' in kwargs):
			# State is 3 when beam is ON.
			state = bool(int(kwargs['value'])==3)
			# Emit the state signal.
			self.state.emit(state)
			# Also emit on/off toggle signals.
			if state:
				self.on.emit()
			else:
				self.off.emit()

	def _shutterStatusMonitor(self,*args,**kwargs):
		# Update the device's position.
		if ('pvname' in kwargs) and ('value' in kwargs):
			state = bool(int(kwargs['value'])==3)
			# Emit the state signal.
			self.shutterState.emit(state)
			# Also emit on/off toggle signals.
			if state:
				self.shutterOpen.emit()
			else:
				self.shutterClosed.emit()

	def turnOn(self):
		""" Turn beam on. """
		if self.Status.get() == 2:
			# If beam is off, turn on.
			self.On.put(1)
		else:
			self.on.emit()

	def turnOff(self):
		""" Turn beam off. """
		if self.Status.get() == 3:
			# If beam is on, turn off.
			self.Off.put(1)
		else:
			# Already off.
			self.off.emit()
	
	def openShutter(self):
		""" Open the shutter. """
		if self.ShutterStatus.get() == 2:
			# Open the shutter.
			self.ShutterOpen.put(1)
		else:
			# Already open.
			self.shutterOpen.emit()

	def closeShutter(self):
		""" Close the shutter. """
		if self.ShutterStatus.get() == 3:
			# If open, close it.
			self.ShutterClose.put(1)
		else:
			# Already closed.
			self.shutterClosed.emit()