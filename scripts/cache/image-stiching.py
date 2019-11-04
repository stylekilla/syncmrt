from skimage.external import tifffile as tif
import glob
import numpy as np
import scipy.ndimage as ndimage

path = '/Users/micahbarnes/Desktop/rando2-xr90/'
fn = glob.glob(path+'image*.tif')
image = []

roiy = 405

flatfield = tif.imread(fn[0])[:roiy,:]
del fn[0]

for i in range(len(fn)):
	data = tif.imread(fn[i])[:roiy,:]
	data = data/flatfield
	image.append(data)

yshift = 225

newrows = roiy+len(fn)*yshift

rows = np.shape(image[0])[0]
cols = np.shape(image[0])[1]
array = np.zeros((newrows,cols))

array[0:roiy,:] = image[0]

for i in range(1,len(fn)):
	l = yshift*i
	u = l + roiy
	# array[l:u,:] = image[i]
	array[l:u,:] = np.fliplr(np.flipud(image[i]))

# array = np.flipud(array)

array = array*10000

np.save(path+'stitched.npy',array.astype('float32'))