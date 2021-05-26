import epics
import numpy as np
import logging
import time
import h5py as hdf
from PyQt5 import QtCore

"""
We don't use the device classes due to a lack of callback functionality and you can't check things like
the connection state of the pv's/device etc. 
Therefore, we implement all that functionality ourselves.
"""

__all__ = ['detector']

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
	Area detector must be configured to use HDF with ROI 1.
	"""
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	imageAcquired = QtCore.pyqtSignal(str)
	detectorReady = QtCore.pyqtSignal()

	def __init__(self,config):
		super().__init__()
		# Flag for init completion. Without this, callbacks will run before we've finished setting up and it will crash.
		self._initComplete = False
		# Save the pv data.
		self.port = str(config.port)
		self.pvs = config.DETECTOR_PVS
		# Save the file paths (locally and for the area detector ioc).
		self.iocpath = str(config.iocpath)
		self.localpath = str(config.localpath)
		# Save other detector attributes.
		self.flipud = bool(config.flipud)
		self.fliplr = bool(config.fliplr)
		self.pixelSize = np.array(config.pixelSize)
		self.isocenter = np.array(config.isocenter)
		self.roiport = str(config.roiPort)
		# Initialisation vars.
		self._connectionStatus = True
		self.arraySize = np.array([0,0])
		self.buffer = {}
		# Add all the pv's.
		self.pv = {}
		for name,pv in self.pvs.items():
			setattr(self,name,epics.PV(f"{port}:{pv}",
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

		if ('port' in kwargs) and ('conn' in kwargs):
			# Update the device connection state (by testing all the devices pv's connection states).
			teststate = [kwargs['conn']]
			# N.B. Epics hasn't actually updated the pv.connected state of the motor sent to this function yet.
			# So instead, get status of every motor except the one sent to this function.
			for pv in [x for x in DETECTOR_PVS if x not in kwargs['port'][kwargs['port'].rfind(':')+1:]]:
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
		for pv in self.pvs:
			epicspv = getattr(self,pv)
			try:
				epicspv.reconnect()
			except:
				raise DetectorException("Failed to force {} to reconnect.".format(pv))
		# Run the setup again.
		self.setup()

	def setup(self):
		# Set up the detector.
		# Here we should also allow for flipping the image to orientate it correctly.
		self.Acquire.put(0)
		self.AcquireTime.put(0.1)
		self.AcquirePeriod.put(0.0)
		self.ImageMode.put('Single')
		self.AutoSave.put('No')
		self.ArrayCounter.put(0)
		self.NumImages.put(1)
		# Get an image so area detector can get array sizes etc. for ROI.
		self.Acquire.put(1)
		time.sleep(1)
		# Get the array size.
		self.arraySize[0] = self.RoiSizeX.get()
		self.arraySize[1] = self.RoiSizeY.get()

	def setupDynamicScan(self,distance,speed,uid="temp"):
		""" Setup a dynamic image in Area Detector using HDF. """
		logging.warning("This requires a ROI to be setup on the detector.")
		# Total imaging time.
		time = distance/speed
		# Number of pixels to read out.
		logging.critical("Need to get ROI value.")
		readoutHeight = 10
		# readoutHeight = self.getRoiSize()
		pixelSize = self.pixelSize
		# Calculate detector settings.
		acquireTime = (readoutHeight*pixelSize)/speed
		acquirePeriod = acquireTime
		numberOfImages = int(time/acquireTime + 1)

		# Stop any acquisitions.
		self.Acquire.put(0)
		# Set vars.
		self.AcquireTime.put(acquireTime)
		self.AcquirePeriod.put(acquirePeriod)
		self.NumberOfImages.put(numberOfImages)
		self.ImageMode.put(1)
		self.ArrayCounter.put(0)
		# Turn off tiff saving.
		self.TIFFautosave.put(False)
		# Get the array size.
		self.arraySize[0] = self.RoiSizeX.get()
		self.arraySize[1] = self.RoiSizeY.get()
		# Setup HDF imaging.
		self.HDFcapture.put(0)
		self.HDFfilePath.put(self.iocpath)
		self.HDFfileName.put(uid)
		self.HDFautosave.put(True)
		self.HDFfileWriteMode.put(2)
		self.HDFnumberOfImages.put(numberOfImages)
		self.HDFautoIncrement.put(False)
		self.HDFarrayPort.put(self.roiport)
		self.HDFattributes.put(self.iocpath+'attributes.xml')
		# Start the capture process.
		self.HDFcapture.put(1)
		logging.info("HDF capture process started... awaiting images.")

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
			raise DetectorException("Could not set unknown parameter {} on device {}.".format(parameter,self.port))

	def acquire(self,mode,uid,metadata={}):
		""" Acquires an image (or series of image). Really it just activates the camera acquire button. """
		# Sanity checks.
		if not self._connectionStatus:
			raise DetectorException("Detector not connected. Cannot acquire image.")
		if mode not in ['static','dynamic']:
			raise TypeError(f"Unknown acquire mode: {mode}.")

		# Tell the detector to acquire.
		self.Acquire.put(1)
		# Sleep to allow acquire to trigger.
		time.sleep(1)
		# While it is acquiring, do nothing.
		while self.HDFcapture.get():
			pass

		# Read the HDF5 file.
		f = hdf.File(f'{self.localpath}{uid}.hdf','r')
		# Grab the image data.
		arr = np.vstack(f['entry']['data']['data'])
		# Do appropriate image gymnastics.
		if self.flipud: arr = np.flipud(arr)
		if self.fliplr: arr = np.fliplr(arr)

		# Create metadata and return image.
		if mode == 'static':
			# Calculate the extent of the image.
			l,t = self.pixelSize*self.imageIsocenter
			r,b = np.r_[l,t] - self.arraySize*self.pixelSize
			extent = [l,r,b,t]
			# Create metadata.
			metadata.update({
				'Pixel Size': self.pixelSize,
				'Image Isocenter': self.imageIsocenter,
				'Extent': extent,
				'Mode': mode,
				'UUID': uid,
			})

		elif mode == 'dynamic':

			logging.critical("Need to do image clean up here!... maybe in another subroutine.")
			self._stitchValid(arr,z)

			# Find the z values of the image.
			z = f['entry']['attributes']['z']
			# Calculate the extent of the image.
			t = z[0] + self.imageIsocenter[1]*self.pixelSize[1]
			b = z[-1] - self.imageIsocenter[1]*self.pixelSize[1]
			l = self.imageIsocenter[0]*self.pixelSize[0]
			r = l - self.arraySize[0]*self.pixelSize[0]
			extent = [l,r,b,t]
			# Create metadata.
			metadata.update({
				'Pixel Size': self.pixelSize,
				'Extent': extent,
				'Mode': mode,
				'UUID': uid,
			})
			
		# We can't send the image + metadata over pyqt signals unfortunately.
		# We will have to come back and manually get it.
		# Save everything in the buffer.
		self.buffer[uid] = (arr,metadata)
		# Let the world know we've finished the image capture.
		self.imageAcquired(uid)

	def getImage(self,uid):
		# Get the data from the buffer and delete it from the buffer.
		data = self.buffer[uid]
		del self.buffer[uid]
		# Return the data from the buffer.
		return data

	def getRoiSize(self):
		logging.critical("detector.getRoiSize(): Not implemented yet.")
		return 0