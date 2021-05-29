import epics
import numpy as np

# https://manual.nexusformat.org/examples/epics/index.html

# Setting things up.
home = 0.0
start = 100.0
stop = -100.0
speed = 5
distance = start-stop
time = distance/speed

useBeam = True

# Number of pixels to read out.
readoutHeight = 10
pixelSize = 0.044

# Calculate detector settings.
acquireTime = (readoutHeight*pixelSize)/speed
acquirePeriod = acquireTime
numberOfImages = int(time/acquireTime + 1)

message = f""" 
Dynamic Imaging Inputs:
=======================
home			= {home}
start			= {start}
stop			= {stop}
speed			= {speed}
distance		= {distance}
time			= {time}
useBeam			= {useBeam}
readoutHeight	= {readoutHeight}
pixelSize		= {pixelSize}
acquireTime		= {acquireTime}
acquirePeriod	= {acquirePeriod}
numberOfImages	= {numberOfImages}
"""
print(message)

print("Initializing image.")
imagedir = 'D:\\syncmrt\\'
filename = "CanineImaging4"

print("Setting up detector.")
epics.caput("SR08ID01ROB01:VELOCITY", speed, wait=True)
epics.caput("SR08ID01DETIOC10:CAM:Acquire", 0, wait=True)			# Stop any current capturing.
epics.caput("SR08ID01DETIOC10:TIFF:AutoSave", False, wait=True)		# Turn off tiff file saving.

# HDF5 Setup.
epics.caput("SR08ID01DETIOC10:HDF:Capture", 0)
epics.caput("SR08ID01DETIOC10:HDF:FilePath", imagedir, wait=True)
epics.caput("SR08ID01DETIOC10:HDF:FileName", filename, wait=True)		# A unique identifier.
epics.caput("SR08ID01DETIOC10:HDF:AutoSave", True, wait=True)		# Auto save file.
epics.caput("SR08ID01DETIOC10:HDF:FileWriteMode", 2, wait=True)		# Streaming mode = 2.
epics.caput("SR08ID01DETIOC10:HDF:NumCapture", numberOfImages, wait=True)
epics.caput("SR08ID01DETIOC10:HDF:AutoIncrement", False, wait=True)
epics.caput("SR08ID01DETIOC10:HDF:NDArrayPort", 'pcoEdge.cam.roi1', wait=True)
epics.caput("SR08ID01DETIOC10:HDF:NDAttributesFile", "D:\\syncmrt\\LAPSPositionTracker.xml", wait=True)		# XML file for LAPS Z position Tracker.

# Capture an initial image for ROI array dimensions in HDF.
# epics.caput("SR08ID01DETIOC10:CAM:AcquireTime", 0.1, wait=True)
# epics.caput("SR08ID01DETIOC10:CAM:AcquirePeriod", 0.1, wait=True)
# epics.caput("SR08ID01DETIOC10:CAM:ImageMode", 0, wait=True)
# epics.caput("SR08ID01DETIOC10:CAM:Acquire", 1, wait=True)

# Setup our imaging parameters.
epics.caput("SR08ID01DETIOC10:CAM:AcquireTime", acquireTime, wait=True)
epics.caput("SR08ID01DETIOC10:CAM:AcquirePeriod", acquirePeriod, wait=True)
epics.caput("SR08ID01DETIOC10:CAM:NumImages", numberOfImages, wait=True)
epics.caput("SR08ID01DETIOC10:CAM:ImageMode", 1, wait=True)			# Multiple mode = 1.
epics.caput("SR08ID01DETIOC10:CAM:ArrayCounter", 0, wait=True)

print("Opening HDF file.")
epics.caput("SR08ID01DETIOC10:HDF:Capture", 1)		# Must start the capture process first.

print("Moving to start position.")
epics.caput("SR08ID01ROB01:MOTOR_Z", start, wait=True)

print("Waiting {}s.".format(time))
import time as ttime
ttime.sleep(np.absolute(start/speed)+2)

# STEP 3: Open Shutters...
if useBeam:
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

print("Starting acquisition.")
# There is a 1.5s delay between motor start and image start.
epics.caput("SR08ID01DETIOC10:CAM:Acquire", 1)
ttime.sleep(1.4)
epics.caput("SR08ID01ROB01:MOTOR_Z", stop, wait=True)
ttime.sleep(0.1)

# while epics.caget("SR08ID01ROB01:MOTOR_Z.DMOV"):
# 	print("Moving")
# 	pass

# STEP 5: Close Shutters...
if useBeam:
	print("Closing shutters...")
	# epics.caput("SR08ID01PSS01:FE_SHUTTER_CLOSE_CMD.VAL",1,wait=True)
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD.VAL",1, wait=True)
	wait = True
	while wait:
		# If shutter status is 3 then the shutter is open.
		# If it is 2 it is closed.
		# if (epics.caget("SR08ID01PSS01:HU01A_SF_SHUTTER_STS") == 2) & (epics.caget("SR08ID01PSS01:FE_SHUTTER_STS") == 2): 
		if (epics.caget("SR08ID01PSS01:HU01A_SF_SHUTTER_STS") == 2): 
			wait = False
	print("Shutters closed.")


print("Finished. Moving to home position.")
# Stop the capture.
epics.caput("SR08ID01DETIOC10:HDF:Capture", 0, wait=True)
epics.caput("SR08ID01ROB01:MOTOR_Z", home, wait=True)




# 'Acquire': 'CAM:Acquire',
# 'AcquireTime': 'CAM:AcquireTime',
# 'AcquirePeriod': 'CAM:AcquirePeriod',
# 'ArrayCounter': 'CAM:ArrayCounter',
# 'NumImages': 'CAM:NumImages',
# 'ImageMode': 'CAM:ImageMode',
# 'AutoSave': 'TIFF:AutoSave',
# 'DataType': 'IMAGE:DataType_RBV',
# 'ArraySize0': 'CAM:ArraySizeX_RBV',
# 'ArraySize1': 'CAM:ArraySizeY_RBV',
# 'RoiData': 'ROI1:IMAGE:ArrayData',
# 'ArrayData': 'IMAGE:ArrayData',
