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
# fn1 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_01-1.jpg'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_02-1.jpg'

# image1 = imageio.imread(fn1,as_gray=True)[125:400,500:650]
# image2 = imageio.imread(fn2,as_gray=True)[:,300:800]

fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test3.png'
fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test2.jpg'

image1 = imageio.imread(fn1,as_gray=True)
image2 = imageio.imread(fn2,as_gray=True)


""" CREATE TEST IMAGES. """
# image1 = np.zeros((500,500))
# poi = np.random.randint(0,499,(500,2))
# poi = poi[np.argsort(poi[:,1])]
# # image1[poi] = np.random.rand(500) * np.linspace(0,254,500)
# image1[poi[:,0],poi[:,1]] = np.linspace(0,254,500)
# from scipy.ndimage import gaussian_filter
# image1 = gaussian_filter(image1, sigma=3)

# image2 = np.zeros((500,500))
# poi = np.array([50,100,150,200,250,300,350,400,450])
# for p in poi:
# 	image2[180:220,p-5:p+5] = 255
# 	image2[280:320,p-5:p+5] = p
# image2 = gaussian_filter(image2, sigma=3)

# imageio.imsave(fn1,image1)
# imageio.imsave(fn2,image2)
# exit()

""" IMPORT CT DATASET """
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

""" GPU START """
# Start the gpu.
gpu = testGpu.gpu()
# Find the features of the image.
descriptors1 = gpu.findFeaturesSIFT(image1)
descriptors2 = gpu.findFeaturesSIFT(image2)

# print("Keypoints: {} - {}".format(len(descriptors1),len(descriptors2)))

"""
MATCHING ALGORITHM
Best way to do this:
Object (or the points we want to find) must come from an ROI in some image... These are the first set of descriptors.
The second set of descriptors is the database we want to match against.
"""

# matches = []
# for index, key in enumerate(descriptors1):
# 	# Calculate the euclidian distance between the keypoint descriptor and the descriptor database.
# 	ed = np.linalg.norm(descriptors2[:,4:]-key[4:],axis=1)
# 	# Find two closest points.
# 	d1,d2 = np.argpartition(ed,1)[:2]
# 	# Reject if distance ratio between two closest points is too large.
# 	if ed[d1]/ed[d2] < 0.8:
# 		# Good match, save it.
# 		matches.append([index,d1])

# # Matches are indices of keypoints.
# matches = np.array(matches)
# kpMatches = np.hstack([descriptors1[matches[:,0]][:,:4],descriptors2[matches[:,1]][:,:4]])

# print("Database Matches: {}".format(len(matches)))


# Show the matches.
fig,ax=plt.subplots(1,2)
ax = ax.ravel()
ax[0].imshow(image1)
ax[1].imshow(image2)
ax[0].scatter(descriptors1[:,1],descriptors1[:,0],ec='k',fc='none',marker='o')
ax[1].scatter(descriptors2[:,1],descriptors2[:,0],ec='k',fc='none',marker='o')

# for i in range(len(descriptors1)):
	# ax[0].arrow(descriptors1[i,1],descriptors1[i,0], 10*descriptors1[i,2]*np.cos(descriptors1[i,3]),10*descriptors1[i,2]*np.sin(descriptors1[i,3]), head_width=3, head_length=4, fc='k', ec='k')
	# ax[1].arrow(descriptors2[i,1],descriptors2[i,0], 10*descriptors2[i,2]*np.cos(descriptors2[i,3]),10*descriptors2[i,2]*np.sin(descriptors2[i,3]), head_width=3, head_length=4, fc='k', ec='k')

# for i in range(0,len(kpMatches),int(len(kpMatches)/25)):
# for i in range(0,len(kpMatches)):
# 	con = ConnectionPatch(xyA=kpMatches[i,4:6][::-1], xyB=kpMatches[i,0:2][::-1], coordsA="data", coordsB="data",axesA=ax[1], axesB=ax[0], color="red")
# 	ax[1].add_artist(con)

plt.show()