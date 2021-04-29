import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import find_peaks
import epics
import time

"""
Assumes:
	- HamaPapa connected and IOC running
	- Single non save image acquisition at 0.5s
	- 
"""

DET_PV = "SR08ID01DETIOC08"

def getImage():
	arr = epics.caget('{}:IMAGE:ArrayData'.format(DET_PV))
	_x = epics.caget('{}:IMAGE:ArraySize1_RBV'.format(DET_PV))
	_y = epics.caget('{}:IMAGE:ArraySize0_RBV'.format(DET_PV))
	time.sleep(0.1)
	return np.flipud(np.fliplr(np.array(arr).reshape(_x,_y)))

image = getImage()

import imageio

imageio.imsave('./DetectorCalib.tif',image.astype('float32'))