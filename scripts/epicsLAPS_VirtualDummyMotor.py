import epics
import logging
import numpy as np


# # METHOD 1: PUSH RBV FROM LAPS TO VIRTUAL MOTOR Z CONTINUOUSLY. 
# laps = epics.PV("SR08ID01ROB01:MOTOR_Z.RBV")
# virtualMotor = epics.PV("SR08ID01ZORRO:Z.VAL")
# 
# while True:
# 	virtualMotor.put(float(laps.get()))

# METHOD 2: WHEN LAPS STARTS TO MOVE... WRITE THE VALUE TO THE VIRTUAL MOTOR ALSO. 
lapsZ = epics.PV("SR08ID01ROB01:MOTOR_Z.VAL")
lapsVelocity = epics.PV("SR08ID01ROB01:VELOCITY.VAL")
lapsDoneMoving = epics.PV("SR08ID01ROB01:MOTOR_Z.DMOV")
virtualMotor = epics.PV("SR08ID01ZORRO:Z.VAL")
virtualMotorVelocity = epics.PV("SR08ID01ZORRO:Z.VELO")
virtualMotorAcceleration = epics.PV("SR08ID01ZORRO:Z.ACCL")


old = float(lapsVelocity.get())

while True:
	new = float(lapsVelocity.get())
	if new != old:
		virtualMotorVelocity.put(new)

	if float(lapsDoneMoving.get()) == 0:
		# If LAPS is on the move.... get the set value and write that to the virtual motor also.
		# This assumes both are moving at the same speed...
		value = float(lapsZ.get())
		sign = np.sign(value)
		writeValue = np.amin([np.absolute(value),13.0])
		virtualMotor.put(sign*writeValue)