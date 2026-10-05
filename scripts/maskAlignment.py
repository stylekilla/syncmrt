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
SAVE = True
DET_PV = "SR08ID01DET01"
# This is the left bottom top right of the field in RUBY in pixels.
l = 0
r = epics.caget('{}:ROI1:IMAGE:ArraySize0_RBV'.format(DET_PV))
b = epics.caget('{}:ROI1:IMAGE:ArraySize1_RBV'.format(DET_PV))
t = 0
# Pixel size (in mm) as calculated from COR script.
pixelSize = 0.012244897959183673


#######################
# INTERNAL CALCULATIONS
#######################
# The row in the image to take.
_col = int((r-l)/2)
_row = int((b-t)/2)

def getImage(save=False,fname=''):
	logging.info("Acquiring an image.")
	epics.caput(f'{DET_PV}:CAM:Acquire.VAL',1,wait=True)
	arr = epics.caget(f'{DET_PV}:ROI1:IMAGE:ArrayData')
	_x = epics.caget(f'{DET_PV}:ROI1:IMAGE:ArraySize1_RBV')
	_y = epics.caget(f'{DET_PV}:ROI1:IMAGE:ArraySize0_RBV')
	time.sleep(0.1)
	arr = np.flipud(np.array(arr,dtype=np.uint16).reshape(_x,_y))[t:b,l:r]
	# Remove any weird values.
	arr = np.nan_to_num(arr)
	arr = median_filter(arr,size=(2,2))
	if save:
		imageio.imsave('~/work/syncmrt/scripts/cache/{}.tif'.format(fname),arr)
	return arr

def closeShutter():
	#logging.info("Closing 1A shutter.")
	#epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)
	#time.sleep(2)
	logging.info("Closing in air pink shutter.")
	epics.caput("SR08ID01ZEB02:SOFT_IN:B0", 0, wait=False)
	time.sleep(0.2)
	epics.caput("SR08ID01ZEB02:SOFT_IN:B1", 1, wait=False)

def openShutter():
	#logging.info("Opening 1A shutter.")
	#epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD", 1, wait=True)
	#time.sleep(2)
	logging.info("Opening in air pink shutter.")
	epics.caput("SR08ID01ZEB02:SOFT_IN:B1", 0, wait=False)
	time.sleep(0.2)
	epics.caput("SR08ID01ZEB02:SOFT_IN:B0", 1, wait=False)


###################################
# START RUBY ACQUISITION PARAMETERS
###################################
exposureTime = 0.01
logging.info("Setting up RUBY acquisition parameters.")
epics.caput(f'{DET_PV}:CAM:Acquire.VAL',0,wait=True)
epics.caput(f'{DET_PV}:CAM:AcquireTime.VAL',exposureTime)
epics.caput(f'{DET_PV}:CAM:AcquirePeriod.VAL',0.00)
epics.caput(f'{DET_PV}:CAM:ImageMode.VAL','Single',wait=True)
epics.caput(f'{DET_PV}:TIFF:AutoSave.VAL','No',wait=True)
epics.caput(f'{DET_PV}:CAM:Acquire.VAL',1,wait=True)

##########################
# GET BALLBEARING POSITION => MIGHT NOT BE NEEDED...???
##########################



##########################
# CALCULATE MASK POSITIONS
##########################
d_v = []
peaks = []
masksize_h = [20.0, 10.0, 5.0]
masksize_v = [20.0, 10.0, 5.0]

# Iterate over all three masks.
for j in range(2):
	i=j+1
	# First mask.
	logging.info("Selecting mask {}.".format(i))
	horizontalImages = []
	verticalImages = []
	# Move to first mask.
	logging.critical("Selecting a mask position is probably wrong. Not sure how epics does that. Check me. In fact, check ALL PV's!")
	epics.caput('SR08ID01SST25:MASK_POS:select',i,wait=True)
	# Open the shutter.
	openShutter()
	logging.info("Acquiring images...")
	horizontalImages.append(getImage(save=SAVE,fname=f'mask{i}-orig'))
	# Move mask to +ve (right) edge and take an image.
	epics.caput('SR08ID01SST25:MASK.TWV',masksize_h[j]/2,wait=True)
	epics.caput('SR08ID01SST25:MASK.TWF',1,wait=True)
	horizontalImages.append(getImage(save=SAVE,fname=f'mask{i}-left'))
	# Move mask to -ve (left) edge and take an image.
	epics.caput('SR08ID01SST25:MASK.TWV',masksize_h[j],wait=True)
	epics.caput('SR08ID01SST25:MASK.TWR',1,wait=True)
	horizontalImages.append(getImage(save=SAVE,fname=f'mask{i}-right'))
	# Put back to horizontal centre.
	epics.caput('SR08ID01SST25:MASK_POS:select',i,wait=True)
	# Get top edge.
	epics.caput('SR08ID01SST25:Z.VAL',masksize_v[j]/2,wait=True)
	verticalImages.append(getImage(save=SAVE,fname=f'mask{i}-bottom'))
	# Get bottom edge.
	epics.caput('SR08ID01SST25:Z.VAL',-masksize_v[j]/2,wait=True)
	verticalImages.append(getImage(save=SAVE,fname=f'mask{i}-top'))
	# Put back to veritcal centre.
	epics.caput('SR08ID01SST25:Z.VAL',0,wait=True)
	# Close the shutter.
	closeShutter()
	# Calculate centre.
	logging.info("Calculating centre point...")
	# Take line profile of each image.
	horizontalLines = []
	verticalLines = []

	logging.critical("Finding the edges of the mask will need to be developed. Haven't worked that out yet.")

	for i in range(len(horizontalImages)):
		horizontalImages[j] = gaussian_filter(horizontalImages[j],sigma=10)
		temp = horizontalImages[j][_row,:].astype(float)
		horizontalLines.append(np.absolute(temp-temp.max()))

	for i in range(len(verticalImages)):
		verticalImages[j] = gaussian_filter(verticalImages[j],sigma=10)
		temp = verticalImages[j][:,_col].astype(float)
		verticalLines.append(np.absolute(temp-temp.max()))

	# Find the change.
	for i in range(len(horizontalLines)):
		# Horizontal lines
		peak = np.argmax(horizontalLines[j])
		peaks.append(peak)
		# Vertical lines
		peak = np.argmax(verticalLines[j])
		peaks.append(peak)

	# Calculate relative movements.
	d_h = np.absolute(peaks[1]-peaks[3])*pixelSize/2
	d_v.append(np.absolute(peaks[0]-peaks[2])*pixelSize/2)

	# Apply horizontal adjustment and save to mask position.
	logging.info(f"Adjusting horizontal centre point... by {d_h}")
	current = epics.caget('SR08ID01SST25:MASK_POS:pos{}.VAL'.format(j))
	#####epics.caput('SR08ID01SST25:MASK_POS:pos{}}.VAL'.format(i),current+d_h,wait=True)

# Apply vertical adjustment (to table).
logging.info(f"Adjusting vertical centre point (set by the average of all three mask positions)... by {np.average(d_v)}")
current = epics.caget('SR08ID01SST25:Z.VAL')
######epics.caput('SR08ID01SST25:Z.VAL',current+np.average(d_v),wait=True)

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
epics.caput('SR08ID01SST25:MASK_POS:select',1,wait=True)

logging.info("Finished! Wasn't that easy?")
