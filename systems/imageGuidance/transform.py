import numpy as np

# def secondaryTranslation(rotation,translation):
# 	''' Rotation should be in degrees. Translation should be [x,y].'''
# 	# Vector a, representing the current coordinate.
# 	a = np.array(translation)

# 	# Rotation happens CCW on stage.
# 	theta = np.deg2rad(rotation)

# 	# Vector b, representing the first horizontal motor plane, we assume the second motor plane is orthogonal to it.
# 	b = np.array([np.cos(theta),np.sin(theta)])

# 	# Find phi, angle between a and b.
# 	phi = np.arccos(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))

# 	# Calculate absolute distance of translation.
# 	# hyp = np.sqrt(a[0]**2 + a[1]**2)
# 	hyp = np.linalg.norm(a)

# 	# Find two horizontal motor translations.
# 	H1 = hyp*np.cos(phi)
# 	H2 = hyp*np.sin(phi)

# 	# print('Results:')
# 	# print('rotation',rotation)
# 	# print('translation',translation)
# 	# print('a',a)
# 	# print('b',b)
# 	# print('theta',theta)
# 	# print('phi',np.rad2deg(phi))
# 	# print('hyp',hyp)
# 	# print('H1',H1)
# 	# print('H2',H2)

# 	return H1, H2

def secondaryTranslation(rotation,translation):
	''' Rotation should be in degrees. Translation should be 'synchrotron' [x,y].'''
	out = np.array([0,0])

	# Point In. Accounts for H1/H2 motor directions and Synchrotron CS directions.
	x,y = translation
	pIn = np.array([-y,x])

	# Angle, theta, in radians.
	theta = np.deg2rad(rotation)

	# 2D rotation matrix.
	R = np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])

	# Apply rotation matrix (rotates x-y coordinate frame).
	pOut = np.dot(R,pIn)

	# Get output values.
	H1, H2 = pOut

	return H1, H2