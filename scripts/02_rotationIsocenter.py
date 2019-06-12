import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import find_peaks
import epics
import time

def getImage():
	arr = epics.caget('SR08ID01DET01:IMAGE:ArrayData')
	_x = epics.caget('SR08ID01DET01:IMAGE:ArraySize1_RBV')
	_y = epics.caget('SR08ID01DET01:IMAGE:ArraySize0_RBV')
	time.sleep(0.1)
	return np.flipud(np.array(arr,dtype=np.uint16).reshape(_x,_y))[1008:1123,695:1909]

def closeShutter():
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)

def openShutter():
	epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD", 1, wait=True)
	time.sleep(2)

# Set home.
epics.caput('SR08ID01SST25:SAMPLEH1.VAL',0,wait=True)
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',0,wait=True)
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)

########################
# START RUBY ACQUISITION
########################
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',0,wait=True)
epics.caput('SR08ID01DET01:CAM:AcquireTime.VAL',0.02)
epics.caput('SR08ID01DET01:CAM:AcquirePeriod.VAL',0.00)
# epics.caput('SR08ID01DET01:CAM:ImageMode.VAL',0.07,wait=True)
epics.caput('SR08ID01DET01:CAM:Acquire.VAL',1)


######################
# CALCULATE PIXEL SIZE
######################

# Distance to travel in mm.
_distance = 5

# Get darkfield.
dark = getImage()
# Get flood field.
epics.caput('SR08ID01SST25:SAMPLEV.TWV',_distance,wait=True)
epics.caput('SR08ID01SST25:SAMPLEV.TWR',1,wait=True)
openShutter()
flood = getImage() - dark
epics.caput('SR08ID01SST25:SAMPLEV.TWF',1,wait=True)

image = []
# Get first image.
image.append((getImage()-dark)/flood)
# Move to 1 mm.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',5,wait=True)
# Get second image.
image.append((getImage()-dark)/flood)
# Put H2 back.
epics.caput('SR08ID01SST25:SAMPLEH2.VAL',0,wait=True)

# The row in the image to take.
_line = 75
_width = 30

# Take line profile of each.
line = []
for i in range(len(image)):
	temp = image[i][_line,:].astype(float)
	line.append(np.absolute(temp-temp.max()))

# Find the peaks.
peaks = []
for i in range(len(line)):
	_peaks, _ = find_peaks(line[i],width=_width)
	peaks.append(_peaks)

pixelSize = _distance/np.absolute(peaks[1]-peaks[0])[0]
print("Pixel Size: {} mm".format(pixelSize))

# fig,ax = plt.subplots(2,2)
# ax = ax.flatten()
# ax[0].plot(np.linspace(0,len(line[0]),len(line[0])),line[0])
# ax[1].plot(np.linspace(0,len(line[0]),len(line[0])),line[1])
# ax[2].imshow(image[0],cmap='gray')
# ax[3].imshow(image[1],cmap='gray')
# plt.show()

###############
# CALCULATE COR
###############
_width = 75

image = []
# Rotate to -180.
epics.caput('SR08ID01SST25:ROTATION.VAL',-180,wait=True)
image.append(getImage())
# Rotate to -90.
epics.caput('SR08ID01SST25:ROTATION.VAL',-90,wait=True)
image.append(getImage())
# Rotate to 0.
epics.caput('SR08ID01SST25:ROTATION.VAL',0,wait=True)
image.append(getImage())
# Rotate to 90
epics.caput('SR08ID01SST25:ROTATION.VAL',90,wait=True)
image.append(getImage())

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
# ax[0].plot(np.linspace(0,len(line[0]),len(line[0])),line[0])
# ax[0].scatter(line[0][peaks[0]],marker='+',color='r')
# ax[1].plot(np.linspace(0,len(line[0]),len(line[0])),line[1])
# ax[1].scatter(line[1][peaks[1]],marker='+',color='r')
# ax[2].plot(np.linspace(0,len(line[0]),len(line[0])),line[2])
# ax[2].scatter(line[2][peaks[2]],marker='+',color='r')
# ax[3].plot(np.linspace(0,len(line[0]),len(line[0])),line[3])
# ax[3].scatter(line[3][peaks[3]],marker='+',color='r')
# ax[4].imshow(image[0],cmap='gray')
# ax[5].imshow(image[1],cmap='gray')
# ax[6].imshow(image[2],cmap='gray')
# ax[7].imshow(image[3],cmap='gray')
# plt.show()

# Move H1.
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

# Take final image of iso.
finalImage = getImage()
closeShutter()

# Take line profile of each.
temp = finalImage[_line,:].astype(float)
line = np.absolute(temp-temp.max())

# Find the peaks.
_peaks, _ = find_peaks(line,width=_width)
pos = np.array(finalImage.shape)/2
pos[1] = _peaks[0]
print("Image isocenter: ",pos)


# fig,ax = plt.subplots(1,2)
# ax = ax.flatten()
# ax[0].imshow(finalImage)
# ax[0].hlines(_line)
# ax[0].scatter(pos[1],pos[0],marker='+',color='r')
# plt.show()