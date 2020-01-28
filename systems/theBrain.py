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
		"""
		Describe the imaging mode. Single frame or continuous imaging??
		"""
		logging.debug("Imaging mode changed to {}.".format(mode))
		self._imagingMode = mode

	def calculateAlignment(self):
		""" This is where the calculation magic happens. """
		# Decomposition routine.
		self.patientSupport.calculateMotion(self.solver.transform,self.solver.solution)

	def applyAlignment(self):
		""" Tell the patientSupport to apply the calculated/prepared motion. """
		self.patientSupport.applyMotion()

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
		self._routine.counter = 0
		self._routine.counterLimit = len(theta)
		logging.info('Acquiring {} images at {}.'.format(len(theta),theta))
		# Get delta z.
		self._routine.tz = trans
		self._routine.theta = theta
		self._routine.theta_relative = np.hstack([np.array([theta[0]]),np.diff(theta)])
		# self._routine.dz = np.absolute(trans[1]-trans[0])
		# logging.info("Calculated delta z as {}".format(self._routine.dz))
		# Get the current patient position.
		self._routine.preImagingPosition = self.patientSupport.position()
		logging.info("Pre-imaging position at: {}".format(self._routine.preImagingPosition))
		# Signals and slots: Connections.
		# self.patientSupport.finishedMove.connect(partial(self._acquireXray,dz))
		# self.detector.imageAcquired.connect()
		self._startScan()

		# 	# Calculate a relative change for the next imaging angle.
		# 	try: 
		# 		theta[i+1] = -(theta[i]-theta[i+1])
		# 	except:
		# 		pass

	def _startScan(self):
		logging.info("Starting scan.")
		# Setup vars.
		tx = ty = rx = ry = 0
		# Move to first position.
		self.patientSupport.finishedMove.connect(partial(self._continueScan,'imaging'))
		self.imager.imageAcquired.connect(partial(self._continueScan,'moving'))
		logging.info("Adding {}deg offset.".format(self.imager.offset))
		self.patientSupport.shiftPosition([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta_relative[0]-self.imager.offset])

	def _continueScan(self,operation):
		logging.info("In continue scan method conducting: {}.".format(operation))
		# So far this will acquire 1 image per angle. It will not do step and shoot or scanning yet.
		if operation == 'imaging':
			# Finished a move, acquire an x-ray.
			self._routine.counter += 1
			tx,ty,tz,rx,ry,rz = self.patientSupport.position()
			metadata = {
				'Image Angle': self._routine.theta[self._routine.counter-1],
				'Patient Support Position': (tx,ty,tz),
				'Patient Support Angle': (rx,ry,rz),
				'Image Index': self._routine.counter,
			}
			self.imager.acquire(self._routine.counter,metadata)
		elif operation == 'moving':
			if self._routine.counter < self._routine.counterLimit:
				# Defaults for now.
				tx = ty = rx = ry = 0
				# Finished a move, acquire an x-ray.
				self.patientSupport.shiftPosition([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta_relative[self._routine.counter]])
			else:
				self._endScan()

	def _step(self):
		# Take over the _continueScan operation.
		self.patientSupport.finishedMove.disconnect()
		self.patientSupport.finishedMove.connect(self._step)
		# Move the patient up one step.
		self.patientSupport.shiftPosition([0,0,_dstep,0,0,0])
		# Acquire part of an image.
		# self.

	def _scan(self):
		pass

	def _endScan(self):
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		self.imager.imageAcquired.disconnect()
		# Finalise image set.
		self.imager.addImagesToDataset()
		# Put patient back where they were.
		self.patientSupport.finishedMove.connect(self._finishedScan)
		logging.debug("Setting patient position to initial pre-imaging position.")
		self.patientSupport.setPosition(self._routine.preImagingPosition)

	def _finishedScan(self):
		logging.debug("Finished scan.")
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		# Send a signal saying how many images were acquired.
		self.imagesAcquired.emit(self._routine.counterLimit)
		# Reset routine.
		self._routine = None

class ImagingRoutine:
	theta = []
	theta_relative = []
	tz = [0,0]
	dz = 0
	preImagingPosition = None
	counter = 0
	counterLimit = 0