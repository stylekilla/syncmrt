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

	def __init__(self,database,config,backendThread=None):
		super().__init__()
		# Information
		self.detector = None
		self.name = None
		# File.
		self.file = None
		self.config = config
		# Image buffer for set.
		self.buffer = []
		self.metadata = {}
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
		if name in self.deviceList:
			# Update our name accordingly.
			self.name = name
			# Create the new detector and load config settings.
			# This is a "hardware" detector.
			newDetector = detector(
				self.config.name,
				self.config,
				backendThread=self.backendThread
			)
			# Signals and slots.
			newDetector.connected.connect(self._connectionMonitor)
			newDetector.disconnected.connect(self._connectionMonitor)
			# When the detector acquires an image, add it to the data set.
			newDetector.imageAcquired.connect(self._addImage)
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

	def setPatientDataset(self,_file):
		""" Save the patient file to save images in to. """
		self.file = _file

	def setImagingParameters(self,params):
		""" Passthrough function: As they appear on PV's. """
		self.detector.setParameters(params)

	def setupDynamicScan(self,distance,speed,uid,metadata={}):
		""" Passthrough function: Set the detector up for a dynamic scan. """
		self.detector.setupDynamicScan(distance,speed,uid)
		# Add the metadata for the image set.
		self.metadata = metadata

	def acquire(self,mode,uid='temp',metadata={}):
		""" Acquire an image. Can supply some metadata if desired. """
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return
		# Tell the detector to acquire an image.
		self.detector.acquire(mode,uid,metadata)
		
	def _addImage(self,uid):
		""" Add an acquired image to the buffer. """
		# Get the image index. Note the len() of the buffer will suffice as we haven't added the data to it yet.
		logging.critical(f"Adding image {uid} to buffer.")
		index = len(self.buffer)
		# Get the image data: made up of (image,metadata).
		data = self.detector.getImage(uid)
		# Append the image and metada to to the buffer.
		self.buffer.append(data)
		# Emit a signal saying we have acquired an image.
		self.imageAcquired.emit(index)

	def addImagesToDataset(self):
		if self.file != None:
			_name, _nims = self.file.addImageSet(self.buffer,metadata=self.metadata)
			logging.critical("Adding {} images to set {}.".format(_nims,_name))
			self.newImageSet.emit(_name, _nims)
		else:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
		# Clear the buffer/metadata.
		self.buffer = []
		self.metadata.clear()