import numpy as np
from matplotlib import pyplot as plt
import imageio
import pydicom as dicom
import os

# Pretty Numpy Printing.
np.set_printoptions(precision=3,suppress=True)

import testGpu
# import testPlot

# Test file.
fn = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_01-1.jpg'
# Read the image.
image = imageio.imread(fn)

# image = image[:70,:70]

# Test CT dataset.
# folder = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/CT'
# dicomFiles = []
# for root,dirs,files in os.walk(folder):
	# for file in files:
		# if file.endswith('.dcm'):
			# dicomFiles.append(os.path.join(root,file))
# Load the CT file.
# import file
# ct = file.importer.ct(dicomFiles)

# Start the gpu.
gpu = testGpu.gpu()
# Find the features of the image.
gpu.findFeaturesSIFT(image)
print("COMPLETE!")

"""
# Read a sub portion of the image.
# HEAD...
# image = image[130:260,480:680]

# DIFFERENCE OF GAUSSIAN
# http://fourier.eng.hmc.edu/e161/lectures/gradient/node9.html
# The bigger the difference in sigma, the fatter the regions it finds.
from scipy.ndimage import gaussian_filter
image_g1 = gaussian_filter(image, sigma=1)
image_g2 = gaussian_filter(image, sigma=2)
dog = image_g1-image_g2

# Find local minima and maxima (in 2D).
# Take the 8 neighbours of a pixel and check whether that pixel is the lowest or highest value.
minima = []
maxima = []
# Scan rows.
for i in range(1,image.shape[0]-1):
	# Scan columns.
	for j in range(1,image.shape[1]-1):
		# Grab the centre pixel and the 8 surrounding pixels.
		i0 = image[i  , j  ]
		i1 = image[i-1, j-1]
		i2 = image[i-1, j  ]
		i3 = image[i-1, j+1]
		i4 = image[i  , j-1]
		i5 = image[i  , j+1]
		i6 = image[i+1, j-1]
		i7 = image[i+1, j  ]
		i8 = image[i+1, j+1]
		# If it is less than all the values, it is a local minima.
		if all(i0 < [i1,i2,i3,i4,i5,i6,i7,i8]):
			minima.append([i,j])
		# If it is less than all the values, it is a local minima.
		elif all(i0 > [i1,i2,i3,i4,i5,i6,i7,i8]):
			maxima.append([i,j])
# Numpy arrays for ease of use.
minima = np.array(minima)
maxima = np.array(maxima)

# Plotting.
fig = plt.figure()
ax1 = fig.add_subplot(2,2,1)
ax2 = fig.add_subplot(2,2,2)
ax3 = fig.add_subplot(2,2,3)
ax4 = fig.add_subplot(2,2,4)
# Images.
ax1.imshow(image)
ax2.imshow(dog)
ax3.imshow(image_g1)
ax4.imshow(image_g2)
# Local minima and maxima.
ax2.scatter(minima[:,1],minima[:,0],c='g')
ax2.scatter(maxima[:,1],maxima[:,0],c='r')
# Show plot.
plt.show()
"""