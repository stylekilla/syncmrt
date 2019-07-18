import numpy as np

def translationOnRotation(translation,rotation,solveFor=None):
	''' 
	This method mathematically solves how much to adjust a translation by when it is affected by a rotation.
	-	Translation should be 'synchrotron' coordinate in a plane e.g., [x,y].
	-	Rotation should be the current rotation stage position in degrees around an axis e.g. [z].

	Examples:
	-	If we are rotating about x: (translation) y,z and (rotation) x
	-	If we are rotating about y: (translation) x,z and (rotation) y
	-	If we are rotating about z: (translation) x,y and (rotation) z
	'''
	if rotation == np.inf:
		# If the rotation provided is an infitnite value, assume the motor isn't connected, so return an inf.
		return np.inf

	# Set the output.
	out = np.array([0,0])

	if solveFor is not None:
		if solveFor == 'tx':
			# We have specified to solve for 'x'. 
			x = translation
			y = 0
		elif solveFor == 'ty':
			# We have specified to solve for 'y'. 
			x = 0
			y = translation
	else:
		# We are solving for two things at once.
		x,y = translation

	# Point In. 
	pIn = np.array([-y,x])
	# THIS IS NOT SO MALLEABLE YET.... NOT SURE HOW TO PROCEED.

	# Angle, theta, in radians.
	theta = np.deg2rad(rotation)

	# 2D rotation matrix.
	R = np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])

	# Apply rotation matrix (rotates x-y coordinate frame).
	pOut = np.dot(R,pIn)

	# Get output values.
	x,y = pOut

	if solveFor is not None:
		if solveFor == 'tx':
			return x
		elif solveFor == 'ty':
			return y
	else:
		return x,y


# 	# Currently this is only specific to the MRT stage in Hutch 2B.
# def translationOnRotation(translation,rotation):
# 	''' 
# 	This method mathematically solves how much to adjust a translation by when it is affected by a rotation.
# 	-	Translation should be 'synchrotron' coordinate.
# 	-	Rotation should be in degrees.
# 	'''
# 	out = np.array([0,0])

# 	# Point In. Accounts for H1/H2 motor directions and Synchrotron CS directions.
# 	x,y = translation
# 	pIn = np.array([-y,x])

# 	# Angle, theta, in radians.
# 	theta = np.deg2rad(rotation)

# 	# 2D rotation matrix.
# 	R = np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])

# 	# Apply rotation matrix (rotates x-y coordinate frame).
# 	pOut = np.dot(R,pIn)

# 	# Get output values.
# 	H1,H2 = pOut

# 	return H1,H2