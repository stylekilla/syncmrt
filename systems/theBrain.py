from systems import control, imageGuidance
import logging
import numpy as np
from functools import partial
from PyQt5 import QtCore
from uuid import uuid1

class Brain(QtCore.QObject):
	"""
	This module creates a treatment 'system' that is made up of imaging devices, positioning aparatus, beam delivery controls etc.
	"""
	connected = QtCore.pyqtSignal(bool)
	imagesAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str)
	newMove = QtCore.pyqtSignal(str)
	moveFinished = QtCore.pyqtSignal(str)

	def __init__(self,patientSupports,detectors,config,**kwargs):
		super().__init__()
		# Image guidance solution solver.
		self.solver = imageGuidance.solver()

		# self.source = control.hardware.source()
		if 'backendThread' in kwargs:
			self.patientSupport = control.hardware.patientSupport(patientSupports,backendThread=kwargs['backendThread'])
			self.imager = control.hardware.Imager(detectors,config.imager,backendThread=kwargs['backendThread'])
		else:
			self.patientSupport = control.hardware.patientSupport(patientSupports)
			self.imager = control.hardware.Imager(detectors,config.imager)

		# Signals.
		self.patientSupport.connected.connect(self._connectionMonitor)
		self.imager.connected.connect(self._connectionMonitor)
		self.patientSupport.finishedMove.connect(self._removePatientMove)
		self.patientSupport.error.connect(self._resetFromError)

		# Connection status, True = Connected, False = Disconnected.
		self._connectionStatus = False

		# Current patient.
		self.patient = None
		# Stack.
		self._moveList = dict()

		# Counters.
		self._routine = None
		self._imagingMode = 'step'

		# When a new image set is acquired, tell the GUI.
		self.imager.newImageSet.connect(self.newImageSet)

		# Device monitor for monitoring subsystems.
		self.deviceMonitor = None
		if 'deviceMonitor' in kwargs:
			self.deviceMonitor = kwargs['deviceMonitor']
			self.patientSupport.connected.connect(partial(self.deviceMonitor.updateMonitor,'Positioning Support'))
			self.imager.connected.connect(partial(self.deviceMonitor.updateMonitor,'Imaging Detector'))

	def isConnected(self):
		# Return the connection status.
		return self._connectionStatus

	def _connectionMonitor(self):
		# Connection monitor for all the motors that make up the patient support system.
		teststate = []
		for essentialSystem in [self.patientSupport,self.imager]:
			teststate.append(essentialSystem.isConnected())
		self._connectionStatus = all(teststate)

		# Send out an appropriate signal.
		self.connected.emit(self._connectionStatus)

	def _resetFromError(self):
		""" reset from an error. """
		logging.warning("Received an error. Reset from an error not incorporated yet...")

	def loadPatient(self,patient):
		""" Assumes patient has an already loaded x-ray dataset. """
		self.patient = patient
		self.patient.newDXfile.connect(self.setLocalXrayFile)
		logging.info("System has been linked with the patient data.")

	def setLocalXrayFile(self,file):
		""" Link the patient datafile to the imager. """
		self.imager.file = self.patient.dx.file

	def setStage(self,name):
		self.patientSupport.load(name)

	def setDetector(self,name):
		self.imager.load(name)

	def setImagingMode(self,mode):
		"""
		Describe the imaging mode. Single frame or continuous imaging??
		"""
		logging.debug("Imaging mode changed to {}.".format(mode))
		self._imagingMode = mode

	def setPatientSupportMonitor(self,monitor):
		# The monitor should have functions to connect to singals and update the positions from.
		self.patientSupport.newSupportSelected.connect(monitor.newMotors)
		self.patientSupport.motorMoving.connect(monitor.updateMotor)
		# If a support has already been selected, add that.
		if self.patientSupport.currentDevice is not None:
			monitor.newMotors(self.patientSupport.currentDevice,self.patientSupport.currentMotors)

	def getPatientMove(self,uid):
		logging.info("Getting Movement UID: {}".format(uid))
		# Return the move from the move list.
		return self._moveList[str(uid)]

	def _removePatientMove(self,uid):
		logging.info("Removing Movement UID: {}".format(uid))
		# Remove the uid from the move list.
		if str(uid) in self._moveList:
			del self._moveList[str(uid)]
		# Emiting signal to say we have finish move.
		self.moveFinished.emit(str(uid))

	def calculateAlignment(self):
		""" This is where the calculation magic happens. """
		# Decomposition routine.
		self.patientSupport.calculateMotion(self.solver.transform,self.solver.solution)

	def applyAlignment(self):
		""" Tell the patientSupport to apply the calculated/prepared motion. """		# Create a new uuid.
		uid = uuid1()
		# Send the signal saying we have a new move.
		self.newMove.emit(str(uid))
		self._moveList[str(uid)] = self.patientSupport._motion
		# Tell the patient support to move.
		self.patientSupport.applyMotion()

	def movePatient(self,amount,motionType):
		""" All patient movement must be done through this function, as it sets a UUID for the motion. """
		if self.isConnected():
			# Create a new uuid.
			uid = uuid1()
			self._moveList[str(uid)] = amount
			# Send the signal saying we have a new move.
			self.newMove.emit(str(uid))
			# Finally, tell the patient support to move.
			if motionType == 'relative':
				self.patientSupport.shiftPosition(amount,uid)
			elif motionType == 'absolute':
				self.patientSupport.setPosition(amount,uid)
			else:
				logging.warning("Could not move patient with motion type {}.".format(motionType))
		else:
			logging.warning("Cannot move as not all systems are connected.")

	def acquireXray(self,theta,trans,comment=''):
		if self.isConnected():
			if self.imager.file is None:
				logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
				return
			# Start a new routine.
			self._routine = ImagingRoutine()
			# We should ideally define a beam height...
			self._routine.dz = 20.0
			logging.critical("Hard setting a beam height of {} for now...".format(self._routine.dz))
			# Theta and trans are relative values from current position.
			self._routine.theta = theta
			# Calculate how many x-rays are required.
			self._routine.imageCounterLimit = len(theta)
			# Get the current patient position.
			self._routine.preImagingPosition = self.patientSupport.position()
			# Calculate how many steps are required per image.
			# self._routine.stepCounterLimit = np.ceil(np.absolute(trans[1]-trans[0])/self._routine.dz)
			m = np.ceil(np.absolute(trans[0])/self._routine.dz - 0.5)
			n = np.ceil(np.absolute(trans[1])/self._routine.dz - 0.5)
			s = self._routine.preImagingPosition[2]
			self._routine.tz = [s-m*self._routine.dz,s+n*self._routine.dz]
			self._routine.stepCounterLimit = m+n+1
			print(self._routine.tz,self._routine.stepCounterLimit)
			# Signals and slots: Connections.
			logging.info("Connecting patient support and detector signals to imaging routine.")
			self.patientSupport.finishedMove.connect(partial(self._continueScan,'imaging'))
			self.imager.imageAcquired.connect(partial(self._continueScan,'moving'))
			# Start the scan process.
			logging.info("Pre-imaging position at: {}".format(self._routine.preImagingPosition))
			self._startScan()
		else:
			logging.warning("Cannot move as not all systems are connected.")


	def _startScan(self):
		if self._routine.imageCounter < self._routine.imageCounterLimit:
			logging.info("Starting scan {}/{} at {}deg.".format(self._routine.imageCounter+1,self._routine.imageCounterLimit,self._routine.theta[self._routine.imageCounter]))
			# Calculate image position and set patient to that position.
			position = np.array(self._routine.preImagingPosition) + np.array([0,0,self._routine.tz[0],0,0,self._routine.theta[self._routine.imageCounter]])
			self.patientSupport.setPosition(position)
		else:
			# We are done. 
			self._endScan()

	def _continueScan(self,operation):
		if self._routine.stepCounterLimit == 1:
			# We are expecting more than 1 image step, and our counter is below that threshold.
			logging.info("In continue scan method conducting: {} for single image.".format(operation,self._routine.stepCounter+1,self._routine.stepCounterLimit))
			if operation == 'imaging':
				# Acquire an x-ray.
				tx,ty,tz,rx,ry,rz = self.patientSupport.position()
				metadata = {
					'Image Angle': self._routine.theta[self._routine.imageCounter],
					'Patient Support Position': (tx,ty,tz),
					'Patient Support Angle': (rx,ry,rz),
					'Image Index': self._routine.imageCounter,
				}
				self.imager.acquire(self._routine.imageCounter,metadata)
			elif operation == 'moving':
				# We are done. 
				self._routine.imageCounter += 1
				# Go back to start scan.
				self._startScan()

		elif self._routine.stepCounter < self._routine.stepCounterLimit:
			logging.info("In continue scan method conducting: {} for step {}/{}".format(operation,self._routine.stepCounter+1,self._routine.stepCounterLimit))
			# We are expecting more than 1 image step, and our counter is below that threshold.
			if operation == 'imaging':
				# Increase the counter first, otherwise the imager signal will continue on without the counter incrementing.
				self._routine.stepCounter += 1
				# Acquire an image step.
				self.imager.acquireStep(self._routine.dz)
			elif operation == 'moving':
				# Shift the position another step.
				self.patientSupport.shiftPosition([0,0,self._routine.dz,0,0,0])
		else:
			# We have finished a stepped scan.
			tx,ty,tz,rx,ry,rz = np.array(self._routine.preImagingPosition) + np.array([0,0,0,0,0,self._routine.theta[self._routine.imageCounter]])
			metadata = {
				'Image Angle': self._routine.theta[self._routine.imageCounter],
				'Patient Support Position': (tx,ty,tz),
				'Patient Support Angle': (rx,ry,rz),
				'Image Index': self._routine.imageCounter,
			}
			# The image start position.
			z1 = self._routine.tz[0]
			# The image finish position.
			z2 = self.patientSupport.position()[2]
			# Stitch the image together.
			self.imager.imageAcquired.disconnect()
			self.imager.stitch(self._routine.imageCounter,metadata,z1,z2)
			self.imager.imageAcquired.connect(partial(self._continueScan,'moving'))
			# Reset the counters. 
			self._routine.imageCounter += 1
			self._routine.stepCounter = 0
			# Go back to start scan.
			self._startScan()

	def _endScan(self):
		logging.info("Finishing scan.")
		# Disconnect signals.
		logging.info("Disconnecting patient support and detector signals from imaging routine.")
		self.patientSupport.finishedMove.disconnect()
		self.imager.imageAcquired.disconnect()
		# Finalise image set.
		self.imager.addImagesToDataset()
		# Put patient back where they were.
		self.patientSupport.finishedMove.connect(self._finishedScan)
		logging.debug("Setting patient position to initial pre-imaging position.")
		self.movePatient(self._routine.preImagingPosition,'absolute')

	def _finishedScan(self):
		logging.debug("Finished scan.")
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		# Send a signal saying how many images were acquired.
		self.imagesAcquired.emit(self._routine.imageCounterLimit)
		# Reset routine.
		self._routine = None

class ImagingRoutine:
	""" Imaging routine data. """
	# Imaging angles.
	theta = []
	# Imaging counters.
	imageCounter = 0
	imageCounterLimit = 0
	# Distance to cover in Z from current position.
	tz = [0,0]
	# Delta Z is the step in z for each "slice" or "still frame".
	dz = 0
	# The position prior to imaging.
	preImagingPosition = None
	# A counter and counter limit for vertically stepping through a region.
	stepCounter = 0
	stepCounterLimit = 0
