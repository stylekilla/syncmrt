import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import ConnectionPatch
import imageio
import pydicom as dicom
import cv2 as cv
import logging
import os

import testGpu

# Logging.
logging.basicConfig(format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",level=logging.INFO)
# Pretty Numpy Printing.
np.set_printoptions(precision=3,suppress=True)


# Test file.
# fn1 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_01-1.jpg'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_02-1.jpg'

# fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/image1.jpg'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/image2.jpg'

fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test1.jpg'
fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test2.jpg'

image1 = cv.imread(fn1,cv.IMREAD_GRAYSCALE)
image2 = cv.imread(fn2,cv.IMREAD_GRAYSCALE)

# image1 = image1[125:400,500:650]
# image2 = image2[:,300:800]

sift = cv.SIFT_create()

# Find the features of the image.
kp1,descriptors1 = sift.detectAndCompute(image1,None) # [100:400,500:650]
kp2,descriptors2 = sift.detectAndCompute(image2,None) # [100:400,500:650]

print("Keypoints: {} - {}".format(len(descriptors1),len(descriptors2)))

# create BFMatcher object
# bf = cv.BFMatcher()
# # Match descriptors.
# matches = bf.knnMatch(descriptors1,descriptors2,k=2)
# # Apply ratio test
# good = []
# for m,n in matches:
# 	if m.distance < 0.8*n.distance:
# 		good.append([m])
# print("Matches: {}".format(len(good)))

fig,ax = plt.subplots(1,2)
# Draw first 10 matches.
# matchImage = cv.drawMatchesKnn(image1,kp1,image2,kp2,good,None,flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
matchImage1 = cv.drawKeypoints(image1,kp1,image1,flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
matchImage2 = cv.drawKeypoints(image2,kp2,image2,flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
ax[0].imshow(matchImage1)
ax[1].imshow(matchImage2)
plt.show()


"""
Best way to do this:
Object (or the points we want to find) must come from an ROI in some image... These are the first set of descriptors.
The second set of descriptors is the database we want to match against.
"""

# matches = []
# for index, key in enumerate(descriptors1):
# 	# Calculate distance between the keypoint descriptor and the descriptor database.
# 	distance = np.linalg.norm(descriptors2[:,4:]-key[4:],axis=1)
# 	# Find two closest points.
# 	d1,d2 = np.argpartition(distance,1)[:2]
# 	# Reject if distance ratio between two closest points is too large.
# 	if distance[d1]/distance[d2] > 0.8:
# 		# No good match found.
# 		continue
# 	else:
# 		# Good match, save it.
# 		matches.append([index,d1])

# # Matches are indices of keypoints.
# matches = np.array(matches)

# print("Database Matches: {}".format(len(matches)))

# kpMatches = np.hstack([descriptors1[matches[:,0]][:,:4],descriptors2[matches[:,1]][:,:4]])

