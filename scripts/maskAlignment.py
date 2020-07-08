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
	- Ball bearing is centred on dynmrt rotation isocentre
	- BDA centred on synch beam
	- Masks are 20x20,10x10,5x5.
"""

##################
# INPUT PARAMETERS
##################
logging.critical("These input params are probably wrong. Should be read out of a cfg file.")
# Save images?
SAVE = False
# This is the left bottom top right of the field in RUBY in pixels.
l = 0
r = 2560
b = 1181
t = 944
# Pixel size (in mm) as calculated from COR script.
pixelSize = 0.008


#######################
# INTERNAL CALCULATIONS
#######################
# The row in the image to take.
_col = int((r-l)/2)
_row = int((b-t)/2)

def getImage(save=False,fname=''):
	logging.info("Acquiring an image.")
	epics.caput('SR08ID01DET01:CAM:Acquire.VAL',1,wait=True)
	arr = epics.caget('SR08ID01DET01:IMAGE:ArrayData')
	_x = epics.caget('SR08ID01DET01:IMAGE:ArraySize1_RBV')
	_y = epics.caget('SR08ID01DET01:IMAGE:ArraySize0_RBV')
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

###################################
# START RUBY ACQUISITION PARAMETERS
###################################
exposureTime = 0.1
logging.info("Setting up RUBY acquisition parameters.")
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',0,wait=True)
epics.caput('SR08ID01DET01:CAM:AcquireTime.VAL',exposureTime)
epics.caput('SR08ID01DET01:CAM:AcquirePeriod.VAL',0.00)
epics.caput('SR08ID01DET01:CAM:ImageMode.VAL','Single',wait=True)
epics.caput('SR08ID01DET01:TIFF:AutoSave.VAL','No',wait=True)
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',1,wait=True)

##########################
# GET BALLBEARING POSITION => MIGHT NOT BE NEEDED...???
##########################

# Open the shutter.
openShutter()

##########################
# CALCULATE MASK POSITIONS
##########################
d_v = []

# Iterate over all three masks.
for i in range(3):
	# First mask.
	logging.info("Selecting mask {}.".format(i))
	horizontalImages = []
	verticalImages = []
	# Move to first mask.
	logging.critical("Selecting a mask position is probably wrong. Not sure how epics does that. Check me. In fact, check ALL PV's!")
	epics.caput('SR08ID01SST25:MASK_POS:{}.VAL'.format(i),1,wait=True)
	logging.info("Acquiring images...")
	# Move mask to +ve (right) edge and take an image.
	epics.caput('SR08ID01SST25:MASK.TWV',10,wait=True)
	epics.caput('SR08ID01SST25:MASK.TWF',1,wait=True)
	horizontalImages.append(getImage(save=SAVE,fname='mask1-left'))
	# Move mask to -ve (left) edge and take an image.
	epics.caput('SR08ID01SST25:MASK.TWV',20,wait=True)
	epics.caput('SR08ID01SST25:MASK.TWR',1,wait=True)
	horizontalImages.append(getImage(save=SAVE,fname='mask1-right'))
	# Put back to horizontal centre.
	epics.caput('SR08ID01SST25:MASK_POS:{}.VAL'.format(i),1,wait=True)
	# Get top edge.
	epics.caput('SR08ID01SST25:Z.VAL',10,wait=True)
	verticalImages.append(getImage(save=SAVE,fname='mask1-top'))
	# Get bottom edge.
	epics.caput('SR08ID01SST25:Z.VAL',-10,wait=True)
	verticalImages.append(getImage(save=SAVE,fname='mask1-bottom'))
	# Put back to veritcal centre.
	epics.caput('SR08ID01SST25:Z.VAL',0,wait=True)

	# Calculate centre.
	logging.info("Calculating centre point...")
	# Take line profile of each image.
	horizontalLines = []
	verticalLines = []

	logging.critical("Finding the edges of the mask will need to be developed. Haven't worked that out yet.")
	for i in range(len(horizontalImages)):
		horizontalImages[i] = gaussian_filter(horizontalImages[i],sigma=10)
		temp = horizontalImages[i][_row,:].astype(float)
		horizontalLines.append(np.absolute(temp-temp.max()))
	for i in range(len(verticalImages)):
		horizontalImages[i] = gaussian_filter(horizontalImages[i],sigma=10)
		temp = horizontalImages[i][_row,:].astype(float)
		verticalLines.append(np.absolute(temp-temp.max()))

	# Find the change.
	for i in range(len(horizontalLines)):
		# Horizontal lines
		peak = np.argmax(horizontalLines[i])
		peaks.append(peak)
		# Vertical lines
		peak = np.argmax(verticalLines[i])
		peaks.append(peak)

	# Calculate relative movements.
	d_h = np.absolute(peaks[1]-peaks[3])*pixelSize/2
	d_v.append(np.absolute(peaks[0]-peaks[2])*pixelSize/2)

	# Apply horizontal adjustment and save to mask position.
	logging.info("Adjusting horizontal centre point...")
	current = epics.caget('SR08ID01SST25:MASK_POS:1.VAL')
	epics.caput('SR08ID01SST25:MASK_POS:1.VAL',current+d_h,wait=True)

# Apply vertical adjustment (to table).
logging.info("Adjusting vertical centre point (set by the average of all three mask positions)...")
current = epics.caget('SR08ID01SST25:TABLE_Z.VAL')
epics.caput('SR08ID01SST25:TABLE_Z.VAL',current+np.average(d_v),wait=True)

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

# Finished, close the shutter.
closeShutter()

# Set rotation back to home.
logging.info("Moving back to Mask 1 position.")
epics.caput('SR08ID01SST25:MASK_POS:{}.VAL'.format(i),1,wait=True)

logging.info("Finished! Wasn't that easy?")
