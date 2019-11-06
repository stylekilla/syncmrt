import numpy as np

def quaternion(v):
	# Take 3d input and turn into quaternion.
	x,y,z = v
	return np.array(([0,x,y,z]))

def rotation(theta,axis=None):
	# Rotation quaternion of angle theta by axis x,y,z.
	# Axis input should be of type [1,0,0].
	if axis is None:
		axis = np.array(([1,1,1]))

	theta = np.deg2rad(theta)
	i,j,k = np.sin(theta/2)*axis

	return np.array([np.cos(theta/2),i,j,k])

def magnitude(q):
	# Calculate magnitude of quaternion.
	return np.sqrt(q[0]**2 + q[1]**2 + q[2]**2 + q[3]**2)

def normalise(q):
	# Normalise a quaternion.
	q /= magnitude(q)
	return q

def multiply(a,b):
	# Product of two quarternions, b operating on a.
	a0,a1,a2,a3 = a
	b0,b1,b2,b3 = b

	q0 = b0*a0 - b1*a1 - b2*a2 - b3*a3
	q1 = b0*a1 + b1*a0 - b2*a3 + b3*a2
	q2 = b0*a2 + b1*a3 + b2*a0 - b3*a1
	q3 = b0*a3 - b1*a2 + b2*a1 + b3*a0

	q = np.array(([q0,q1,q2,q3]))

	return q

def product(q):
	''' q as list'''
	qout = multiply(q[0],q[1])
	for i in range(2,len(q)):
		qout = multiply(qout,q[i])

	return qout

def intrinsicRotation(q):
	''' q as list'''
	return product(q)

def globalRotation(q):
	''' q as list'''
	e = len(q)-1
	qout = multiply(q[e],q[e-1])
	for i in range(e-2,-1,-1):
		qout = multiply(qout,q[i])

	return qout

def inverse(a):
	# Inverse of quaternion a
	a0,a1,a2,a3 = a
	q = (np.array(([a0,-a1,-a2,-a3])) / (a0**2 + a1**2 + a2**2 + a3**2))

	return q

def euler(q):
	R = np.array([[(q[0]**2+q[1]**2-q[2]**2-q[3]**2), 2*(q[1]*q[2]-q[0]*q[3]), 2*(q[1]*q[3]+q[0]*q[2])],
		[2*(q[2]*q[1]+q[0]*q[3]), (q[0]**2-q[1]**2+q[2]**2-q[3]**2), 2*(q[2]*q[3]-q[0]*q[1])],
		[2*(q[3]*q[1]-q[0]*q[2]), 2*(q[3]*q[2]+q[0]*q[1]), (q[0]**2-q[1]**2-q[2]**2+q[3]**2)]])

	return R

def rotate(a,r):
	# Rotate quaternion a, by quaternion r.
	ri = inverse(r)
	b = product(product(r,a),ri)

	return b