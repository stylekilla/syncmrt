import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import find_peaks
import epics
import time
import imageio


import logging, coloredlogs
coloredlogs.install(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',datefmt='%H:%M:%S',level=logging.DEBUG)


"""
Assumes:
	- RUBY In beam
	- Ball bearing on stage in centre of field.
	- BDA centred on synch beam
	- All movements possible wrt rotations on dynmrt (doesn't check if they are possible or not).
"""
# ballbearing on the stage.
# RUBY is in beam.


# This is the left bottom top right of the field in RUBY in pixels.
l = 0
r = 2560
b = 1250
t = 1019

def getImage(save=False,fname=''):
	logging.info("Acquiring an image.")
	epics.caput('SR08ID01DET01:CAM:Acquire.VAL',1,wait=True)
	arr = epics.caget('SR08ID01DET01:IMAGE:ArrayData')
	_x = epics.caget('SR08ID01DET01:IMAGE:ArraySize1_RBV')
	_y = epics.caget('SR08ID01DET01:IMAGE:ArraySize0_RBV')
	time.sleep(0.1)
	ary = np.flipud(np.array(arr,dtype=np.uint16).reshape(_x,_y))[t:b,l:r]
	if save:
		imageio.imsave('./{}.tif'.format(fname),ary)
	return ary

def closeShutter():
	logging.info("Closing 1A shutter.")
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)
	time.sleep(2)

def openShutter():
	logging.info("Opening 1A shutter.")
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD", 1, wait=True)
	time.sleep(2)

# Set home.
logging.info("Moving DynMRT stages to home positions.")
epics.caput('SR08ID01SST25:SAMPLEH1.VAL',0,wait=True)
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',0,wait=True)
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)

########################
# START RUBY ACQUISITION
########################
exposureTime = 1.0
logging.info("Setting up RUBY acquisition parameters.")
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',0,wait=True)
epics.caput('SR08ID01DET01:CAM:AcquireTime.VAL',exposureTime)
epics.caput('SR08ID01DET01:CAM:AcquirePeriod.VAL',0.00)
epics.caput('SR08ID01DET01:CAM:ImageMode.VAL','Single',wait=True)
epics.caput('SR08ID01DET01:TIFF:AutoSave.VAL','No',wait=True)
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',1,wait=True)


######################
# CALCULATE PIXEL SIZE
######################

# Distance to travel in mm.
_distance = 10

closeShutter()
# Get darkfield.
logging.info("Getting darkfield.")
dark = getImage(save=True,fname='darkfield')
# Get flood field.
epics.caput('SR08ID01SST25:SAMPLEV.TWV',5,wait=True)
epics.caput('SR08ID01SST25:SAMPLEV.TWR',1,wait=True)
openShutter()
logging.info("Getting floodfield.")
flood = getImage(save=True,fname='flood') - dark
epics.caput('SR08ID01SST25:SAMPLEV.TWF',1,wait=True)

image = []
# Get first image.
image.append((getImage(save=True,fname='bb-trans-p1')-dark)/flood)
# Move to 1 mm.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',_distance,wait=True)
# Get second image.
image.append((getImage(save=True,fname='bb-trans-p2')-dark)/flood)
# Put H2 back.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',0,wait=True)

# The row in the image to take.
_line = int((b-t)/2)
_width = 30

# Take line profile of each.
logging.info("Taking line profiles of images.")
line = []
for i in range(len(image)):
	temp = image[i][_line,:].astype(float)
	line.append(np.absolute(temp-temp.max()))

# Find the peaks.
peaks = []
for i in range(len(line)):
	_peaks, _ = find_peaks(line[i],width=_width)
	peaks.append(_peaks)

fig,ax = plt.subplots(2,2)
ax = ax.flatten()
ax[0].plot(np.linspace(0,len(line[0]),len(line[0])),line[0])
ax[1].plot(np.linspace(0,len(line[0]),len(line[0])),line[1])
ax[2].imshow(image[0],cmap='gray')
ax[3].imshow(image[1],cmap='gray')
plt.show()

pixelSize = _distance/np.absolute(peaks[1]-peaks[0])[0]
logging.critical("Pixel Size: {} mm".format(pixelSize))


###############
# CALCULATE COR
###############
logging.info("Calculating centre of rotation.")

image = []
# Rotate to -180.
logging.info("Calculating centre of rotation: -180.")
epics.caput('SR08ID01SST25:ROTATION.VAL',-180,wait=True)
image.append((getImage(save=True,fname='bb-n180d')-dark)/flood)
# Rotate to -90.
logging.info("Calculating centre of rotation: -90.")
epics.caput('SR08ID01SST25:ROTATION.VAL',-90,wait=True)
image.append((getImage(save=True,fname='bb-n90d')-dark)/flood)
# Rotate to 0.
logging.info("Calculating centre of rotation: 0.")
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)
image.append((getImage(save=True,fname='bb-0d')-dark)/flood)
# Rotate to 90
logging.info("Calculating centre of rotation: 90.")
epics.caput('SR08ID01SST25:ROTATION.VAL',90,wait=True)
image.append((getImage(save=True,fname='bb-90d')-dark)/flood)

# Take line profile of each.
line = []
for i in range(len(image)):
	temp = image[i][_line,:].astype(float)
	line.append(np.absolute(temp-temp.max()))
	# line.append(np.absolute(np.invert(temp)))

# Find the peaks.
peaks = []
for i in range(len(line)):
	_peaks, _ = find_peaks(line[i],width=_width)
	peaks.append(_peaks)

# Calculate relative movements.
d_h1 = (peaks[1]-peaks[3])*pixelSize/2
d_h2 = (peaks[0]-peaks[2])*pixelSize/2

# fig,ax = plt.subplots(2,4)
# ax = ax.flatten()
# ax[0].plot(line[0])
# # ax[0].scatter(line[0][peaks[0]],marker='+',color='r')
# ax[1].plot(line[1])
# # ax[1].scatter(line[1][peaks[1]],marker='+',color='r')
# ax[2].plot(line[2])
# # ax[2].scatter(line[2][peaks[2]],marker='+',color='r')
# ax[3].plot(line[3])
# # ax[3].scatter(line[3][peaks[3]],marker='+',color='r')
# ax[4].imshow(image[0],cmap='gray')
# ax[5].imshow(image[1],cmap='gray')
# ax[6].imshow(image[2],cmap='gray')
# ax[7].imshow(image[3],cmap='gray')
# plt.show()

# Move H1.
logging.info("Moving the ball-bearing to the centre of rotation.")
epics.caput('SR08ID01SST25:SAMPLEH1.TWV',d_h1,wait=True)
if peaks[1] < peaks[3]:
	epics.caput('SR08ID01SST25:SAMPLEH1.TWF',1,wait=True)
else:
	epics.caput('SR08ID01SST25:SAMPLEH1.TWR',1,wait=True)
# Move H2.
epics.caput('SR08ID01SST25:SAMPLEH2.TWV',d_h2,wait=True)
if peaks[0] < peaks[2]:
	epics.caput('SR08ID01SST25:SAMPLEH2.TWF',1,wait=True)
else:
	epics.caput('SR08ID01SST25:SAMPLEH2.TWR',1,wait=True)

logging.info("Acquiring final image of centre of rotation.")
# Take final image of iso.
finalImage = (getImage(save=True,fname='bb-isocenter')-dark)/flood
closeShutter()

# Take line profile of each.
temp = finalImage[_line,:].astype(float)
line = np.absolute(temp-temp.max())

# Find the peaks.
_peaks, _ = find_peaks(line,width=_width)
pos = np.array(finalImage.shape)/2
pos[1] = _peaks[0]
logging.critical("Image isocenter: {}".format(pos))

# Set rotation back to home.
logging.info("Moving ball-bearing back to 0 deg rotation.")
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)

logging.info("Finished! Wasn't that easy?")

# fig,ax = plt.subplots(1,2)
# ax = ax.flatten()
# ax[0].imshow(finalImage)
# # ax[0].hlines(_line)
# ax[0].scatter(pos[1],pos[0],marker='+',color='r')
# plt.show()