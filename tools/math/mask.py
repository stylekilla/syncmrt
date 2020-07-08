import numpy as np

import h5py as h
import numpy as np
import matplotlib as mpl
mpl.use('Qt5Agg')

"""
	USEFUL METHODS.
"""

def toPoint(point):
	point = np.array(point)
	point[1] *= -1
	return point-250

def toIndex(point):
	point = np.array(point)
	point[1] *= -1
	return point+250

"""
	START OF MASK STUFF.
"""

import imageio as io
arr = io.read('../scratch/testMask.png').get_data(0)
arr = np.int64(np.all(arr[:, :, :3] == 0, axis=2))

from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle,Rectangle

# N pixels per mm.
pixelSize = 10
# Beam height in mm converted to pixels.
beamHeight = 0.5

# Look at beam position (center position in mm).
_lookAt = 10
_beamB = _lookAt - beamHeight/2
_beamT = _lookAt + beamHeight/2

# Initialise mask start and stop positions.
# Start and stop are index positions of the array.
start = [0,0]
stop = [0,0]

# Find mask horizontal start and stop positions.
for row in range(arr.shape[0]):
	# Find the first row with a 0 in it.
	if np.sum(arr[row,:]) != arr.shape[0]:
		# Find the middle position of all the values that are 0.
		middle = np.argwhere(arr[row,:] == 0).mean()
		# Store the start position.
		start = [row,middle]
		break
for row in reversed(range(arr.shape[0])):
	if np.sum(arr[row,:]) != arr.shape[0]:
		middle = np.argwhere(arr[row,:] == 0).mean()
		stop = [row,middle]
		break

# Set diameter for the mask (in mm).
_radius = 25
# Create datapoints for two half circles in degrees.
leftCircleAngle = np.linspace(90, 270, 2000)
rightCircleAngle = np.linspace(90, -90, 2000)
# Find the tangent values of the points in each half circle.
leftCircleTangent = np.tan(np.deg2rad(leftCircleAngle))
rightCircleTangent = np.tan(np.deg2rad(rightCircleAngle))

# Get subArray of mask.
# subArray = arr[b:t,:]
# Investigate beam area:
_bt = int( np.absolute(25-_beamT)*10 )
_bb = int( np.absolute(25-_beamB)*10 )
subArray = arr[_bt:_bb,:]

# Get the top and bottom line of the sub array.
line1 = subArray[0,:]
line2 = subArray[-1,:]
# Find the left and right most points for each line.
line1 = np.argwhere(line1 == 0)
line2 = np.argwhere(line2 == 0)
tl = line1.min()
tr = line1.max()
bl = line2.min()
br = line2.max()
# Calculate the tangent for each side.
left = np.arctan(((tl-bl)/pixelSize)/beamHeight)
right = np.arctan(((tr-br)/pixelSize)/beamHeight)

# Find the tangent condition that matches in the circle.
leftAngle = np.deg2rad(leftCircleAngle[ np.argmin(np.absolute(leftCircleTangent-left)) ])
rightAngle = np.deg2rad(rightCircleAngle[ np.argmin(np.absolute(rightCircleTangent-right)) ])

# Find the position of the mask that matches the tangent condition.
circleLeftPosition = np.array([_radius*np.cos(leftAngle),-_radius*np.sin(leftAngle)])
circleRightPosition = np.array([_radius*np.cos(rightAngle),-_radius*np.sin(rightAngle)])

# Get the position of the matched pixel.
x1 = (0 + np.min(np.array([tl,bl])) + np.absolute(tl-bl)/2)/pixelSize
y1 = (_bt + subArray.shape[0]/2)/pixelSize
pos1 = np.array([-25+x1,25-y1])
move1 = circleLeftPosition - pos1

# Right circle.
x2 = (0 + np.min(np.array([tr,br])) + np.absolute(tr-br)/2)/pixelSize
y2 = (_bt + subArray.shape[0]/2)/pixelSize
pos2 = np.array([-25+x2,25-y2])
move2 = circleRightPosition - pos2

# Pathces.
p = []
p.append(Rectangle((-25,_beamB),50,beamHeight,fc='r',alpha=0.25,fill=True))
p.append(Circle(-move1,_radius,ec='g',fill=False))
p.append(Circle(-move2,_radius,ec='b',fill=False))
pc = PatchCollection(p,match_original=True)
# Plotting.
fig, ax = plt.subplots()
ax.imshow(arr,cmap='gray',extent=[-25,25,-25,25])
ax.add_collection(pc)
plt.show()