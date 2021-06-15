import epics
import numpy as np
import logging
import time
import h5py as hdf
from PyQt5 import QtCore
import os

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
	detectorReady = QtCore.pyqtSignal()
	imageAcquired = QtCore.pyqtSignal(str)

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
		self.attributesfile = str(config.attributesfile)
		# Initialisation vars.
		self._connectionStatus = False
		self.arraySize = np.array([0,0])
		self.buffer = {}
		# Flood fields and dark fields.
		self.floodfield = None
		self.darkfield = None
		# Add all the pv's.
		self.pv = {}
		self.blockSignals(True)
		for name,pv in self.pvs.items():
			setattr(self,name,epics.PV(f"{self.port}:{pv}",
				auto_monitor=True,
				connection_callback=self._connectionMonitor
				)
			)
		self.blockSignals(False)
		# Set up the detector preferences. Should link to config file or settings?
		# self.setup()
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
			for pv in [k for k,v in self.pvs.items() if v not in kwargs['pvname'][kwargs['pvname'].find(':')+1:]]:
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

	def setup(self):
		# Set up the detector.
		if not self._connectionStatus:
			raise DetectorException("Cannot continue with setup as not all PV's are connected.")
		# Here we should also allow for flipping the image to orientate it correctly.
		self.Acquire.put(0)
		self.AcquireTime.put(0.1)
		self.AcquirePeriod.put(0.0)
		self.ImageMode.put('Single')
		self.AutoSave.put('No')
		self.ArrayCounter.put(0)
		self.NumberOfImages.put(1)
		# Get an image so area detector can get array sizes etc. for ROI.
		self.Acquire.put(1)
		time.sleep(1)
		# Get the array size.
		self.arraySize[0] = self.RoiSizeX.get()
		self.arraySize[1] = self.RoiSizeY.get()

	def setupFFC(self):
		# Stop any existing imaging.
		self.Acquire.put(0)
		# Set new exposure up.
		self.AcquireTime.put(0.1)
		self.AcquirePeriod.put(0.0)
		self.ImageMode.put('Single')
		self.AutoSave.put('No')
		self.ArrayCounter.put(0)
		self.NumberOfImages.put(1)
		self.Acquire.put(1)
		time.sleep(0.2)
		# Get the array size.
		self.arraySize[0] = self.RoiSizeX.get()
		self.arraySize[1] = self.RoiSizeY.get()

	def acquireFFC(self,mode):
		""" Acquire a dark field image. """
		# Acquire an image.
		self.Acquire.put(1)
		time.sleep(0.2)
		# Get the image.
		arr = self.RoiData.get().reshape(tuple(self.arraySize[::-1]))
		# Set the field correction.
		if mode == 'dark':
			self.darkfield = arr
			logging.info("Acquired Dark Field.")
			self.imageAcquired.emit('darkField')
		elif mode == 'flood':
			self.floodfield = arr
			logging.info("Acquired Flood Field.")
			self.imageAcquired.emit('floodField')

	def setupDynamicScan(self,distance,speed,uid="temp"):
		""" Setup a dynamic image in Area Detector using HDF. """
		logging.warning("This requires a ROI to be setup on the detector.")
		# Total imaging time.
		time = distance/speed
		# Number of pixels to read out.
		self.arraySize[0] = self.RoiSizeX.get()
		self.arraySize[1] = self.RoiSizeY.get()
		readoutHeight = self.arraySize[1]
		pixelSize = self.pixelSize[1]
		# Calculate detector settings.
		acquireTime = (readoutHeight*pixelSize)/speed
		acquirePeriod = acquireTime
		numberOfImages = int(time/acquireTime + 1)

		# Stop any acquisitions.
		self.Acquire.put(0,wait=True)
		# Setup image processing.
		self.HDFenable.put(1,wait=True)
		self.TIFFenable.put(0,wait=True)
		# Set vars.
		self.AcquireTime.put(acquireTime,wait=True)
		self.AcquirePeriod.put(acquirePeriod,wait=True)
		self.NumberOfImages.put(numberOfImages,wait=True)
		self.ImageMode.put(1,wait=True)
		self.ArrayCounter.put(0,wait=True)
		# Turn off tiff saving.
		self.TIFFautosave.put(False,wait=True)
		# Setup HDF imaging.
		self.HDFcapture.put(0,wait=True)
		self.HDFfilePath.put(self.iocpath,wait=True)
		self.HDFfileName.put(uid,wait=True)
		self.HDFautosave.put(True,wait=True)
		self.HDFfileWriteMode.put(2,wait=True)
		self.HDFnumberOfImages.put(numberOfImages,wait=True)
		self.HDFautoIncrement.put(False,wait=True)
		self.HDFarrayPort.put(self.roiport,wait=True)
		if self.attributesfile != "":
			self.HDFattributes.put(self.iocpath+self.attributesfile,wait=True)
		# Start the capture process. Don't use wait here, for some reason it takes an eternity to return.
		self.HDFcapture.put(1)
		logging.info("HDF capture process started... awaiting images.")
		self.detectorReady.emit()

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
		# Wait a second for IOC to close the file.
		time.sleep(0.1)
		# Read the HDF5 file.
		fn = f'{self.localpath}{uid}.hdf'
		f = hdf.File(fn,'r')
		# Grab the image data.
		arrData = f['entry']['data']['data']

		if mode == 'dynamic':
			# Get the zpos as well.
			zPos = np.array(f['entry']['instrument']['NDAttributes']['Z'])
			# logging.debug(f"zPos: {zPos}")
			# Filter the z positions so they are averaged over 3 places.
			zPos_filtered = np.convolve(zPos, np.ones(3)/3,'valid')
			zPos_diff = np.absolute(np.diff(zPos_filtered))
			zPos_diff = np.r_[zPos_diff[0],zPos_diff,zPos_diff[-1]]
			# Find the positions that exceed the mean +/- 2 std deviations.
			mean = np.mean(zPos_diff[np.where(zPos_diff!=0)])
			std = np.std(zPos_diff[np.where(zPos_diff!=0)])
			invalidPositions = [
				np.where(zPos_diff < mean - 2*std),
				np.where(zPos_diff > mean + 2*std)
			]
			invalidPositions = np.hstack(invalidPositions).ravel()
			# Find the start and finish indices of our valid image.
			if len(invalidPositions) == 0: 
				startIdx = 0
				finishIdx = len(zPos_diff)
			else:
				theSplit = np.split(invalidPositions, np.where(np.diff(invalidPositions) != 1)[0]+1)
				if len(theSplit) == 1:
					# We only have one invalid region at the start or the end?
					if 0 in theSplit[0]:
						startIdx = theSplit[0][-1]
						finishIdx = len(zPos_diff)
					elif len(zPos_diff)-1 in theSplit[0]:
						startIdx = 0
						finishIdx = theSplit[0][0]
				else:
					# We have two regions.
					if 0 in theSplit[0]:
						startIdx = theSplit[0][-1]
					else:
						startIdx = 0
					if len(zPos_diff)-1 in theSplit[-1]:
						finishIdx = theSplit[-1][0]
					else:
						finishIdx = len(zPos_diff)
			# Finalize the array and zrange.
			arrData = arrData[startIdx:finishIdx]
			zRange = np.array([zPos[startIdx], zPos[finishIdx]])
			# logging.debug(f"zRange: {zRange}")

		# Close the file.
		f.close()
		# Delete the HDF5 file.
		os.remove(fn)

		# Apply flat field corrections (if available):
		for i in range(len(arrData)):
			# Do FFC before image gymnasticks (they are unadulterated fields).
			if (self.floodfield is not None) and (self.darkfield is not None):
				arrData[i] = (arrData[i]-self.darkfield)/(self.floodfield-self.darkfield)
			# Do appropriate image gymnastics.
			if self.flipud: arrData[i] = np.flipud(arrData[i])
			if self.fliplr: arrData[i] = np.fliplr(arrData[i])
		# Stack the array data.
		arr = np.vstack(arrData)
		# Handle any weird values.
		arr = np.nan_to_num(arr, nan=0, posinf=0, neginf=0)
		# Get the Z offset from the imaging system.
		zOffset = float(metadata['Image Offset'][2])

		# Create metadata and return image.
		if mode == 'static':
			# Calculate the extent of the image.
			l,t = self.pixelSize*self.isocenter
			r,b = np.r_[l,t] - self.arraySize*self.pixelSize
			t -= zOffset
			b -= zOffset
			extent = [l,r,b,t]
			# Create metadata.
			metadata.update({
				'Pixel Size': self.pixelSize,
				'Image Isocenter': self.isocenter,
				'Extent': extent,
				'Mode': mode,
				'UUID': uid,
			})

		elif mode == 'dynamic':
			# Find the z values of the image.
			z = zRange - zOffset
			# Calculate the extent of the image.
			t = z[1] + self.isocenter[1]*self.pixelSize[1]
			b = z[0] - self.isocenter[1]*self.pixelSize[1]
			l = self.isocenter[0]*self.pixelSize[0]
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
		logging.debug(f"Adding image to buffer: {uid}")
		# Save everything in the buffer.
		self.buffer[uid] = (arr,metadata)
		# Let the world know we've finished the image capture.
		self.imageAcquired.emit(uid)

	def getImage(self,uid):
		# Get the data from the buffer and delete it from the buffer.
		data = self.buffer[uid]
		del self.buffer[uid]
		# Return the data from the buffer.
		return data