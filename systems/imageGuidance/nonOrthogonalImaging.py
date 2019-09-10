import numpy as np
import logging

def calculate(p1,p2,t1,t2):
	"""
	This will take two points (p1 and p2) from two different imaging frames at non-orthogonal angles (t1 and t2) from the 0deg axis and give back a globally fixed position value (p) for the true position of the object w.r.t. to the fixed axis.
	+X is downstream, +Y is downstream left (synchrotron coordinate system).
	Xv and Yv are X and Y rotated by +45 (right handed coordinate system). 


		Parameters
		----------
		p1 : [float,float] or list([float,float])
			The position of the object (?,z) in imaging frame 1.
		p2 : [float,float]
			The position of the object (?,z) in imaging frame 2.
		t1 : float
			The angular separation (in degrees) of the first imaging angle and Xv.
		t2 : float
			The angular separation (in degrees) of the second imaging angle and Yv.

		Returns
		-------
		p
			The calculated location of the object with respect to the fixed synchrotron XYZ axes.
	"""
	p1 = np.array(p1)
	p2 = np.array(p2)

	result = np.zeros((len(p1),3))

	# Expect at least 3 points.
	if p1.ndim != 2:
		logging.critical("Cannot interpret input of array with ndim {}.".format(p1.ndim))
		return
	else:
		for i in range(len(p1)):
			# Convert angles to radians, calculate them from +/- 45 deg virtual axes.
			alpha = np.deg2rad(45-t2)
			beta = np.deg2rad(t1+45)
			# Unpack the two points.
			a, z2 = p2[i]
			b, z1 = p1[i]
			# Do some safe conversions if zeros are encountered.
			if a == 0: a = 1e-9
			if b == 0: b = 1e-9
			# Calculate the separation of each imaging axis from the true X axis.
			phi = np.pi/2 - alpha - beta
			psi_a = np.arctan((a*np.sin(phi))/(a*np.cos(phi)+b))
			psi_b = np.pi/2-alpha-beta-psi_a
			# Calculate the radius of the point p from the origin.
			r1 = a/np.sin(psi_a)
			r2 = b/np.sin(psi_b)
			r = (r1+r2)/2
			# Calculate the point with respect to the virtual X and Y axes (rotated +45deg).
			xv = r*np.sin(psi_b+beta)
			yv = r*np.sin(psi_a+alpha)
			# Calculate the point with respect to the true synchrotron XYZ axes.
			x = -(np.sqrt(2)/2)*xv - (np.sqrt(2)/2)*yv
			y = -(np.sqrt(2)/2)*xv + (np.sqrt(2)/2)*yv
			z = (z1+z2)/2
			# Add the new points to the result.
			result[i,:] = [x,y,z]
	return result