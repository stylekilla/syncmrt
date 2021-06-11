from systems import control, imageGuidance
import logging
import numpy as np
from functools import partial
from PyQt5 import QtCore
from uuid import uuid1
import sched, time
from threading import Thread, Event
from datetime import datetime,timedelta

class threadFunction(Thread):
	def __init__(self,func,args=(),kwargs={},synchronizeEvent=None,delay=0):
		""" A thread function. """
		# Create the thread.
		super().__init__()
		# Save the func arguments.
		self.func = func
		self.args = args
		self.kwargs = kwargs
		# Mark the synchronization event.
		self.event = synchronizeEvent
		self.delay = delay
	def run(self):
		# Run this once the thread has been started.
		# Wait for the trigger event then run the function.
		if self.event is not None:
			while not self.event.is_set():
				pass
		# Wait for the delay.
		time.sleep(self.delay.total_seconds())
		# Run the function.
		self.func(*self.args,**self.kwargs)

def synchronize(functions,args=(),kwargs=(),delays=()):
	""" Synchronize a list of events (to within ~16 ms). """
	# Handle any empty lists.
	if len(args) == 0: args = tuple([() for _ in range(len(functions))])
	if len(kwargs) == 0: kwargs = tuple([{} for _ in range(len(functions))])
	if len(delays) == 0: delays = tuple([0 for _ in range(len(functions))])
	threads = []
	# Synchronization event.
	synchronizeEvent = Event()
	# Add the functions to synchronize.
	for i in range(len(functions)):
		threads.append(threadFunction(functions[i],args=args[i],kwargs=kwargs[i],synchronizeEvent=synchronizeEvent,delay=timedelta(milliseconds=delays[i])))
	# Start and run the threads.
	for thread in threads:
		thread.start()
	# Send the synchronization signal.
	synchronizeEvent.set()
	# Rejoin the threads.
	for thread in threads:
		thread.join()

class Brain(QtCore.QObject):
	"""
	This module creates a treatment 'system' that is made up of imaging devices, positioning aparatus, beam delivery controls etc.
	"""
	connected = QtCore.pyqtSignal(bool)
	newImageSet = QtCore.pyqtSignal(str)
	newMove = QtCore.pyqtSignal(str)
	moveFinished = QtCore.pyqtSignal(str)
	workflowFinished = QtCore.pyqtSignal()
	displayMessage = QtCore.pyqtSignal(str)

	def __init__(self,config,**kwargs):
		super().__init__()
		# Machine configuration.
		self.imagingMode = config.machine.imagingMode
		# Create our x-ray sources for imaging and treatment.
		self.imagingBeam = control.hardware.source('Imaging',config.imagingBeam)
		self.treatmentBeam = control.hardware.source('Treatment',config.treatmentBeam)
		# Threading.
		if 'backendThread' in kwargs:
			self.patientSupport = control.hardware.patientSupport(config.patientSupport,backendThread=kwargs['backendThread'])
			self.imager = control.hardware.Imager(config.imager,backendThread=kwargs['backendThread'])
		else:
			self.patientSupport = control.hardware.patientSupport(config.patientSupport)
			self.imager = control.hardware.Imager(config.imager)

		# Hardware signals.
		self.patientSupport.connected.connect(self._connectionMonitor)
		self.imager.connected.connect(self._connectionMonitor)
		self.patientSupport.finishedMove.connect(self._removePatientMove)
		self.patientSupport.error.connect(self._resetFromError)

		# Connection status, True = Connected, False = Disconnected.
		self._connectionStatus = False

		# Current patient.
		self.patient = None
		# Move queue.
		self._moveQueue = dict()
		# Workflow queue.
		self.workflowQueue = []
		self._workflowLastTrigger = None
		# Counters.
		self._routine = None
		# Image guidance solution solver.
		self.solver = imageGuidance.solver()

		# When a new image set is acquired, tell the GUI.
		self.imager.newImageSet.connect(self.newImageSet)

		# Device monitor for monitoring subsystems.
		self.deviceMonitor = None
		if 'deviceMonitor' in kwargs:
			self.deviceMonitor = kwargs['deviceMonitor']
			self.patientSupport.connected.connect(partial(self.deviceMonitor.updateMonitor,'Positioning Support'))
			self.imager.connected.connect(partial(self.deviceMonitor.updateMonitor,'Imaging Detector'))
			# self.imagingBeam.connected.connect(partial(self.deviceMonitor.updateMonitor,'Imaging Source'))
			# self.treatmentBeam.connected.connect(partial(self.deviceMonitor.updateMonitor,'Treatment Source'))

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
		logging.info("Patient loaded.")

	def setLocalXrayFile(self,file):
		""" Link the patient datafile to the imager. """
		self.imager.file = self.patient.dx.file
		logging.info(f"Patient X-ray file set to: {self.imager.file}.")

	def setStage(self,name):
		logging.warning("Pending removal. Obsolete(?).")
		self.patientSupport.load(name)

	def setDetector(self,name):
		logging.warning("Pending removal. Obsolete(?).")
		self.imager.load(name)

	def setPatientSupportMonitor(self,monitor):
		# The monitor should have functions to connect to singals and update the positions from.
		self.patientSupport.moving.connect(monitor.updateMotor)
		monitor.newMotors(self.patientSupport.name,self.patientSupport.motors)

	def setImagingSpeed(self,value):
		""" Set the velocity for the imaging routines. """
		self.patientSupport.setSpeed(float(value))

	def getPatientMove(self,uid):
		logging.debug("Getting Movement UID: {}".format(uid))
		# Return the move from the move list.
		return self._moveQueue[str(uid)]

	def _removePatientMove(self,uid):
		logging.debug("Removing Movement UID: {}".format(uid))
		# Remove the uid from the move list.
		if str(uid) in self._moveQueue:
			del self._moveQueue[str(uid)]
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
		self._moveQueue[str(uid)] = self.patientSupport._motion
		self.newMove.emit(str(uid))
		# Tell the patient support to move.
		self.patientSupport.applyMotion(uid=str(uid))

	def movePatient(self,amount,motionType):
		""" All patient movement must be done through this function, as it sets a UUID for the motion. """
		if not self.isConnected():
			logging.warning("Cannot move as not all systems are connected.")
			return

		# Create a new uuid and add it to the queue..
		uid = uuid1()
		self._moveQueue[str(uid)] = amount
		# Send the signal saying we have a new move.
		self.newMove.emit(str(uid))
		# Finally, tell the patient support to move.
		if motionType == 'relative':
			self.patientSupport.shiftPosition(amount,uid)
		elif motionType == 'absolute':
			self.patientSupport.setPosition(amount,uid)
		else:
			logging.warning("Could not move patient with motion type {}.".format(motionType))
			return

	def runWorkflowQueue(self):
		""" Run all the items in the queue, one at a time. Uses FIFO approach. """
		# Workflow items: (func, (args), {kwargs}, trigger).
		# Trigger: connect a signal to trigger the next workflow item.

		# If we had a trigger before, disconnect it.
		if self._workflowLastTrigger is not None: 
			self._workflowLastTrigger.disconnect(self.runWorkflowQueue)
			self._workflowLastTrigger = None
		# If there is something in the queue, process it.
		if len(self.workflowQueue) > 0:
			logging.info(f"Processing worfklow item. {len(self.workflowQueue)} items remaining.")
			# Take the first item and pop it.
			item = self.workflowQueue.pop(0)
			# Put a small sleep in to help make things slower.
			time.sleep(0.1)
			# Unpack the queue item.
			func,args,kwargs,trigger = item
			# logging.debug(f"func: {func}\n\nargs: {args}\n\nkwargs: {kwargs}\n\ntrigger: ({trigger})")
			# Keep a reference to the trigger.
			self._workflowLastTrigger = trigger
			# Make a trigger if required.
			if self._workflowLastTrigger is not None: 
				# Connect it to the the run workflow function.
				self._workflowLastTrigger.connect(self.runWorkflowQueue)
			# Finally, run the function with the arguments.
			func(*args,**kwargs)
			# If no trigger was provided for the next item... just trigger it automatically.
			if self._workflowLastTrigger is None:
				self.runWorkflowQueue()
		else:
			# Disconnect any signals that are being held on to.
			if self._workflowLastTrigger is not None:
				self._workflowLastTrigger.disconnect(self.runWorkflowQueue)
				self._workflowLastTrigger = None
			# Tell the world our workflow is finished.
			logging.debug("Workflow is empty.")
			self.workflowFinished.emit()

	def acquireXrays(self,theta,zrange=None,comment=''):
		""" Theta and translation must be lists of values. """
		# Check: Are all systems connected?
		if not self.isConnected():
			logging.warning("Cannot move as not all systems are connected.")
			return
		# Check: Is an x-ray file avaialbe to use?
		if self.imager.file is None:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
			return

		# Take note of the home position prior to imaging.
		homePosition = self.patientSupport.position()
		# Set the workpoint (if required).
		if self.patientSupport.workpoint is not None:
			self.workflowQueue.append(
				(self.patientSupport.zeroWorkpoint, (), {}, self.patientSupport.workpointZeroed)
			)
			# Also, as the workpoint is zeroed, we need to overide our home position.
			homePosition[:3] = [0,0,0]
		# Move to the imager position.
		self.workflowQueue.append(
			(self.movePatient, (tuple(self.imager.config.offset),'relative'), {}, self.patientSupport.finishedMove)
		)

		# Two very different imaging modes.
		if self.imagingMode == 'dynamic':
			# Calculate parameters.
			start, stop = zrange
			distance = stop-start
			speed = self.patientSupport.getSpeed()
			uid = str(uuid1())
			time = datetime.now()
			metadata = {
				'Patient Support Position': homePosition[:3],
				'Patient Support Angle': homePosition[3:],
				'Imaging Mode': self.imagingMode,
				'Image Angles': theta,
				'Image Offset': tuple(self.imager.config.offset),
				'Scan Range': zrange,
				'Scan Distance': distance,
				'Scan Speed': speed,
				'UUID': uid,
				'Time': time.strftime("%H:%M:%S"),
				'Date': time.strftime("%d/%m/%Y"),
			}

			# For each angle, take an image.
			for index,angle in enumerate(theta):
				# Imaging UUID.
				imageUid = str(uuid1())
				imageMetadata = {
					'Image Angle': angle,
					'Imaging Mode': self.imagingMode,
					'Image Offset': tuple(self.imager.config.offset),
					'UUID': imageUid,
				}

				# Append to the workflow queue.
				self.workflowQueue += [
					(self.movePatient, ([0,0,start,0,0,angle],'relative'), {}, self.patientSupport.finishedMove),
					(self.imager.setupDynamicScan, (distance,speed,imageUid), {}, self.imager.detector.detectorReady),
					(self.imagingBeam.turnOn,		(), {}, self.imagingBeam.on),
					(self.imagingBeam.openShutter,	(), {}, self.imagingBeam.shutterOpen),
					(synchronize,
						[(self.patientSupport.verticalScan,self.imager.acquire)],
						{
							'args': (
								(distance,'relative',speed),
								(self.imagingMode,imageUid,imageMetadata)
							),
							'delays': (1400,0)
						},
						self.patientSupport.finishedMove
					),
					(self.imagingBeam.closeShutter,	(), {}, self.imagingBeam.shutterClosed),
					# (self.imagingBeam.turnOff, (), {}, self.imagingBeam.off),
					(self.movePatient, ([0,0,-stop,0,0,-angle],'relative'), {}, self.patientSupport.finishedMove),
				]

		elif self.imagingMode == 'static':
			pass

		else:
			logging.warning(f"Unknown imaging mode {self.imagingMode}.")
			return

		# Move back to the pre-imaging position.
		self.workflowQueue.append(
				(self.movePatient, (homePosition,'absolute'), {}, self.patientSupport.finishedMove)
			)
		# What to do when the workflow is finished.
		self.workflowFinished.connect(self._finaliseAcquireXrays)
		logging.warning("When the workflow is finished we an unlock it?")
		# Start the workflow.
		self.runWorkflowQueue()

	def _finaliseAcquireXrays(self):
		# Disconnect the signal that got us here.
		self.workflowFinished.disconnect(self._finaliseAcquireXrays)
		logging.warning("When the imager sends imageAcquired(n) == n expected x-rays, we can finalize?")
		# Finalise image set.
		self.imager.addImagesToDataset()

	def deliverTreatment(self,ports=([0,0,0,0,0,0],),scanRanges=([30,-30],),speeds=(5,)):
		# Check: Are all appropriate systems connected?
		if not self.isConnected():
			logging.warning("Cannot move as not all systems are connected.")
			return

		# Get the number of ports to deliver.
		nPorts = len(ports)
		# Take note of the home position prior to imaging.
		homePosition = self.patientSupport.position()
		# Create a workflow for each port.
		for i in range(nPorts):
			start,stop = scanRanges[i]
			# Treatment workflow:
			self.workflowQueue += [
				(self.patientSupport.setSpeed, (speeds[i],), {}, None),
				(self.movePatient, (ports[i],'relative'), {}, self.patientSupport.finishedMove),
				(self.movePatient, ([0,0,start,0,0,0],'absolute'), {}, self.patientSupport.finishedMove),
				(self.treatmentBeam.turnOn,		(), {}, self.treatmentBeam.on),
				(self.treatmentBeam.openShutter,	(), {}, self.treatmentBeam.shutterOpen),
				(self.movePatient, ([0,0,stop,0,0,0],'absolute'), {}, self.patientSupport.finishedMove),
				(self.treatmentBeam.closeShutter,	(), {}, self.treatmentBeam.shutterClosed),
				# (self.treatmentBeam.turnOff, (), {}, self.treatmentBeam.off),
				(self.movePatient, (homePosition,'absolute'), {}, self.patientSupport.finishedMove)
			]
		# What to do when the workflow is finished.
		self.workflowFinished.connect(self._finaliseTreatment)
		# Start the workflow.
		self.runWorkflowQueue()

	def _finaliseTreatment(self):
		# Finalize the treatment.
		self.workflowFinished.disconnect(self._finaliseTreatment)
		self.displayMessage.emit("Treatment finished.")

	def setupFlatFieldCorrection(self):
		# Check: Are all appropriate systems connected?
		if not self.isConnected():
			logging.warning("Cannot proceed as not all systems are connected.")
			return

		self.displayMessage.emit("Ensure there is nothing in the beam.")

		# Detector workflow:
		self.workflowQueue = [
			(self.imagingBeam.turnOn,		(), {}, self.imagingBeam.on),
			(self.imagingBeam.openShutter,	(), {}, self.imagingBeam.shutterOpen),
			(self.imager.acquireFloodField,	(), {}, self.imager.imageAcquired),
			(self.imagingBeam.closeShutter,	(), {}, self.imagingBeam.shutterClosed),
			(self.imager.acquireDarkField,	(), {}, self.imager.imageAcquired),
		]
		# What to do when the workflow is finished.
		self.workflowFinished.connect(self._finalizeFloodDarkFields)
		# Start the workflow.
		self.runWorkflowQueue()

	def _finalizeFloodDarkFields(self):
		# Finalize the treatment.
		self.workflowFinished.disconnect(self._finalizeFloodDarkFields)
		self.displayMessage.emit("Flood fields and dark fields acquired.")