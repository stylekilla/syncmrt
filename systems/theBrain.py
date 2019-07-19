from systems import control, imageGuidance
import logging
import numpy as np
from functools import partial
from PyQt5 import QtCore

class Brain(QtCore.QObject):
	"""
	This module creates a treatment 'system' that is made up of imaging devices, positioning aparatus, beam delivery controls etc.
	"""
	
	imagesAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str)

	def __init__(self,patientSupports,detectors,config):
		super().__init__()
		self.solver = imageGuidance.solver()
		# self.source = control.hardware.source()
		self.patientSupport = control.hardware.patientSupport(patientSupports)
		self.imager = control.hardware.Imager(detectors,config.imager)
		self.patient = None
		# Counter
		self._routine = None
		self._imagingMode = 'step'
		# When a new image set is acquired, tell the GUI.
		self.imager.newImageSet.connect(self.newImageSet)

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
		logging.debug("Imaging mode changed to {}.".format(mode))
		self._imagingMode = mode

	def calculateAlignment(self):
		""" This is where the calculation magic happens. """

		# Update variables.
		# self.solver.setVariable()
		# Solve for alignment solution.
		# self.solver.solve()
		# Decompose.
		self.patientSupport.calculateMotion(self.solver.transform,self.solver.solution)
		# Apply solution.
		# self.patientSupport.shiftPosition(stageSolution)

	def applyAlignment(self):
		# Tell the patientSupport to apply the calculated/prepared motion.
		self.patientSupport.applyMotion(None)

	def movePatient(self,amount):
		self.patientSupport.shiftPosition(amount)

	def acquireXray(self,theta,trans,comment=''):
		if self.imager.file is None:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
			return
		# Start a new routine.
		self._routine = ImagingRoutine()
		# Theta and trans are relative values.
		# How many xrays to acquire?
		self._routine.imageCounter = 0
		self._routine.imageCounterLimit = len(theta)
		logging.info('Acquiring {} images at {} between {}.'.format(len(theta),theta,trans))
		# Get delta z.
		self._routine.tz = trans
		self._routine.theta = theta
		self._routine.roiZ = np.absolute(trans[1]-trans[0])
		logging.info("Calculated z range as {}".format(self._routine.roiZ))
		self._routine.beamHeight = 5
		logging.critical("Hard coding a beam height for now. This could be read off pappas and hutch mode.")
		# Get the current patient position.
		self._routine.preImagingPosition = self.patientSupport.position()
		logging.info("Pre-imaging position at: {}".format(self._routine.preImagingPosition))
		# Signals and slots: Connections.
		# self.patientSupport.finishedMove.connect(partial(self._acquireXray,roiZ))
		# self.detector.imageAcquired.connect()
		logging.info("Starting scan.")
		# Setup vars.
		tx = ty = rx = ry = 0
		# Move to first position.
		self.patientSupport.finishedMove.connect(self._startImage)
		self.patientSupport.shiftPosition([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta[0]])

	def _startImage(self):
		# Assume step for now.
		mode = 'step'
		if mode == 'step':
			# Signals and slots.
			self.imager.imageAcquired.connect(partial(self._step,'imageAcquired'))
			self.patientSupport.finishedMove.disconnect()
			self.patientSupport.finishedMove.connect(partial(self._step,'finishedMove'))
			# Calculate routine vars.
			self._routine.stepCounterLimit = round(self._routine.roiZ/self._routine.beamHeight)
			self._routine.stepSize = self._routine.beamHeight
			# Record the position for the final image.
			self._routine.preImagingStepPosition = self.patientSupport.position()
			# Up the step counter by 1.
			self._routine.stepCounter += 1
			# We are in the first position. Take an image.
			self.imager.acquireStep(self._routine.beamHeight)

	def _step(self,status):
		logging.info("In image step method {}/{} with status {}.".format(self._routine.stepCounter,self._routine.stepCounterLimit,status))
		if self._routine.stepCounter < self._routine.stepCounterLimit:
			if status == 'finishedMove':
				self._routine.stepCounter += 1
				# Acquire an image.
				self.imager.acquireStep(self._routine.beamHeight)
			elif status == 'imageAcquired':
				# Image was acquired. Move the patient up one step.
				self.patientSupport.shiftPosition([0,0,self._routine.stepSize,0,0,0])
		else:
			# Set up the sigansl to move to the continue scan method.
			self.imager.imageAcquired.disconnect()
			self.imager.imageAcquired.connect(self._continueScan)
			self.patientSupport.finishedMove.disconnect()
			# Metadata.
			tx,ty,tz,rx,ry,rz = self._routine.preImagingStepPosition
			metadata = {
				'Image Angle': self._routine.theta[self._routine.imageCounter-1],
				'Patient Support Position': (tx,ty,tz),
				'Patient Support Angle': (rx,ry,rz),
				'Image Index': self._routine.imageCounter,
			}
			# Update the imaging counter.
			self._routine.imageCounter += 1
			# Reset the routine steps.
			self._routine.stepCounter = 0
			# Stitch the image.
			self.imager.stitch(self._routine.imageCounter,metadata,tz,self._routine.tz)

	def _scan(self):
		pass

	def _continueScan(self):
		# So far this will acquire 1 image per angle. It will not do step and shoot or scanning yet.
		# Set position to pos before last image.
		self.patientSupport.setPosition(self._routine.preImagingStepPosition)
		logging.info("In continue scan method {}/{}.".format(self._routine.imageCounter,self._routine.imageCounterLimit))
		if self._routine.imageCounter < self._routine.imageCounterLimit:
			# Defaults for now.
			tx = ty = rx = ry = 0
			# Signals for moving.
			self.imager.imageAcquired.disconnect()
			self.patientSupport.finishedMove.connect(self._startImage)
			# Move to the next imaging position
			_pos = np.array(self._routine.preImagingPosition) + np.array([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta[self._routine.imageCounter]])
			# self.patientSupport.shiftPosition(_pos)
			self.patientSupport.setPosition(_pos)
		else:
			self._endScan()

	def _endScan(self):
		logging.info("Ending the scan.")
		# Disconnect signals.
		try:
			self.imager.imageAcquired.disconnect()
			self.patientSupport.finishedMove.disconnect()
		except:
			pass
		# Finalise image set.
		self.imager.addImagesToDataset()
		# Put patient back where they were.
		self.patientSupport.finishedMove.connect(self._finishedScan)
		self.patientSupport.setPosition(self._routine.preImagingPosition)

	def _finishedScan(self):
		logging.info("Emitting finished signal.")
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		# Send a signal saying how many images were acquired.
		self.imagesAcquired.emit(self._routine.imageCounterLimit)
		# Reset routine.
		self._routine = None

	def _acquireXray(self,deltaZ,mode='scan'):
		# logging.info("In continue scan method conducting: {}.".format(operation))
		# # So far this will acquire 1 image per angle. It will not do step and shoot or scanning yet.
		# if operation == 'imaging':
		# 	# Finished a move, acquire an x-ray.
		# 	self._routine.imageCounter += 1
		# 	tx,ty,tz,rx,ry,rz = self.patientSupport.position()
		# 	metadata = {
		# 		'Image Angle': self._routine.theta[self._routine.imageCounter-1],
		# 		'Patient Support Position': (tx,ty,tz),
		# 		'Patient Support Angle': (rx,ry,rz),
		# 		'Image Index': self._routine.imageCounter,
		# 	}
		# 	self.imager.acquire(self._routine.imageCounter,metadata)
		# elif operation == 'moving':
		# 	if self._routine.imageCounter < self._routine.imageCounterLimit:
		# 		# Defaults for now.
		# 		tx = ty = rx = ry = 0
		# 		# Finished a move, acquire an x-ray.
		# 		_pos = np.array(self._routine.preImagingPosition) + np.array([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta[self._routine.imageCounter]])
		# 		self.patientSupport.shiftPosition(_pos)
		# 	else:
		# 		self._endScan()
		pass

class ImagingRoutine:
	theta = []
	tz = [0,0]
	roiZ = 0
	preImagingPosition = None
	beamHeight = 0
	"""
	Image routine.
	"""
	imageCounter = 0
	imageCounterLimit = 0
	"""
	Step routine.
	"""
	preImagingStepPosition = None
	stepCounter = 0
	stepCounterLimit = 0
	stepSize = 0
	"""
	Scan routine.
	"""
	# stepCounter = 0
	# stepCounterLimit = 0
	# stepSize = 0