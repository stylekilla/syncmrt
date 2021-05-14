import numpy as np
from PyQt5 import QtWidgets
import logging

def calculate(p1,p2,t1,t2):
	"""
	This will take two points (p1 and p2) from two different imaging frames at non-orthogonal angles (t1 and t2) from the 0deg axis and give back a globally fixed position value (p) for the true position of the object w.r.t. to the fixed axis.

	https://www.desmos.com/calculator/g28bkshwyz

		Parameters
		----------
		p1 : [float,float] or list([float,float])
			The position of the object (?,z) in imaging frame 1.
		p2 : [float,float]
			The position of the object (?,z) in imaging frame 2.
		t1 : float
			The angle of image plane 1 relative to the BEV.
		t2 : float
			The angle of image plane 2 relative to the BEV.

		Returns
		-------
		p
			The calculated location of the object with respect to the fixed synchrotron XYZ axes.
	"""
	test = np.array(p1)

	# Flag for axis alignment.
	swap = False
	# Determine if image data needs to be swapped.
	if t1 < t2: 
		swap = True

	# Data prep.
	if swap:
		p1_prime = p2
		p2_prime = p1
		t1_prime = t2
		t2_prime = t1
	else:
		p1_prime = p1
		p2_prime = p2
		t1_prime = t1
		t2_prime = t2
	
	# Get the seperation between the images (in radians).
	theta_a = np.deg2rad(t1_prime)
	theta_b = np.deg2rad(t2_prime)
	theta = np.abs(theta_a-theta_b)

	if len(test.shape) == 1:
		# If a single number is passed then turn it into a numpy array.
		# This is most likely an isocentre value.
		p1 = np.array([p1_prime])
		p2 = np.array([p2_prime])
	else:
		p1 = np.array(p1_prime)
		p2 = np.array(p2_prime)

	# The result to return.
	result = np.zeros((len(p1),3))

	message = """
--------------
NOI Debugging:
==============
Inputs
--------------
p1: \n {}

p2: \n {}

t1: {}
t2: {}
""".format(p1,p2,t1,t2)

	# Iterate over each point.
	for i in range(len(p1)):
		# Unpack the two points.
		a, z1 = p1[i]
		b, z2 = p2[i]
		# Calculate the chord length between the two imaging planes.
		c = (a**2 + b**2 - 2*a*b*np.cos(2*np.pi-theta))**0.5

		# Calculate the angle between the chord and the a/b axes.
		psi_a = np.abs(np.arcsin((b*np.sin(theta))/c))
		psi_b = np.abs(np.arcsin((a*np.sin(theta))/c))

		# If the chord length is zero (which occurs when a and b are both 0), there is a divide by zero above. So, instead, set the angles to 0.
		if np.isnan(psi_a): psi_a = 0.0
		if np.isnan(psi_b): psi_b = 0.0

		# Calculate the angle between the chord and the a'/b' axes.
		phi_a = (np.pi/2) - psi_a
		phi_b = (np.pi/2) - psi_b

		# Calculate the distance of the imaging frame the origin.
		a_prime = c*np.sin(phi_b)/np.sin(theta)
		b_prime = c*np.sin(phi_a)/np.sin(theta)
		# Determine the positive/negative direction of the distance.
		if (a>=0):
			b_prime = -b_prime
		if (b<0):
			a_prime = -a_prime


		# Calculate the radius to the point.
		r_a = (a**2 + a_prime**2)**0.5
		r_b = (b**2 + b_prime**2)**0.5
		r = (r_a+r_b)/2

		# Calculate angle to radius line.
		omega = np.arctan2(a,a_prime)
		theta_r = theta_a + omega

		# Calculate the final resting positions on the orthogonal aligned BEV axes.
		x = r*np.cos(theta_r)
		y = r*np.sin(theta_r)
		z = (z1+z2)/2
		# Add the new points to the result.
		result[i,:] = [x,y,z]

		message += """
==============
Point {}/{}
--------------
Angle between imaging planes A ({:.3f}) and B ({:.3f}) is {:.3f} degrees.
Chord length between imaging planes is {:.3f} mm.
Calculated psi_a as {:.3f} degrees and psi_b {:.3f} degrees.
Calculated phi_a as {:.3f} degrees and phi_b {:.3f} degrees.
Calculated a' as {:.3f} mm and b' as {:.3f} mm.
Radius of point according to a is {:.3f} mm and for b is {:.3f} mm. Average is {:.3f} mm.
Omega is {:.3f} degrees. Angle to radius is {:.3f} deg.
--------------
Point is calculated as {}.
		""".format(
			i+1,len(p1),
			t1,t2,np.rad2deg(theta),
			c,
			np.rad2deg(psi_a),np.rad2deg(psi_b),
			np.rad2deg(phi_a),np.rad2deg(phi_b),
			a_prime,b_prime,
			r_a,r_b,r,
			np.rad2deg(omega),np.rad2deg(theta_r),
			result[i,:]
		)
	
	logging.debug(message)

	return result