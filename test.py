import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import ConnectionPatch
import imageio
import pydicom as dicom
import logging
import os

# Logging.
logging.basicConfig(format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",level=logging.INFO)
# Pretty Numpy Printing.
np.set_printoptions(precision=3,suppress=True)

import testGpu
# import testPlot

# Test file.
fn1 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_01-1.jpg'
fn2 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_02-1.jpg'
image1 = imageio.imread(fn1,as_gray=True)
image2 = imageio.imread(fn2,as_gray=True)
# fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/image1.jpg'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/image2.jpg'
# Read the image.

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
descriptors1 = gpu.findFeaturesSIFT(image1) # [100:400,500:650]
descriptors2 = gpu.findFeaturesSIFT(image2) # [100:400,500:650]

print("{} - {}".format(len(descriptors1),len(descriptors2)))

# matches = []
# for key in descriptors1:
# 	# Calculate distance between the keypoint and the descriptor database.
# 	distance = np.linalg.norm(descriptors2[:,2:]-key[2:],axis=1)
# 	# Find two closest points.
# 	d1,d2 = np.argpartition(distance,1)[:2]
# 	# Reject if distance ratio is too large.
# 	if distance[d1]/distance[d2] > 0.8:
# 		# No good match found.
# 		continue
# 	else:
# 		# Good match, save it.
# 		matches.append([key,descriptors2[d1]])

# matches = np.array(matches)


# print(matches[:,0,:2])
# print(matches[:,1][:2])




fig,ax=plt.subplots(1,2)
ax = ax.ravel()
ax[0].imshow(image1)
ax[1].imshow(image2)
# ax[0].scatter(matches[:,0,1],matches[:,0,0],c='k',marker='o')
# ax[1].scatter(matches[:,1,1],matches[:,1,0],c='k',marker='o')
ax[0].scatter(descriptors1[:,1],descriptors1[:,0],c='k',marker='o')
ax[1].scatter(descriptors2[:,1],descriptors2[:,0],c='k',marker='o')


# for i in range(0,len(matches),int(len(matches)/25)):
	# con = ConnectionPatch(xyA=[matches[i,1,1],matches[i,1,0]], xyB=[matches[i,0,1],matches[i,0,0]], coordsA="data", coordsB="data",axesA=ax[1], axesB=ax[0], color="red")
	# ax[1].add_artist(con)

plt.show()