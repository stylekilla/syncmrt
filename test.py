import matplotlib as mpl
mpl.use('Qt5Agg')

import imageio as io
arr = io.read('../scratch/testMask2.jpg').get_data(0)
import numpy as np
# arr = np.int64(np.all(arr[:, :, :3] == 0, axis=2))

from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle,Rectangle
from matplotlib.gridspec import GridSpec

"""
Usage Notes
-----------
- The mask array must be sub-sampled at 1/5th of the nominal beam size; or
- the beam height must be 5 times the size of the mask array pixel size.
- Mask must be 0 (tungsten) to 255 (free air).

"""

"""
Set up the beam/images.
"""
# N pixels per mm.
pixelSize = arr.shape[0]/50
# Beam height in mm converted to pixels.
beamHeight = 1

# Patient speed in mm/s.
_patientSpeed = 5
# Patient travel distance in mm.
_top = 25
_bottom = -25
_patientTravelDistance = _top-_bottom
# Time for patient to travel distance in s.
_patientTravelTime = _patientTravelDistance/_patientSpeed
# Time per beam height.
_deltaT = beamHeight/_patientSpeed

"""
Create the mask.
"""
# Set diameter for the mask (in mm).
_radius = 100
# Create datapoints for two half circles in degrees.
maskLeftAngle = np.linspace(90, 270, 2000)
maskRightAngle = np.linspace(90, -90, 2000)
# Find the tangent values of the points in each half circle.
maskLeftTangent = np.tan(np.deg2rad(maskLeftAngle))
maskRightTangent = np.tan(np.deg2rad(maskRightAngle))


"""
Set up the scan parameters.
"""
# Initialise mask start and stop positions.
# Start and stop are index positions of the array.
# start = [0,0]
# stop = [0,0]

# # Find mask horizontal start and stop positions.
# for row in range(arr.shape[0]):
# 	# Find the first row with a 0 in it.
# 	if np.sum(arr[row,:]) != arr.shape[0]:
# 		# Find the middle position of all the values that are 0.
# 		middle = np.argwhere(arr[row,:] == 0).mean()
# 		# Store the start position.
# 		start = [row,middle]
# 		break
# for row in reversed(range(arr.shape[0])):
# 	if np.sum(arr[row,:]) != arr.shape[0]:
# 		middle = np.argwhere(arr[row,:] == 0).mean()
# 		stop = [row,middle]
# 		break


"""
Disect the scan into beam steps.
"""
# nBeams = int((np.absolute(start[0]-stop[0])/pixelSize)/beamHeight)+1
# beamPositions = np.linspace(start[0],stop[0],nBeams)
nBeams = int(_patientTravelDistance/beamHeight)
# beamPositions = np.linspace(25-beamHeight/2,-25-beamHeight/2,nBeams+1)
beamPositions = np.linspace(_top-beamHeight/2,_bottom+beamHeight/2,nBeams)

leftMaskPosition = []
rightMaskPosition = []

"""
Set up plot.
"""
# Create figure.
fig = plt.figure(constrained_layout=True)
# Create grid.
gs = GridSpec(4, 2, figure=fig)

ax0 = fig.add_subplot(gs[:,0])
ax1 = fig.add_subplot(gs[0,1])
ax2 = fig.add_subplot(gs[1,1])
ax3 = fig.add_subplot(gs[2,1])
ax4 = fig.add_subplot(gs[3,1])

# Show the image.
ax0.imshow(arr,cmap='gray',extent=[-25,25,-25,25])

# Patches.
p = []

"""
Iterate over beams.
"""
for i in beamPositions:
	# Investigate beam area:
	_bt = int( (25-(i + beamHeight/2 ))*pixelSize )
	_bb = _bt + int(beamHeight*pixelSize)

	# Get sub array for treatment.
	subArray = arr[_bt:_bb,:]
	# Get the top and bottom line of the sub array.
	line1 = subArray[0,:]
	line2 = subArray[-1,:]
	# Find the left and right most points for each line.
	line1 = np.argwhere(line1 == 255)
	line2 = np.argwhere(line2 == 255)

	# See if the top/bottom lines have any mask data.
	if line2.shape == (0,1):
		# The bottom line has no data, check the top line.
		if line1.shape == (0,1):
			# No mask data found on bottom or top.
			# Close the slits at the top.
			pos1 = np.array([0,i])
			pos2 = np.array([0,i])
			move1 = np.array([0,_radius + beamHeight/2]) - pos1
			move2 = np.array([0,_radius + beamHeight/2]) - pos2
			continue
		else:
			# Data was found at the top of the mask.
			# Find a new bottom line that has data.
			for j in reversed(range(1,subArray.shape[0])):
				line2 = subArray[j,:]
				line2 = np.argwhere(line2 == 255)
				if line2.shape != (0,1):
					# We found something! Save it and leave.
					_bb -= j
					break
				else:
					# If nothing found yet, continue on.
					pass

	elif line1.shape == (0,1):
		# The top line has no data, check the bottom line.
		if line2.shape == (0,1):
			# No mask data found on top or bottom.
			# Close the slits at the bottom.
			pos1 = np.array([0,i])
			pos2 = np.array([0,i])
			move1 = np.array([0,-_radius - beamHeight]) - pos1
			move2 = np.array([0,-_radius - beamHeight]) - pos2
			continue
		else:
			# Data was found at the bottom of the mask.
			# Find a new top line that has data.
			for j in range(subArray.shape[0]):
				line1 = subArray[j,:]
				line1 = np.argwhere(line1 == 255)
				if line1.shape != (0,1):
					# We found something! Save it and leave.
					_bt += j
					break
				else:
					# If nothing found yet, continue on.
					pass

	# Get min and max values for each line.
	tl = line1.min()
	tr = line1.max()
	bl = line2.min()
	br = line2.max()

	# Calculate the tangent for the left side.
	if tl > bl:
		x = bl - tl
		y = -(_bt-_bb)
		# y = (arr.shape[0]/2-_bt) - (arr.shape[0]/2-_bb)
	elif bl > tl:
		x = tl - bl
		y = _bt-_bb

	leftAngle = np.rad2deg(np.arctan2(y, x))
	print("(x,y) ({},{}) = {}".format(x,y,leftAngle))

	# Calculate the tangent for the right side.
	if tl < bl:
		x = bl - tl
		y = _bt-_bb
	elif bl < tl:
		x = tl - bl
		y = np.absolute(_bb-_bt)

	rightAngle = np.rad2deg(np.arctan2(y, x))

	# print("{},{}".format(x1,x2))

	xl = _radius*np.cos(leftAngle)
	yl = _radius*np.sin(leftAngle)
	maskLeftPosition = np.array([xl,yl])

	xr = _radius*np.cos(rightAngle)
	yr = _radius*np.sin(rightAngle)
	maskRightPosition = np.array([xr,yr])

	# Find the tangent condition that matches in the circle.
	# leftAngle = np.deg2rad(maskLeftAngle[ np.argmin(np.absolute(maskLeftTangent-left)) ])
	# rightAngle = np.deg2rad(maskRightAngle[ np.argmin(np.absolute(maskRightTangent-right)) ])
	# leftAngle = np.correlate(maskLeftTangent,np.array([left]),mode='valid')
	# leftAngle = maskLeftAngle[np.argmin(np.absolute((maskLeftTangent/left)-1))]

	# _left.append(left)
	# _right.append(right)

	# Find the position of the mask that matches the tangent condition.
	# circleLeftPosition = np.array([_radius*np.cos(leftAngle),-_radius*np.sin(leftAngle)])
	# circleRightPosition = np.array([_radius*np.cos(rightAngle),-_radius*np.sin(rightAngle)])

	# Get the position of the matched pixel.
	x1 = (0 + np.min(np.array([tl,bl])) + np.absolute(tl-bl)/2)/pixelSize
	# y1 = (_bt + subArray.shape[0]/2)/pixelSize
	# y1 = (_bt + (np.absolute(_bt-_bb)/2))/pixelSize
	y1 = i
	pos1 = np.array([-25+x1,y1])
	move1 = pos1 - maskLeftPosition

	# Right circle.
	x2 = (0 + np.min(np.array([tr,br])) + np.absolute(tr-br)/2)/pixelSize
	# y2 = (_bt + subArray.shape[0]/2)/pixelSize
	y2 = i
	pos2 = np.array([-25+x2,25-y2])
	move2 = maskRightPosition - pos2

	# Plotting patches.
	# p.append(Rectangle((-25,i-(beamHeight/2)),50,beamHeight,fc='r',alpha=0.25,fill=True))
	p.append(Circle(-move1,_radius,ec='g',fill=False,linestyle='--'))
	# p.append(Circle(-move2,_radius,ec='b',fill=False,linestyle='--'))
	# ax0.plot(pos1[0],pos1[1],'r+')
	ax0.plot(maskLeftPosition[0],maskLeftPosition[1],'r+')
	# ax0.plot(pos2[0],pos2[1],'r+')

	# Plot tangent left.
	# x = np.linspace(-25,25,50)
	# m = ((bl-tl)/(_bb-_bt))
	# c = pos1[1]-pos1[0]*m
	# ax0.plot(x,m*x+c,'g--')

	# Store the moves required by the masks.
	leftMaskPosition.append(-move1)
	rightMaskPosition.append(-move2)

# Plotting.
pc = PatchCollection(p,match_original=True)
ax0.add_collection(pc)


"""
Velocity/acceleration profiles.
"""
# Initialise lists.
leftMaskVelocity = []
rightMaskVelocity = []
leftMaskAcceleration = []
rightMaskAcceleration = []

# Generate data.
for i in range(len(leftMaskPosition)-1):
	# Calculate velocity.
	leftMaskVelocity.append(np.absolute(leftMaskPosition[i]-leftMaskPosition[i+1])/_deltaT)
	rightMaskVelocity.append(np.absolute(rightMaskPosition[i]-rightMaskPosition[i+1])/_deltaT)
	# Calculate acceleration.
	leftMaskAcceleration.append(leftMaskVelocity[i]/_deltaT)
	rightMaskAcceleration.append(rightMaskVelocity[i]/_deltaT)

# Reshape the lists.
leftMaskVelocity = np.array(leftMaskVelocity).reshape(len(leftMaskVelocity),2)
rightMaskVelocity = np.array(rightMaskVelocity).reshape(len(rightMaskVelocity),2)
leftMaskAcceleration = np.array(leftMaskAcceleration).reshape(len(leftMaskAcceleration),2)
rightMaskAcceleration = np.array(rightMaskAcceleration).reshape(len(rightMaskAcceleration),2)
leftMaskPosition = np.array(leftMaskPosition).reshape(len(leftMaskPosition),2)
rightMaskPosition = np.array(rightMaskPosition).reshape(len(rightMaskPosition),2)

# Time scale for plots.
# xPosition = np.linspace(0,_deltaT*nBeams,nBeams)
# x = np.linspace(0,_deltaT*nBeams,nBeams+1)
# x1 = np.linspace(0,_patientTravelTime-_deltaT*1,nBeams-1)
# x2 = np.linspace(0,_patientTravelTime-_deltaT*2,nBeams-2)

x1 = np.linspace(0,_patientTravelTime,len(leftMaskPosition[:,0]))
x2 = np.linspace(0,_patientTravelTime-_deltaT,len(leftMaskVelocity[:,0]))

print("Patient Travel Velocity: {} mm/s".format(_patientSpeed))
print("Patient Travel Distance: {} mm ({} to {})".format(_patientTravelDistance,_top,_bottom))
print("Patient Travel Time: {} s".format(_patientTravelTime))
print("Beam Height: {} mm".format(beamHeight))
print("Number of beam windows: {}".format(nBeams))
print("Time interval between beams: {} s".format(_deltaT))

# Plot the profiles.
ax1.set_title("Mask Position (Horizontal Motors)")
ax1.set_ylabel("Position (mmm)")
ax1.plot(x1,leftMaskPosition[:,0],'gx-')
ax1.plot(x1,rightMaskPosition[:,0],'bx-')
ax2.set_title("Mask Position (Vertical Motors)")
ax2.set_ylabel("Position (mmm)")
ax2.plot(x1,leftMaskPosition[:,1],'gx-')
ax2.plot(x1,rightMaskPosition[:,1],'bx-')
ax3.set_title("Mask Velocity (Horizontal Motors)")
ax3.set_ylabel("Velocity (mm/s)")
ax3.plot(x2,leftMaskVelocity[:,0],'gx-')
ax3.plot(x2,rightMaskVelocity[:,0],'bx-')
ax4.set_title("Mask Velocity (Vertical Motors)")
ax4.set_ylabel("Velocity (mm/s)")
ax4.set_xlabel("Time (s)")
ax4.plot(x2,leftMaskVelocity[:,1],'gx-')
ax4.plot(x2,rightMaskVelocity[:,1],'bx-')

# Show the plot.
plt.show()





"""
A DIFFERENT TEST. CALCULATING 3D POINTS.
"""
a = 49
b = 97

ta = np.arctan(63/105)
tb = np.arctan(71/66.5)

x = b*np.sin(ta+tb)*np.cos(ta) - a*np.tan(ta+tb)*np.cos(ta) + b*np.cos(ta+tb)*np.tan(ta+tb)*np.cos(ta) - a*np.sin(ta)
print("X: Expected ~51/52 mm, got {:.2f}.".format(x))
y  = a*np.cos(ta) + b*np.cos(ta+tb)*np.sin(ta) - a*np.sin(ta)*np.tan(ta+tb) + b*np.sin(ta)*np.tan(ta+tb)*np.sin(ta+tb)
print("Y: Expected ~88/89 mm, got {:.2f}.".format(y))