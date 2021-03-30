import epics
import logging

def treat(
		field = [-5,5],
		homePosition=0,
		velocity = 3.0,
		acceleration = 0.0
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
	print("Setting velocity/acceleration.")
	# Set the velocity.
	epics.caput("SR08ID01ROB01:VELOCITY.VAL", float(velocity), wait=True)
	# Set the acceleration, if unspecified (i.e. 0.0) then default to twice the velocity.
	if acceleration == 0.0: acceleration = 3*float(velocity)
	epics.caput("SR08ID01ROB01:ACCELERATION.VAL", float(acceleration), wait=True)

	# # STEP 2: Move to home position.
	# epics.caput("SR08ID01ROB01:MOTOR_X.VAL", float(homePosition[0]), wait=True)
	# epics.caput("SR08ID01ROB01:MOTOR_Y.VAL", float(homePosition[1]), wait=True)
	# epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", float(homePosition[2]), wait=True)
	# epics.caput("SR08ID01ROB01:MOTOR_XTILT.VAL", float(homePosition[3]), wait=True)
	# epics.caput("SR08ID01ROB01:MOTOR_YTILT.VAL", float(homePosition[4]), wait=True)
	# epics.caput("SR08ID01ROB01:MOTOR_ZTILT.VAL", float(homePosition[5]), wait=True)
	# epics.caput("SR08ID01ZORRO:Z.VAL", float(homePosition[2]), wait=True)

	# STEP 2: Calculate and move to offset required.
	time = velocity/acceleration
	distance = 0.5*acceleration*(time**2)
	startPosition = homePosition + field[1] + distance
	endPosition = homePosition + field[0] - distance

	print("Moving to start position.")
	epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", float(startPosition), wait=True)

	# STEP 3: Open Shutters...
	print("Opening shutters...")
	epics.caput("SR08ID01PSS01:FE_SHUTTER_OPEN_CMD.VAL",1, wait=True)
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD.VAL",1, wait=True)
	wait = True
	while wait:
		# If shutter status is 3 then the shutter is open.
		# If it is 2 it is closed.
		if (epics.caget("SR08ID01PSS01:HU01A_SF_SHUTTER_STS") == 3) & (epics.caget("SR08ID01PSS01:FE_SHUTTER_STS") == 3): 
			wait = False
	print("Shutters open.")

	print("Moving LAPS.")
	# STEP 4: Start a combined movement with LAPS and Zorro.
	epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", float(endPosition), wait=True)

	# STEP 5: Close Shutters...
	print("Closing shutters...")
	epics.caput("SR08ID01PSS01:FE_SHUTTER_CLOSE_CMD.VAL",1,wait=True)
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD.VAL",1, wait=True)
	wait = True
	while wait:
		# If shutter status is 3 then the shutter is open.
		# If it is 2 it is closed.
		if (epics.caget("SR08ID01PSS01:HU01A_SF_SHUTTER_STS") == 2) & (epics.caget("SR08ID01PSS01:FE_SHUTTER_STS") == 2): 
			wait = False
	print("Shutters closed.")

	print("Returning Home.")
	# STEP 6: Return to home position.
	epics.caput("SR08ID01ROB01:MOTOR_Z.VAL", float(homePosition), wait=True)
	print("Finished.")


treat(field=[-10,20],homePosition=82.0,velocity=5.0,acceleration=0.0)