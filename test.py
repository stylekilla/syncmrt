import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import ConnectionPatch
import imageio
import pydicom as dicom
import logging
import os

# Logging.
logging.basicConfig(format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Pretty Numpy Printing.
np.set_printoptions(precision=3,suppress=True)
import testGpu

"""
RAT ANATOMY.
"""
# folder = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/CT'

# # Read the dicom files.
# dataset = []
# for root, subdir, fp in os.walk(folder):
# 	for fn in fp:
# 		if fn.endswith(tuple('.dcm')):
# 			dataset.append(os.path.join(root,fn))
# # Reference file.
# ref = dicom.dcmread(dataset[0])
# # Get the 3D CT array shape.
# shape = np.array([int(ref.Rows), int(ref.Columns), len(dataset)])
# # Create an empty python array to dump the CT data into.
# pixelArray = np.zeros(shape)
# # Order the dataset in Z slices.
# order = []
# for fn in dataset:
# 	order.append(float(dicom.dcmread(fn).ImagePositionPatient[2]))
# order = np.argsort(np.array(order))
# # Read array in one slice at a time.
# for index,fn in enumerate(np.array(dataset)[order]):
# 	ctSlice = dicom.dcmread(fn)
# 	pixelArray[:,:,index] = ctSlice.pixel_array
# # Rescale the Hounsfield Units.
# pixelArray = (pixelArray*ref.RescaleSlope) + ref.RescaleIntercept
# # Find front on view of the dataset.
# image1 = np.rot90(np.sum(pixelArray,axis=0))[:,150:350]

# # Test file.
fn1 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_01-1.jpg'
# image2 = imageio.imread(fn,as_gray=True)[125:400,500:650]

fn2 = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2_02-1.jpg'
# image2 = imageio.imread(fn2,as_gray=True)[:,300:800]
# image2 = imageio.imread(fn2,as_gray=True)


# fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/hand1.jpg'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/hand2.jpg'
# fn1 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test3.png'
# fn2 = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test3.png'
image1 = imageio.imread(fn1,as_gray=True)
image2 = imageio.imread(fn2,as_gray=True)

# Start the gpu.
gpu = testGpu.gpu()

# descriptors1 = gpu.findFeaturesSIFT(image1,plot=True)
# exit()

""" 
CREATE TEST IMAGES. 
"""
# image1 = np.zeros((500,500))
# poi = np.random.randint(0,499,(500,2))
# poi = poi[np.argsort(poi[:,1])]
# # image1[poi] = np.random.rand(500) * np.linspace(0,254,500)
# image1[poi[:,0],poi[:,1]] = np.linspace(0,254,500)
# from scipy.ndimage import gaussian_filter
# image1 = gaussian_filter(image1, sigma=3)

# image2 = np.zeros((500,500))
# poi = np.array([50,100,150,200,250,300,350,400,450])
# height = np.arange(4,40,4)
# for p,h in zip(poi,height):
# 	image2[200-h:200+h,p-5:p+5] = 255
# 	image2[280:320,p-5:p+5] = p
# image2 = gaussian_filter(image2, sigma=3)

# imageio.imsave(fn1,image1)
# imageio.imsave(fn2,image2)
# exit()

"""
GPU START 
"""
# Find the features of the image.
image1, descriptors1 = gpu.findFeaturesSIFT(image1,sigma=1.6,contrast=3,curvature=10,upsample=False,plot=False)
image2, descriptors2 = gpu.findFeaturesSIFT(image2,sigma=1.6,contrast=3,curvature=10,upsample=False,plot=False)

print("Keypoints: {} - {}".format(len(descriptors1),len(descriptors2)))

"""
MATCHING ALGORITHM
Best way to do this:
Object (or the points we want to find) must come from an ROI in some image... These are the first set of descriptors.
The second set of descriptors is the database we want to match against.
"""

matches = []
# for index, key in enumerate(descriptors1):
# 	# Calculate the euclidian distance between the keypoint descriptor and the descriptor database.
# 	ed = np.linalg.norm(descriptors2[:,4:]-key[4:],axis=1)
# 	# Find two closest points.
# 	d1,d2 = np.argpartition(ed,1)[:2]
# 	# Reject if distance ratio between two closest points is too large.
# 	if ed[d1]/ed[d2] < 0.8:
# 		# Good match, save it.
# 		matches.append([index,d1])
# 	matches.append([index,d1])

# Matches are indices of keypoints.
matches = np.array(matches)
print("Database Matches: {}".format(len(matches)))
# Grab the actual keypoint values.
if len(matches) > 0:
	kpMatches = np.hstack([descriptors1[matches[:,0]][:,:4],descriptors2[matches[:,1]][:,:4]])

# Show the matches.
fig,ax=plt.subplots(1,2)
ax = ax.ravel()
ax[0].imshow(image1,cmap='Greys')
ax[1].imshow(image2,cmap='Greys')
if len(descriptors1) > 0: ax[0].scatter(descriptors1[:,1]*descriptors1[:,2],descriptors1[:,0]*descriptors1[:,2],ec='k',fc='none',marker='o')
if len(descriptors2) > 0: ax[1].scatter(descriptors2[:,1]*descriptors2[:,2],descriptors2[:,0]*descriptors2[:,2],ec='k',fc='none',marker='o')

for kp in descriptors1:
	x = kp[1]*kp[2]
	y = kp[0]*kp[2]
	dx = 10*np.cos(kp[3])
	dy = 10*np.sin(kp[3])
	ax[0].arrow(x,y,dx,dy)
for kp in descriptors2:
	x = kp[1]*kp[2]
	y = kp[0]*kp[2]
	dx = 10*np.cos(kp[3])
	dy = 10*np.sin(kp[3])
	ax[1].arrow(x,y,dx,dy)

COLORS=['r','g','b','k','w','y']
from itertools import cycle
clr = cycle(COLORS)
if len(matches) > 0:
	# for i in range(0,len(kpMatches),int(len(kpMatches)/25)):
	for i in range(0,len(kpMatches)):
		con = ConnectionPatch(
			xyA=kpMatches[i,4:6][::-1]*kpMatches[i,6],
			xyB=kpMatches[i,0:2][::-1]*kpMatches[i,2],
			coordsA="data", coordsB="data",axesA=ax[1], axesB=ax[0], color=next(clr)
		)
		ax[1].add_artist(con)

plt.show()