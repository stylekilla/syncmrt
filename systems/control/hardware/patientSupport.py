from systems.control.hardware.motor import motor
from PyQt5 import QtCore, QtWidgets
import numpy as np
import logging

class patientSupport(QtCore.QObject):
	# startedMove = QtC
	# moving = QtCore.pyqtSignal()
	finishedMove = QtCore.pyqtSignal()
	# error = QtCore.pyqtSignal()

	# This needs to be re-written to accept 6DoF movements and split it up into individual movements.

	def __init__(self,database,ui=None):
		super().__init__()
		# Information
		self.currentDevice = None
		self.currentMotors = []
		self._dof = (0,[0,0,0,0,0,0])
		# A preloadable motion.
		self._motion = None
		# Stage size information.
		self._size = np.array([0,0,0])
		# Calibration object size.
		self._offset = np.array([0,0,0])
		# UI elements.
		self._ui = ui
		# Motor counter for finished arguments.
		self._counter = 0
		# Counter for calculate motion loop.
		self._i = 0

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
		logging.info("Loading patient support: {}.".format(name))
		if name in self.deviceList:
			# Remove all motors.
			for i in range(len(self.currentMotors)):
				del self.currentMotors[-1]
			# Iterate over new motors.
			for support in self.motors:
				# Does the motor match the name?
				if support['PatientSupport'] == name:
					# Define the new motor.
					newMotor = motor(
							support['Description'],
							int(support['Axis']),
							int(support['Order']),
							pv = support['PV Root']
						)
					# Set a ui for the motor if we are doing that.
					if self._ui is not None:
						newMotor.setUi(self._ui)
					# Connect to finished method.
					newMotor.finished.connect(self._finished)
					# Append the motor to the list.
					self.currentMotors.append(newMotor)
			# Set the order of the list from 0-i.
			self.currentMotors = sorted(self.currentMotors, key=lambda k: k._order) 
			# Update the name details.
			self.currentDevice = name
			# Calibrate with no calibration offset. This can be recalculated later.
			self.calibrate(np.array([0,0,0]))
			# Update GUI.
			if self._ui is not None:
				self._ui.update()

	def reconnect(self):
		for motor in self.currentMotors:
			motor.reconnectControls()

	def calibrate(self,calibration):
		# Stage size in mm including calibration offset (i.e. a pin or object used to calibrate the stage).
		self._offset = calibration
		self._size = calibration
		for motor in self.currentMotors:
			if motor._stage == 0:
				self._size = np.add(self._size,motor._size)

	def shiftPosition(self,position):
		logging.info("Shifting position to {}".format(position))
		# This is a relative position change.
		# Iterate through available motors.
		for motor in self.currentMotors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			motor.shiftPosition(value)
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

	def setPosition(self,position):
		logging.info("Setting position to {}".format(position))
		# This is a direct position change.
		# Iterate through available motors.
		for motor in self.currentMotors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			motor.setPosition(value)
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

	def _finished(self):
		# Increment the counter.
		self._counter += 1
		logging.debug("Motor {} of {} finished movement.".format(self._counter,len(self.currentMotors)))
		# If counter finished, emit finished signal.
		if self._counter == len(self.currentMotors):
			# Reset the counter.
			self._counter = 0
			# Send signal.
			logging.debug("Emitting finished move.")
			self.finishedMove.emit()

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
		if self._i > 10: return
		# Create a transform for this stage, S.
		print('\n'*3)
		logging.info('Stage Name: {}'.format(self.currentDevice))
		logging.info('Variables: {}'.format(variables))
		S = np.identity(4)
		Si = np.identity(4)
		# Position of motor in stack (in mm).
		stackPos = np.array([0,0,0])
		# NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!
		np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})
		# Make a copy so original stays intact.
		calcVars = np.array(variables)
		# Iterate over each motor in order.
		for motor in self.currentMotors:
			logging.info('Motor Name: {}'.format(motor.name))
			# Get the x y z translation or rotation value.
			value = calcVars[(motor._axis + (3*motor._type))]
			# Take as much of this as you can if it fits within the limits of the motor!!
			# print('calcVars before',calcVars)
			# Set the taken variable to 0. This stops any future motor from taking this value.
			calcVars[(motor._axis + (3*motor._type))] = 0
			# print('calcVars after',calcVars)
			# Add current motor height in stack.
			if motor._stage == 0:
				stackPos += motor._size
			# If it has a working distance, update the working point.
			if sum(motor._workDistance) > 0:
				# Get the current position of the stage.
				stagePos = self.position()
				motor.calculateWorkPoint(stagePos,self._size,stackPos)
			# Get the transform for the motor.
			if motor._type == 0:
				T = motor.transform(value)
				Ti = np.identity(4)
			elif motor._type == 1:
				T, Ti = motor.transform(value)
			# Multiply the transform into the overall transform.
			# print('****** MOTOR NUMBER ',motor._order,':')
			# print('====== T:')
			# print(T)
			S = S@T
			Si = Si@Ti 
			# print('=== S:')
			# print(S)
		# Take out all unecessary shit. (Undo maths for translations on rotations.)
		St = S@Si
		# Now we have S, a 4x4 transform that encompases all motors.
		print('****** RESULTS:')
		print('====== Global:')
		print(G)
		print('====== Stage:')
		print(St)
		remainder = np.linalg.inv(St)@G
		print('====== Remainder:')
		# remainder[:3,3] = G[:3,3]+S[:3,3]
		print(remainder)
		t = np.array(St[:3,3]).reshape(3,)
		r = np.array(St[:3,:3]).reshape(3,3)

		# Start by assuming a successful decomposition.
		success = True

		# Update variables to match stage movements.
		logging.info('a: {}'.format(np.sum(remainder[:3,3])))
		print(np.isclose( np.sum(np.absolute(remainder[:3,3])) ,0, atol=1e-02))
		if np.isclose( np.sum(np.absolute(remainder[:3,3])) ,0, atol=1e-02) == False:
			# Check to see if remainder is within less than 1 micron tolerance.
			# If the translations aren't 0 then subtract the updates to the vars.
			# print('variables before additions: ',variables[:3])
			# print('remainder: ',remainder[:3,3])
			print("WAS FALSE....")
			
			logging.info('variables: {}'.format(variables))
			logging.info('stage pos: {}'.format(S))
			# May have to rejig this for other stages where it goes through the actual process?
			# variables[:3] += S[:3,:3]@remainder[:3,3]
			variables[:3] = np.linalg.inv(S[:3,:3])@G[:3,3]
			logging.info('variables changed: {}'.format(variables))
			# variables[:3] += remainder[:3,3]@S[:3,:3]
			# variables[:3] -= remainder[:3,3]@S[:3,:3]

			# variables[:3] -= np.array(S[:3,3]@remainder[:3,3]).reshape(3,)
			# print('S: ',S[:3,3])
			# print('S: ',S[:3,3])
			# print('combined: ',S[:3,3] - remainder[:3,3])
			# variables[:3] = S[:3,3] - remainder[:3,3]
			# print('variables after additions: ',variables[:3])
			success = False

		# Extract any extra angles or just report back whats missing. This involves extracting angles.
		# Can do something with varTracking to see how many have gone down to 0. Can be used to show that we can't account for some parts of the movement?

		# Re-iterate this function with the adjusted vars.
		if success is False:
			self.calculateMotion(G,variables)

		elif success is True:
			# Exit the function.
			self._motion = variables
			logging.critical('Self Motion on success: {}'.format(self._motion))
			return self._motion

	def applyMotion(self,variables=None):
		# If no motion is passed, then apply the preloaded motion.
		if variables == None:
			variables = self._motion
			logging.info('inside apply motion, vars are now motion: {}'.format(variables))
		logging.critical("Applying motion: {}".format(variables))
		# Iterate over each motor in order.
		for motor in self.currentMotors:
			# Understand the motors function.
			index = motor._axis + (3*motor._type)
			# Get the x y z translation or rotation value.
			value = variables[index]
			# Apply the value.
			motor.shiftPosition(value)
			logging.info('Moving {}: {}'.format(motor.name,value))
			# Set the taken variable to 0. This stops any future motor from taking this value.
			variables[index] = 0
			# Connect to finished method.
			motor.finished.connect(self._finished)
		QtWidgets.QMessageBox.warning(None,"Patient Alignment","Movement finished.")
		return

		'''
		Start with removing the rotations.
		To remove these, we need to know the shift of the P in relation to the rotation origin.
		what's left = T*M[rx]^-1
		Find working origin.
		what's left = T*M[ry]^-1
		what's left = T*M[rz]^-1
		Whats left now should only be translations.
		After removing the translations, anything left should be considered impossible for the stage to complete. This should go into a "accuracy" measurement

		Take position of stage when working distance is at the origin. homePos
		Get the working distance, workDist
		Get it's current position. currPos
		workPos = currPos + workDist (this is the point we will rotate around)
		Transform needs the workPos.
		'''


