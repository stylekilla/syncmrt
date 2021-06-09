# from systems.control.hardware.motor import motor
from systems.control import hardware
from PyQt5 import QtCore
import numpy as np
from functools import partial
import logging
import time
from datetime import datetime

class patientSupport(QtCore.QObject):
	connected = QtCore.pyqtSignal(bool)
	newSupportSelected = QtCore.pyqtSignal(str,list)
	moving = QtCore.pyqtSignal()
	finishedMove = QtCore.pyqtSignal(str)
	workpointSet = QtCore.pyqtSignal()
	workpointZeroed = QtCore.pyqtSignal()
	moving = QtCore.pyqtSignal(str,float)
	error = QtCore.pyqtSignal()

	def __init__(self,database,config,backendThread=None):
		super().__init__()
		# Information
		self.currentDevice = None
		self.currentMotors = []
		self._dof = (0,[0,0,0,0,0,0])
		# The vertical translation motor.
		self.verticalTranslationMotor = None
		# Configuration file.
		self.config = config
		# Current movement id.
		self.uid = None
		# A queue for sequential movements.
		self.motionQueue = []
		self._workflowLastTrigger = None
		# A preloadable motion.
		self._motion = None
		# Motor counter for finished arguments.
		self._counter = 0
		# Counter for calculate motion loop.
		self._i = 0
		# Connection status, True = Connected, False = Disconnected.
		self._connectionStatus = False
		# Save the backend thread (if any).
		self.backendThread = backendThread
		# A settable work point for the patient support.
		self.workpoint = None

		if config.velocityMode == 'global':
			self.velocityController = hardware.velocityController(config.VELOCITY_CONTROLLER)
		else:
			self.velocityController = None

		"""
		Load the CSV dataset.
		"""
		# Get list of motors.
		import csv, os
		# Open CSV file
		f = open(database)
		r = csv.DictReader(f)
		# Devices is the total list of all devices in the database.
		self.motors = []
		self.deviceList = set()
		for row in r:
			# Check for commented out lines first.
			if row['PatientSupport'].startswith('--'): 
				continue
			else:
				self.motors.append(row)
				self.deviceList.add(row['PatientSupport'])

	def load(self,name):
		# Load a set of motors for the patient support.
		logging.info("Loading patient support: {}.".format(name))

		# Check if the desired device is in the devices list.
		if name in self.deviceList:
			# Remove all existing motors.
			for i in range(len(self.currentMotors)):
				del self.currentMotors[-1]

			# Iterate over new motors.
			for support in self.motors:
				# Does the motor match the name?
				if support['PatientSupport'] == name:
					# Define the new motor.
					newMotor = hardware.motor(
							support['Description'],
							int(support['Axis']),
							int(support['Order']),
							pv = support['PV Root'],
							backendThread = self.backendThread
						)

					# Signals and slots.
					newMotor.connected.connect(self._connectionMonitor)
					newMotor.disconnected.connect(self._connectionMonitor)
					newMotor.position.connect(partial(self.moving.emit,newMotor.name))
					newMotor.moveFinished.connect(self._finished)
					newMotor.error.connect(self.error.emit)

					# Append the motor to the list.
					self.currentMotors.append(newMotor)

			logging.critical("Hard coding LAPS TCP stuff...")
			self.workpoint = hardware.workpoint(
					"SR08ID01ROB01",
					backendThread = self.backendThread
				)
			self.workpoint.workpointSet.connect(self.workpointSet.emit)
			self.workpoint.workpointZeroed.connect(self.workpointZeroed.emit)

			if self.config.velocityMode == 'global':
				# Set the global speed for the device.
				self.velocityController = hardware.velocityController(self.config.VELOCITY_CONTROLLER)

			# Set the order of the list from 0-i.
			self.currentMotors = sorted(self.currentMotors, key=lambda k: k._order)
			# Update the name details.
			self.currentDevice = name
			# Emit a signal to say we've selected a new patient support.
			self.newSupportSelected.emit(name,[x.name for x in self.currentMotors])

		# Define the new motor.
		self.verticalTranslationMotor = hardware.motor(
				'Vertical Translation Motor',2,0,
				pv = self.config.verticalTranslationMotor,
				backendThread = self.backendThread
			)

		# Signals and slots.
		self.verticalTranslationMotor.connected.connect(self._connectionMonitor)
		self.verticalTranslationMotor.disconnected.connect(self._connectionMonitor)
		self.verticalTranslationMotor.position.connect(partial(self.moving.emit,self.verticalTranslationMotor.name))
		self.verticalTranslationMotor.moveFinished.connect(partial(self.finishedMove.emit,None))
		self.verticalTranslationMotor.error.connect(self.error.emit)


	def isConnected(self):
		# Return the connection status.
		return self._connectionStatus

	def _connectionMonitor(self):
		# Connection monitor for all the motors that make up the patient support system.
		teststate = []
		for motor in self.currentMotors:
			teststate.append(motor.isConnected())
		teststate.append(self.verticalTranslationMotor.isConnected())
		self._connectionStatus = all(teststate)

		# Send out an appropriate signal.
		self.connected.emit(self._connectionStatus)

	def reconnect(self):
		""" Reconnect all the motors in the system. """
		for motor in self.currentMotors:
			motor.reconnectControls()

	def setSpeed(self,speed):
		""" Set the speed of the patient support. """
		if self.config.velocityMode == 'global':
			# Set the global speed for the device.
			self.velocityController.setSpeed(speed)
			self.velocityController.setAcceleration(speed*4)

		elif self.config.velocityMode == 'axis':
			# Set the speed on each motor if it allows it.
			for motor in self.currentMotors:
				raise TypeError("Not implemented.")
				# if motor.adjustableSpeed:
					# motor.setSpeed(speed)

	def getSpeed(self):
		""" Return the speed of the patient support. """
		if self.config.velocityMode == 'global':
			return self.velocityController.getSpeed()
		elif self.config.velocityMode == 'axis':
			raise TypeError("Not implemented.")

	def setworkpoint(self,workpoint):
		""" Set the workpoint (if available). """
		# Set the work point if required.
		if self.workpoint is not None:
			logging.info(f"Setting the workpoint to {workpoint}")
			self.workpoint.offset(workpoint)
		else:
			logging.warning("No workpoint to set, skipping.""")

	def zeroWorkpoint(self):
		""" Zero the workpoint (if available). """
		# Set the work point if required.
		if self.workpoint is not None:
			logging.info("Zeroing the workpoint.")
			self.workpoint.zero()
		else:
			logging.warning("No workpoint to zero, skipping.""")

	def shiftPosition(self,position,uid=None,workpoint=None):
		""" A relative position change. """
		position = list(position)
		logging.info(f"Shifting position by {position}")
		# Set the uid.
		self.uid = str(uid)

		# Set the work point if required.
		if (workpoint is not None) and (self.workpoint is not None):
			if self.config.simulatenousCommands:
				logging.warning("This may cause problems due to timing. This is untested - and should probably be reworked when it is needed.")
				self.workpoint.offset(workpoint)
			else:
				self.motionQueue.append((self.workpoint.offset,(workpoint),self.workpoint.workpointSet))

		# Iterate through available motors.
		for motor in self.currentMotors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			if self.config.simulatenousCommands:
				motor.shiftPosition(value)
			else:
				self.motionQueue.append((motor.shiftPosition,(value),motor.moveFinished))
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

		if not self.config.simulatenousCommands: 
			# Start the queue.
			self.runMotorQueue()

	def setPosition(self,position,uid=None,workpoint=None):
		""" A direct position change. """
		position = list(position)
		logging.info(f"Setting position to {position}")
		# Set the uid.
		self.uid = str(uid)

		# Set the work point if required.
		if (workpoint is not None) and (self.workpoint is not None):
			if self.config.simulatenousCommands:
				logging.warning("This may cause problems due to timing. This is untested - and should probably be reworked when it is needed.")
				self.workpoint.offset(workpoint)
			else:
				self.motionQueue.append((self.workpoint.offset,(workpoint),self.workpoint.workpointSet))

		# Iterate through available motors.
		for motor in self.currentMotors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			if self.config.simulatenousCommands:
				motor.setPosition(value)
			else:
				self.motionQueue.append((motor.setPosition,(value),motor.moveFinished))
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

		if not self.config.simulatenousCommands:
			# Start the queue.
			self.runMotorQueue()

	def runMotorQueue(self):
		""" Run all the items in the queue one at a time. Uses FIFO approach. """
		# If we had a trigger before, disconnect it.
		if self._workflowLastTrigger is not None: 
			self._workflowLastTrigger.disconnect(self.runMotorQueue)
			self._workflowLastTrigger = None

		if len(self.motionQueue) > 0:
			# Take the first item and pop it.
			item = self.motionQueue.pop(0)
			# Unpack the queue item.
			func,args,trigger = item
			# Keep a reference to the trigger.
			self._workflowLastTrigger = trigger
			# Make a trigger if required.
			if self._workflowLastTrigger is not None: 
				# Connect it to the the run workflow function.
				self._workflowLastTrigger.connect(self.runMotorQueue)
			# Data prep.
			if type(args) != list: 
				args = [args]
			# Run the function with the arguments.
			func(*args)
			# If no trigger was provided for the next item... just trigger it automatically.
			if self._workflowLastTrigger is None:
				self.runWorkflowQueue()
		else:
			# Disconnect any signals that are being held on to.
			if self._workflowLastTrigger is not None:
				self._workflowLastTrigger.disconnect(self.runMotorQueue)
				self._workflowLastTrigger = None

	def _finished(self):
		# Increment the counter.
		self._counter += 1
		logging.debug(f"Motor {self._counter} of {len(self.currentMotors)} finished movement.")
		# If counter finished, emit finished signal.
		if self._counter == len(self.currentMotors):
			# Reset the counter.
			self._counter = 0
			# Send signal.
			logging.debug("Emitting finished move.")
			# Set the uid to none before sending out the signal.
			uid = str(self.uid)
			self.uid = None
			self.finishedMove.emit(uid)

	def verticalScan(self,scanRange,mode,speed):
		# Pass one argument for scan range and it will just go to that position.
		# Pass two arguments in a tuple and it will go to start then go to stop.
		if type(scanRange) == tuple:
			start,stop = scanRange
		else:
			start = np.NaN
			stop = scanRange
		logging.debug(f"Running an {mode} vertical scan between {start:.3f} and {stop:.3f} at speed {speed:.3f}.")
		# Make the motion queue.
		if mode == 'absolute':
			if not np.isnan(start): self.motionQueue.append((self.verticalTranslationMotor,self.verticalTranslationMotor.setPosition,(start)))
			self.motionQueue.append((self.verticalTranslationMotor.setPosition,(stop),self.verticalTranslationMotor.moveFinished))
		elif mode == 'relative':
			if not np.isnan(start): self.motionQueue.append((self.verticalTranslationMotor,self.verticalTranslationMotor.shiftPosition,(start)))
			self.motionQueue.append((self.verticalTranslationMotor.shiftPosition,(stop),self.verticalTranslationMotor.moveFinished))
		# Run the motion queue.
		self.runMotorQueue()

	def position(self,idx=None):
		# return the current position of the stage in Global XYZ.
		pos = np.array([0,0,0,0,0,0],dtype=float)
		for motor in self.currentMotors:
			# Read motor position and the axis it works on.
			mpos = motor.readPosition()
			axis = motor._axis + (3*motor._type)
			# Add value to the overall position.
			if mpos == np.inf: 
				mpos = 0
			pos[axis] += mpos

		# Return the position.
		if idx is not None:
			return pos[idx]
		else: 
			return pos

	def calculateMotion(self,G,variables):
		# We take in the 4x4 transformation matrix G, and a list of 6 parameters (3x translations, 3x rotations).
		self._i += 1
		if self._i > 10: 
			return
		# Create a transform for this stage, S.
		S = np.identity(4)
		Si = np.identity(4)
		# Position of motor in stack (in mm).
		stackPos = np.array([0,0,0])
		# Make a copy so original stays intact.
		calcVars = np.array(variables)
		# Iterate over each motor in order.
		for motor in self.currentMotors:
			# Get the x y z translation or rotation value.
			value = calcVars[(motor._axis + (3*motor._type))]
			# Take as much of this as you can if it fits within the limits of the motor!!
			# Set the taken variable to 0. This stops any future motor from taking this value.
			calcVars[(motor._axis + (3*motor._type))] = 0
			# Get the transform for the motor.
			if motor._type == 0:
				T = motor.transform(value)
				Ti = np.identity(4)
			elif motor._type == 1:
				T, Ti = motor.transform(value)
			# Multiply the transform into the overall transform.
			S = S@T
			Si = Si@Ti
		# Take out all unecessary shit. (Undo maths for translations on rotations.)
		St = S@Si
		# Now we have S, a 4x4 transform that encompases all motors.
		remainder = np.linalg.inv(St)@G
		t = np.array(St[:3,3]).reshape(3,)
		r = np.array(St[:3,:3]).reshape(3,3)

		# Start by assuming a successful decomposition.
		success = True

		# Update variables to match stage movements.
		if np.isclose( np.sum(np.absolute(remainder[:3,3])) ,0, atol=1e-02) == False:
			# Check to see if remainder is within less than 1 micron tolerance.
			variables[:3] = np.linalg.inv(S[:3,:3])@G[:3,3]
			success = False

		# Extract any extra angles or just report back whats missing. This involves extracting angles.
		# Can do something with varTracking to see how many have gone down to 0. Can be used to show that we can't account for some parts of the movement?

		# Re-iterate this function with the adjusted vars.
		if success is False:
			self.calculateMotion(G,variables)

		elif success is True:
			# Exit the function.
			self._motion = variables
			return self._motion

	def applyMotion(self,variables=None,uid=None):
		# If no motion is passed, then apply the stored motion.
		if variables == None:
			variables = self._motion
			logging.info(f'Inside apply motion, vars are now motion: {variables}')

		# Carry out a shift movement.
		if self.config.workpoint:
			# workpoint is set to negative the shift as we want the workpoint to be at the point of interest, not where it ends up.
			self.shiftPosition(variables,uid=uid,workpoint=-variables[:3])
		else:
			self.shiftPosition(variables,uid=uid,workpoint=None)