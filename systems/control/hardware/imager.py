from systems.control.hardware.detector import detector
from file import hdf5
from PyQt5 import QtCore
import numpy as np
import csv, os
import logging

class Imager(QtCore.QObject):
	"""
	A QObject class containing information about imager hardware (detector + source).

	Parameters
	----------
	database : str
		A link to a *.csv file containing information about the hardware.
	config : str
		Pass the configuration file section relating to the imager.
	ui : QtWidget
		Unused. Should allow for imager controls to be set up and placed within the gui by using the ui to set a layout and imager child widgets.

	Attributes
	----------
	imageAcquired : pyqtSignal(int)
		An image has been acquired by the imager.
	newImageSet : pyqtSignal(str, int)
		An image set has been acquired by the imager with set `name` and `n` images.
	detector : object
		A synctools.hardware.detector object.
	file : object
		A synctools.fileHandler.hdf5.file object. Patient HDF5 file for storing x-ray images in.
	buffer : list
		A buffer for image frames, these later get released as a image set (1 or 2 images).
	sid : float
		Source to Imager Distance in mm.
	sad : float 
		Source to Axis Distance in mm.
	detectors : dict
		Dictionary of available detectors in the system and their Epics PV's.
	deviceList : set
		A list of all the detector names available to the system.
	"""
	connected = QtCore.pyqtSignal(bool)
	imageAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str,int)

	def __init__(self,database,config,ui=None,backendThread=None):
		super().__init__()
		# Information
		self.detector = None
		self.name = None
		# File.
		self.file = None
		self.config = config
		# Image buffer for set.
		self.buffer = []
		self._stitchBuffer = []
		self.metadata = []
		# System properties.
		# self.sid = self.config.sid
		# self.sad = self.config.sad
		# Connection status, True = Connected, False = Disconnected.
		self._connectionStatus = False
		# Save the backend thread (if any).
		self.backendThread = backendThread


		# Open CSV file
		f = open(database)
		r = csv.DictReader(f)
		# Devices is the total list of all devices in the database.
		self.detectors = {}
		self.deviceList = set()
		for row in r:
			# Check for commented out lines first.
			if row['Detector'].startswith('--'): 
				continue
			else:
				self.detectors[row['Detector']] = row['PV Root']
				self.deviceList.add(row['Detector'])

	def load(self,name):
		"""
		Load a detector into the imager configuration.

		Attributes
		----------
		name : str
			The name of the detector to look up in the database file.
		"""
		logging.info("Loading the {} detector with settings from `settings.cfg`.".format(name))
		if name in self.deviceList:
			# Update our name accordingly.
			self.name = name
			# Create the new detector and load config settings.
			newDetector = detector(
				name,
				self.detectors[name],
				backendThread=self.backendThread
			)
			newDetector.imageIsocenter = self.config.isocenter
			newDetector.pixelSize = self.config.pixelSize
			# Signals and slots.
			newDetector.connected.connect(self._connectionMonitor)
			newDetector.disconnected.connect(self._connectionMonitor)
			# Assign ourselves the new detector.
			self.detector = newDetector
			
	def reconnect(self):
		""" Reconnect the detector controller to Epics. Use this if the connection dropped out. """
		if self.detector is not None:
			self.detector.reconnect()

	def isConnected(self):
		if self.detector is None:
			return False
		else:
			return self.detector.isConnected()

	def _connectionMonitor(self):
		# Connection monitor for the detector.
		self._connectionStatus = self.detector.isConnected()
		# Send out an appropriate signal.
		self.connected.emit(self._connectionStatus)

	def setImagingParameters(self,params):
		""" As they appear on PV's. """
		self.detector.setParameters(params)

	def acquire(self,index,metadata,continuous=False):
		"""
		Grabs a single image frame and loads it into the buffer. 

		Parameters
		----------
		index : int
			The `index` of the image (1 or 2).
		metadata : dict
			A dictionary of arguments that should be written into the HDF5 file as image attributes.
		continuous : bool
			Continuous scan, set to False by default.
		
		Returns
		-------
		imageAcquired(i) : pyqtSignal
			Emits a signal saying that the image index `i` has been added to the image buffer with `(array, metadata)`.
		"""
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return None
		# Get the image and update the metadata.
		# _data = self.detector.acquire(continuous)
		_data = self.detector.acquire()
		metadata.update(_data[1])
		image = _data[0]
		# Calculate the extent.
		l = -self.detector.imageIsocenter[1]*self.detector.pixelSize[1]
		r = l + image.shape[1]*self.detector.pixelSize[1]
		t = self.detector.imageIsocenter[0]*self.detector.pixelSize[0]
		b = t - image.shape[0]*self.detector.pixelSize[0]
		extent = (l,r,b,t)
		# Add the transformation matrix into the images frame of reference.
		# Imagers FOR is a RH-CS where +x propagates down the beamline.
		M = np.identity(3)
		t = np.deg2rad(float(metadata['Image Angle']))
		rz = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		M = rz@M
		metadata.update({
				'Extent': extent,
				'M':M,
				'Mi':np.linalg.inv(M),
			})
		# Append the image and metada to to the buffer.
		self.buffer.append((_data[0],metadata))
		# Emit a signal saying we have acquired an image.
		self.imageAcquired.emit(index)

	def acquireStep(self,beamHeight):
		"""
		Grabs a small vertical section of a larger image. 

		Parameters
		----------
		beamHeight : float
			The vertical height of the beam used for imaging. This will specify the region of the image to acquire.

		Returns
		-------
		imageAcquired(-1) : pyqtSignal
			Emits signal with -1 to state part of an image has been acquired.
		"""
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return None
		# Define the region of interest.
		t = int(self.detector.imageIsocenter[0] - (beamHeight/self.detector.pixelSize[0])/2)
		b = int(self.detector.imageIsocenter[0] + (beamHeight/self.detector.pixelSize[0])/2)
		logging.debug("Top and bottom indexes of array are: {}t {}b.".format(t,b))
		# Get the image ROI and add it to the stitch buffer.
		self._stitchBuffer.append(list(self.detector.acquire()))
		self._stitchBuffer[-1][0] = self._stitchBuffer[-1][0][t:b,:]
		# Emit a signal saying we have acquired an image.
		logging.info("Step image acquired. Stitch buffer has {} elements.".format(len(self._stitchBuffer)))
		self.imageAcquired.emit(-1)

	def prepareScan(self,beamHeight,speed):
		"""
		Sets up a continuous scan over `time`.

		Parameters
		----------
		time : float
			The time 

		"""		
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return
		# Set detector acusition time. ROI? How to port images straight to me?
		kwargs = {
			'AcquireTime':		beamHeight/speed,
			'AcquirePeriod':	0,
			'ImageMode':		'Continuous',
		}
		self.detector.setParameters(kwargs)


	def stitch(self,index,metadata,z1,z2):
		"""
		The `imager._stitchBuffer` is stitched together and the complete image is sent to the `imager.buffer` along with its finalised metadata.
		Stitching assumes the middle of the beam window is the middle of the beam. No offset.

		Parameters
		----------
		index : int
			Index of the image to be stitched (1 or 2).
		metadata : dict
			The metadata of the image to be included in the HDF5 file as image attributes.
		z : float
			The `z` (vertical) position of the patient before imaging.
		z1 : float
			The top position of the patient at the start of imaging.
		z2 : float
			The bottom position of the patient at the end imaging.
		"""
		# Metadata
		finish = self._stitchBuffer[-1][1]
		metadata.update(finish)
		logging.critical("Stitching image {}. The pre-imaging height positions are [{}, {}]".format(index,z1,z2))

		# Stitch the image together.
		images = []
		for i in reversed(range(0,len(self._stitchBuffer))):
			images.append(self._stitchBuffer[i][0])
		images = tuple(images)
		image = np.vstack(images)

		# Calculate the extent.
		logging.critical("Extent calculation for stitching is currently wrong. Unfinished")
		l = (image.shape[1]/2)*self.detector.pixelSize[1]
		r = -(image.shape[1]/2)*self.detector.pixelSize[1]
		t = z2 + 0.5*self._stitchBuffer[0][0].shape[0]*self.detector.pixelSize[0]
		b = z1 - 0.5*self._stitchBuffer[0][0].shape[0]*self.detector.pixelSize[0]
		extent = (l,r,b,t)
		# Add the transformation matrix into the images frame of reference.
		# Imagers FOR is a RH-CS where +x propagates down the beamline.
		M = np.identity(3)
		t = np.deg2rad(float(metadata['Image Angle']))
		rz = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		M = rz@M
		metadata.update({
				'Extent': extent,
				'M':M,
				'Mi':np.linalg.inv(M),
			})
		# Append the image and metada to to the buffer.
		self.buffer.append((image,metadata))
		# Clear the stitch buffer.
		self._stitchBuffer = []
		logging.info("Image stitched.")
		# Emit the signal
		self.imageAcquired.emit(index)

	def setPatientDataset(self,_file):
		self.file = _file

	def addImagesToDataset(self):
		if self.file != None:
			_name, _nims = self.file.addImageSet(self.buffer)
			logging.debug("Adding {} images to set {}.".format(_nims,_name))
			self.newImageSet.emit(_name, _nims)
		else:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
		# Clear the buffer.
		self.buffer = []