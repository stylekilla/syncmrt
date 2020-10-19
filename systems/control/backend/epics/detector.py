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

__all__ = ['detector']

DETECTOR_PVS = {
	'Acquire': 'CAM:Acquire',
	'AcquireTime': 'CAM:AcquireTime',
	'AcquirePeriod': 'CAM:AcquirePeriod',
	'ArrayCounter': 'CAM:ArrayCounter',
	'NumImages': 'CAM:NumImages',
	'ImageMode': 'CAM:ImageMode',
	'AutoSave': 'TIFF:AutoSave',
	'DataType': 'IMAGE:DataType_RBV',
	'ArraySize0': 'IMAGE:ArraySize0_RBV',
	'ArraySize1': 'IMAGE:ArraySize1_RBV',
	'ArrayData': 'IMAGE:ArrayData',
}

class DetectorException(Exception):
	""" Raised to indicate a problem with a detector """
	def __init__(self, msg, *args):
		Exception.__init__(self, *args)
		self.msg = msg
	def __str__(self):
		# Debugging logs included.
		logging.debug(self.msg)
		return str(self.msg)

class detector(QtCore.QObject):
	"""
	If the motor driver can't do anything, it raises an exception DetectorException.
	The caller function should attempt to catch this in the event something goes wrong.
	"""
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	imageAcquired = QtCore.pyqtSignal()

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
		for name,pv in DETECTOR_PVS.items():
			setattr(self,name,epics.PV("{}:{}".format(self.pvBase,pv),
				auto_monitor=True,
				connection_callback=self._connectionMonitor
				)
			)
		# Set up the detector preferences. Should link to config file or settings?
		self.setup()
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
			pvname = kwargs['pvname'][kwargs['pvname'].find(':')+1:]
			petname = DETECTOR_PVS.get(pvname)
			# for pv in [x for x in DETECTOR_PVS.values() if x!=kwargs['pvname'][kwargs['pvname'].find('.')+1:]]:
			for name,pv in DETECTOR_PVS.items():
				if name == petname:
					# Don't update this pv, we already know it's status.
					continue
				else:
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
		# Reconnect the PV's.
		for pv in DETECTOR_PVS.values():
			epicspv = getattr(self,pv)
			try:
				epicspv.reconnect()
			except:
				raise DetectorException("Failed to force {} to reconnect.".format(pv))
		# Run the setup again.
		self.setup()

	def setup(self):
		# Set up the detector.
		logging.warning("Setting up the detector with hard coded defaults.")
		# Here we should also allow for flipping the image to orientate it correctly.
		self.AcquireTime.put(0.1)
		self.AcquirePeriod.put(0.1)
		self.ImageMode.put('Single')
		self.AutoSave.put('No')
		self.ArrayCounter.put(0)
		self.NumImages.put(1)

	def set(self,parameter,value):
		# If the parameter is known to the backend...
		if parameter in DETECTOR_PVS:
			# Grab the PV.
			pv = DETECTOR_PVS[parameter]
			epicspv = getattr(self,pv)
			# Assign the value (doesn't do any error checking).
			epicspv.put(value)
			# Return successful.
			return True
		else:
			raise DetectorException("Could not set unknown parameter {} on device {}.".format(parameter,self.pvBase))

	def acquire(self):
		if self._connectionStatus:
			# Run Acquire.
			self.Acquire.put(1,wait=True)
			# Once finished grab the frame and return it.
			image = self.ArrayData.get()
			logging.debug("This is set to ArraySize0 and ArraySize1... should this not be X and Y? Is there something wrong with the IOC?")
			return image.reshape(self.ArraySize0,self.ArraySize1)
		else:
			raise DetectorException("Detector not connected. Cannot acquired image.")