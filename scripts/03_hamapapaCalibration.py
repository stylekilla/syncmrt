import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import find_peaks
import epics
import time

def getImage():
	arr = epics.caget('SR08ID01DET04:IMAGE:ArrayData')
	_x = epics.caget('SR08ID01DET04:IMAGE:ArraySize1_RBV')
	_y = epics.caget('SR08ID01DET04:IMAGE:ArraySize0_RBV')
	time.sleep(0.1)
	return (np.array(arr).reshape(_x,_y))

image = getImage()

from skimage.external import tifffile as tif

tif.imsave('./LOOKATME.tif',image.astype('float32'))