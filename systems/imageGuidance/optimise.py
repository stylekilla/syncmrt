import numpy as np
from scipy import ndimage

def optimiseFiducials(pts,data,extent,markersize,threshold):
	'''
	Optimise fiducials will take an ROI around a point and re-center it based on the pixel values.
	- Requires points in mm (x-horizontal then y-vertical)
	- requires dims in mm (rows,cols)
	- requires markerSize in mm
	- requires pixel data array
	- gives out points in mm
	- input should be [row,col]; we have made exceptions to align x/y and row/col in here
	'''

	# Calculate pixel size in x-y (hor-vert)
	pixelSize = np.absolute(np.array([
		(extent[1]-extent[0])/data.shape[1],
		(extent[3]-extent[2])/data.shape[0]
			]))

	# Calculate input points topLeft (x-y) (to help return them to a zero based indexing system)
	topLeft = np.array([extent[0],extent[3]])

	# Create empty array for optimised points.
	pts_ctrds = np.zeros((np.shape(pts)))

	# Turn point measurements (mm) into integers for indexing.
	pts = np.absolute(topLeft-pts)/pixelSize

	# Set regions of interest in both x and y.
	x_roi = int(markersize*3/pixelSize[0])
	y_roi = int(markersize*3/pixelSize[1])

	'''TESTING: saving ims for inspection in imageJ'''
	from skimage.external import tifffile as tif
	import datetime
	time = datetime.datetime.now().time()
	name = "dump/"+str(time.second)+str(time.microsecond)+"entireImage.tif"
	tif.imsave(name,data)

	# Iterate over number of points.
	for i in range(np.shape(pts)[0]):
		# Select the coordinate in the array and sample the value.
		x = int(pts[i,0])
		y = int(pts[i,1])
		clr = data[y,x]

		# Create ROI to look at.
		roi = data[(y-y_roi):(y+y_roi),(x-x_roi):(x+x_roi)]

		'''TESTING: saving ims for inspection in imageJ'''
		from skimage.external import tifffile as tif
		import datetime
		time = datetime.datetime.now().time()
		name = "dump/"+str(time.second)+str(time.microsecond)+"roiColor%i.tif"%i
		tif.imsave(name,roi)

		# Find ROI corner as y-x (vert-hor). This enables us to put our new values in the context of the larger array later.
		roi_cnr = np.array([y-y_roi,x-x_roi])

		# Define thresholds of +/- X% of that value.
		thresh_max = clr+np.absolute(clr*(threshold/100))
		thresh_min = clr-np.absolute(clr*(threshold/100))

		# Mask the image.
		roi[(roi<thresh_min)] = 0
		roi[(roi>thresh_max)] = 0
		# Set remaining values to binary 1.
		roi[(roi>0)] = 1

		'''TESTING: saving ims for inspection in imageJ'''
		from skimage.external import tifffile as tif
		import datetime
		time = datetime.datetime.now().time()
		name = "dump/"+str(time.second)+str(time.microsecond)+"roiBW%i.tif"%i
		tif.imsave(name,roi)

		# Find connection maps of each element.
		labels, index = ndimage.label(roi)

		# Create empty array size of indexes.
		labels_com = np.zeros((index,2))

		# Get center of mass for each element.
		for j in range(index):
			labels_com[j,:] = ndimage.measurements.center_of_mass(roi,labels,j+1)

		# Add corner of roi back to set within larger array. (still in y-x (vert-hor))
		labels_com += roi_cnr

		# Swap back to x-y so it can interact with pts.
		labels_com = np.fliplr(labels_com)

		# Find the CoM that most accurately represents a datapoint.
		# Test points.
		test = np.absolute(labels_com-pts[i,:])
		dist = np.zeros((index,1))

		# Find the length of each set of points.
		for j in range(index):
			dist[j,0] = np.sqrt(test[j,0]**2 + test[j,1]**2)

		# Find the smallest line.
		ind = np.argmin(dist)

		# Write the new value (in x-y).
		pts_ctrds[i,:] = labels_com[ind,:]

	# Return pts_ctrds to measurement values (mm).
	pts_ctrds *= pixelSize
	pts_ctrds[:,0] = topLeft[0] + pts_ctrds[:,0]
	pts_ctrds[:,1] = topLeft[1] - pts_ctrds[:,1]

	# Return centroid refined points as np array.
	return pts_ctrds