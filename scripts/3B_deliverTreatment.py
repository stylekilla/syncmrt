import epics
import logging


def treat(
	startposition=[0,0,13.0,0,0,0],
	velocity = 3.0,
	acceleration = 40.0
	):
	"""
	treat: A function in which we can pass basic parameters to perform a dynamic treatment delivery in 3B on LAPS.
	
	Parameters
	----------
	startposition: list
		Start position for [x,y,z,rx,ry,rz]
	velocity: float
		Target velocity for treatment delivery in mm/s. 
	acceleration: float
		Target acceleration for treatment delivery in mm/s^2.

	Assumptions
	-----------
	1. The TCP is set and irrelevant as we are only moving in the Z-translation axis.
	2. The beam is set up appropriately.
	3. The detector is out of the way (and other devices are positioned appropriately).
	"""

	# Step 1: Set up the robot.
	# Set the velocity.
	epics.caput("SR08ID01ROB01:VELOCITY.VAL", float(velocity), wait=True)
	# Set the acceleration, if unspecified (i.e. 0.0) then default to twice the velocity.
	if acceleration == 0.0: acceleration = 3*float(velocity)
	epics.caput("SR08ID01ROB01:ACCELERATION.VAL", float(acceleration), wait=True)

	# STEP 2: Move to start position.
	epics.caput("SR08ID01ROB01:MOTOR_X.VAL", float(startposition[0]), wait=True)
	epics.caput("SR08ID01ROB01:MOTOR_Y.VAL", float(startposition[1]), wait=True)
	epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", float(startposition[2]), wait=True)
	epics.caput("SR08ID01ROB01:MOTOR_XTILT.VAL", float(startposition[3]), wait=True)
	epics.caput("SR08ID01ROB01:MOTOR_YTILT.VAL", float(startposition[4]), wait=True)
	epics.caput("SR08ID01ROB01:MOTOR_ZTILT.VAL", float(startposition[5]), wait=True)
	epics.caput("SR08ID01ZORRO:Z.VAL", float(startposition[2]), wait=True)

	# STEP 3: Open Shutters...
	epics.caput("", , wait=True)

	# STEP 4: Start a combined movement with LAPS and Zorro... assumes that our epicsLAPS_VirtualDummyMotor.py is running.
	# For now we will just write to the negative start position...
	epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", -float(startposition[2], wait=True)
	# Can also attempt writing both at the same time...
	# epics.caput("SR08ID01ROB01:Z.VAL", -float(startposition[2], wait=True)

