import numpy as np
from matplotlib import pyplot as plt
from scipy.ndimage import median_filter, gaussian_filter
import epics
import time
import imageio


import logging, coloredlogs
coloredlogs.install(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',datefmt='%H:%M:%S',level=logging.INFO)

"""
Assumes:
	- RUBY In beam
	- Ball bearing on stage in centre of field.
	- BDA centred on synch beam
	- All movements possible wrt rotations on dynmrt (doesn't check if they are possible or not).
"""
# ballbearing on the stage.
# RUBY is in beam.

SAVE = False
PLOT = True

# Ruby HCL IOC.
DET_PV = "SR08ID01DET01"

# This is the left bottom top right of the field in RUBY in pixels.
l = 0
r = epics.caget('{}:ROI1:IMAGE:ArraySize0_RBV'.format(DET_PV))
b = epics.caget('{}:ROI1:IMAGE:ArraySize1_RBV'.format(DET_PV))
t = 0

def getImage(save=False,fname=''):
	logging.info("Acquiring an image.")
	epics.caput('{}:CAM:Acquire.VAL'.format(DET_PV),1,wait=True)
	time.sleep(0.5)
	arr = epics.caget('{}:ROI1:IMAGE:ArrayData'.format(DET_PV))
	_x = epics.caget('{}:ROI1:IMAGE:ArraySize1_RBV'.format(DET_PV))
	_y = epics.caget('{}:ROI1:IMAGE:ArraySize0_RBV'.format(DET_PV))
	time.sleep(0.1)
	arr = np.flipud(np.array(arr,dtype=np.uint16).reshape(_x,_y))[t:b,l:r]
	# Remove any weird values.
	arr = np.nan_to_num(arr)
	arr = median_filter(arr,size=(2,2))
	if save:
		imageio.imsave('./cache/{}.tif'.format(fname),arr)
	return arr

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
exposureTime = 0.01
logging.info("Setting up RUBY acquisition parameters.")
epics.caput('{}:CAM:Acquire.VAL'.format(DET_PV),0,wait=True)
epics.caput('{}:CAM:AcquireTime.VAL'.format(DET_PV),exposureTime)
epics.caput('{}:CAM:AcquirePeriod.VAL'.format(DET_PV),0.00)
epics.caput('{}:CAM:ImageMode.VAL'.format(DET_PV),'Single',wait=True)
epics.caput('{}:TIFF:AutoSave.VAL'.format(DET_PV),'No',wait=True)
epics.caput('{}:CAM:Acquire.VAL'.format(DET_PV),1,wait=True)


######################
# CALCULATE PIXEL SIZE
######################

# Distance to travel in mm.
_distance = 9
# Ball bearing sizes.
_bb = 2.0

closeShutter()
# Get darkfield.
logging.info("Getting darkfield.")
dark = getImage(save=SAVE,fname='darkfield')
# Get flood field.
epics.caput('SR08ID01SST25:SAMPLEV.TWV',5,wait=True)
epics.caput('SR08ID01SST25:SAMPLEV.TWR',1,wait=True)
openShutter()
logging.info("Getting floodfield.")
flood = getImage(save=SAVE,fname='flood') - dark
epics.caput('SR08ID01SST25:SAMPLEV.TWF',1,wait=True)

if PLOT:
	fig,ax = plt.subplots(1,2)
	ax = ax.flatten()
	ax[0].imshow(dark,cmap='gray')
	ax[1].imshow(flood,cmap='gray')
	plt.show()

image = []
# Get first image.
image.append((getImage(save=SAVE,fname='bb-trans-p1')-dark)/flood)
# Move to 1 mm.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',_distance,wait=True)
# Get second image.
image.append((getImage(save=SAVE,fname='bb-trans-p2')-dark)/flood)
# Put H2 back.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',0,wait=True)

# The row in the image to take.
_line = int((b-t)/2)
_width = 30

# Take line profile of each.
logging.info("Taking line profiles of images.")
line = []
for i in range(len(image)):
	image[i] = gaussian_filter(image[i],sigma=10)
	temp = image[i][_line,:].astype(float)
	line.append(np.absolute(temp-temp.max()))
# Find the peaks.
peaks = []
for i in range(len(line)):
	peak = np.argmax(line[i])
	peaks.append(peak)

if PLOT:
	fig,ax = plt.subplots(2,2)
	ax = ax.flatten()
	ax[0].plot(np.linspace(0,len(line[0]),len(line[0])),line[0])
	ax[1].plot(np.linspace(0,len(line[0]),len(line[0])),line[1])
	ax[2].imshow(image[0],cmap='gray')
	ax[3].imshow(image[1],cmap='gray')
	plt.show()

pixelSize = _distance/np.absolute(peaks[1]-peaks[0])
logging.critical("Pixel Size: {} mm".format(pixelSize))


###############
# CALCULATE COR
###############
logging.info("Calculating centre of rotation.")

image = []
# Rotate to -180.
logging.info("Calculating centre of rotation: 180.")
epics.caput('SR08ID01SST25:ROTATION.VAL',180,wait=True)
image.append((getImage(save=SAVE,fname='bb-180d')-dark)/flood)
# Rotate to -90.
logging.info("Calculating centre of rotation: 90.")
epics.caput('SR08ID01SST25:ROTATION.VAL',90,wait=True)
image.append((getImage(save=SAVE,fname='bb-90d')-dark)/flood)
# Rotate to 0.
logging.info("Calculating centre of rotation: 0.")
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)
image.append((getImage(save=SAVE,fname='bb-0d')-dark)/flood)
# Rotate to 90
logging.info("Calculating centre of rotation: -90.")
epics.caput('SR08ID01SST25:ROTATION.VAL',-90,wait=True)
image.append((getImage(save=SAVE,fname='bb-n90d')-dark)/flood)

# Take line profile of each.
line = []
for i in range(len(image)):
	image[i] = gaussian_filter(image[i],sigma=10)
	temp = image[i][_line,:].astype(float)
	line.append(np.absolute(temp-temp.max()))
# Find the peaks.
peaks = []
for i in range(len(line)):
	peak = np.argmax(line[i])
	peaks.append(peak)
# Calculate relative movements.
d_h1 = np.absolute(peaks[1]-peaks[3])*pixelSize/2
d_h2 = np.absolute(peaks[0]-peaks[2])*pixelSize/2

if PLOT:
	fig,ax = plt.subplots(2,4)
	ax = ax.flatten()
	ax[0].plot(line[0])
	# ax[0].scatter(line[0][peaks[0]],marker='+',color='r')
	ax[1].plot(line[1])
	# ax[1].scatter(line[1][peaks[1]],marker='+',color='r')
	ax[2].plot(line[2])
	# ax[2].scatter(line[2][peaks[2]],marker='+',color='r')
	ax[3].plot(line[3])
	# ax[3].scatter(line[3][peaks[3]],marker='+',color='r')
	ax[4].imshow(image[0],cmap='gray')
	ax[5].imshow(image[1],cmap='gray')
	ax[6].imshow(image[2],cmap='gray')
	ax[7].imshow(image[3],cmap='gray')
	plt.show()

# Move H1.
logging.info("Moving the ball-bearing to the centre of rotation.")
epics.caput('SR08ID01SST25:SAMPLEH1.TWV',d_h1,wait=True)
if peaks[1] < peaks[3]:
	epics.caput('SR08ID01SST25:SAMPLEH1.TWF',1,wait=True)
else:
	epics.caput('SR08ID01SST25:SAMPLEH1.TWR',1,wait=True)
# Move H2.
epics.caput('SR08ID01SST25:SAMPLEH2.TWV',d_h2,wait=True)
if peaks[2] < peaks[0]:
	epics.caput('SR08ID01SST25:SAMPLEH2.TWF',1,wait=True)
else:
	epics.caput('SR08ID01SST25:SAMPLEH2.TWR',1,wait=True)

logging.info("Acquiring final image of centre of rotation.")
# Take final image of iso.
finalImage = (getImage(save=SAVE,fname='bb-isocenter')-dark)/flood
closeShutter()

# Blur the image for smoothing.
finalImage = gaussian_filter(finalImage,sigma=10)
# Take line profiles and find the horiz and vertical centre of the bb.
# Horizontal.
temp_horiz = finalImage[_line,:].astype(float)
line_horiz = np.absolute(temp_horiz-temp_horiz.max())
col = np.argmax(line_horiz)
# Vertical.
temp_vert = finalImage[:,col].astype(float)
line_vert = np.absolute(temp_vert-temp_vert.max())
row = np.argmax(line_vert)
# Position.
pos = [row,col]
logging.critical("Image isocenter (row,col): {}".format(pos))

# NOW NEED TO DO VERTICAL ALIGNMENT!!!!


# Set rotation back to home.
logging.info("Moving ball-bearing back to 0 deg rotation.")
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)

logging.info("Finished! Wasn't that easy?")

if PLOT:
	fig,ax = plt.subplots(1,2)
	ax = ax.flatten()
	ax[0].imshow(finalImage)
	ax[0].scatter(pos[1],pos[0],marker='+',color='r')
	ax[1].plot(line_horiz)
	plt.show()