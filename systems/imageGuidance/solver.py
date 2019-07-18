import math
import numpy as np

'''
ASSUMPTIONS:
	1. That the orientation of the two objects are the same vertically (i.e. one cannot be upside down and the other upright.)
	2. CT is left points in mm, XR is right points in mm.
	3. User origin is in relation to Dicom origin.
	4. All points are relative to the user origin.
	5. Both CT and Synchrotron orthogonal images are the same CW or CCW direction of the image.
'''

class solver:
	def __init__(self):
		self._leftPoints = np.zeros((3,3))
		self._rightPoints = np.zeros((3,3))
		self._patientIsocenter = None
		self._machineIsocenter = np.zeros((3,))
		self._scale = 0
		self.solution = np.zeros((6,))
		self.transform = np.identity(4)

	def input(self,left=None,right=None,patientIsoc=None,machineIsoc=None):
		# Update vars.
		if left is not None: self._leftPoints = np.array(left)
		if right is not None: self._rightPoints = np.array(right)
		if patientIsoc is not None: self._patientIsocenter = np.array(patientIsoc)
		if machineIsoc is not None: self._machineIsocenter = np.array(machineIsoc)

	def centroid(self):
		# Run the centroid calcaulation routine.
		self._leftCentroid = centroid(self._leftPoints)
		self._rightCentroid = centroid(self._rightPoints)

	def solve(self):
		'''Points should come in as xyz cols and n-points rows: np.array((n,xyz))'''
		n = np.shape(self._leftPoints)[0]

		# Find the centroids of the LEFT and RIGHT WCS.
		self._leftCentroid = centroid(self._leftPoints)
		self._rightCentroid = centroid(self._rightPoints)

		# If no patient isocenter is set, align to the centroid.
		if self._patientIsocenter is None:
			self._patientIsocenter = self._leftCentroid

		print('Left Points:',self._leftPoints)
		print('Left Ctd:',self._leftCentroid)
		print('Right Points:',self._rightPoints)
		print('Right Ctd:',self._rightCentroid)
		print('Patient Isoc:',self._patientIsocenter)
		print('Machine Isoc:',self._machineIsocenter)

		# Find the LEFT and RIGHT points in terms of their centroids (notation: LEFT Prime, RIGHT Prime)
		_leftPrime = np.zeros([n,3])
		_rightPrime = np.zeros([n,3])

		for i in range(n):
			_leftPrime[i,:] = np.subtract(self._leftPoints[i,:],self._leftCentroid)
			_rightPrime[i,:] = np.subtract(self._rightPoints[i,:],self._rightCentroid)

		# Find the quaternion matrix, N.
		N = quaternion(_leftPrime,_rightPrime)

		# Solve eigenvals and vec that maximises rotation.
		val, vec = eigen(N)

		# Extract transformation quarternion from evec.
		q = np.zeros((4,))
		q[0] = vec[0][0]
		q[1] = vec[1][0]
		q[2] = vec[2][0]
		q[3] = vec[3][0]

		# Compute rotation matrix, R.
		R = rotationMatrix(q)
		R = np.reshape(R,(3,3))
		self.transform[:3,:3] = R

		# Extract individual angles in degrees.
		rotation = angles(R)

		# Translation 1: Centroid to patient isocenter.
		translation1 = -(self._leftCentroid - self._patientIsocenter)

		# Translation 2: Centroid isoc to machine isocenter.
		translation2 = self._machineIsocenter - self._rightCentroid

		# Final translation is a combination of all other translations.
		translation = translation2 - translation1
		self.transform[:3,3] = translation.transpose()

		# Extract scale.
		# if synchRotIsoc is not None:
		# 	self._rightPoints = np.zeros([n,3])
		# 	for i in range(n):
		# 		self._rightPoints[i,:] = np.subtract(self._rightPoints[i,:],self._rightCentroid)

		self.scale = scale(self._leftPoints,self._rightPoints,R)
		self.solution = np.hstack((translation,rotation))

		# Calculate the patient isoc in the synchrotron frame of reference for plotting.
		self._syncPatientIsocenter = self._rightCentroid + translation1

		print('Translation 1: patisoc - leftctd',translation1)
		print('Translation 2: machiso - patisoc',translation2)
		print('Overall transpose:',translation)
		print('Synch Patient Iso:',self._syncPatientIsocenter)

		return self.solution

# Obtain scale factor between coordinate systems. Requires left and right points in reference to centroids.
def scale(lp,rp,R):
	n = np.shape(lp)[0]

	D = np.zeros((n,1))
	S_l = np.zeros((n,1))

	for i in range(n):
		D[i,0] = np.dot(np.array([rp[i,:]]),np.dot(R,np.array([lp[i,:]]).T))[0][0]
		S_l[i,0] = np.linalg.norm(lp[i,:])**2

	return np.sum(D)/np.sum(S_l)

# Find the centroid of a set of points (pts).
def centroid(pts):
	n = np.shape(pts)[0]
	ctd = (1/n)*np.sum(pts,axis=0)
	return ctd

# Pass left and right coordinate system points in and pass out the matrix N.
def quaternion(l,r):
	# Calculate sum of products matrix, M.
	M = np.dot(l.transpose(),r)

	# Calculate xx, xy, xz, yy ... zz. 
	sxx = M[0,0]
	sxy = M[0,1]
	sxz = M[0,2]
	syx = M[1,0]
	syy = M[1,1]
	syz = M[1,2]
	szx = M[2,0]
	szy = M[2,1]
	szz = M[2,2]

	# Calculate N
	N = np.array([[sxx+syy+szz, syz-szy, szx-sxz, sxy-syx],
	[syz-szy, sxx-syy-szz, sxy+syx, szx+sxz],
	[szx-sxz, sxy+syx, -sxx+syy-szz, syz+szy],
	[sxy-syx, szx+sxz, syz+szy, -sxx-syy+szz]])

	# Return the matrix N
	return N

#  Find the eigenvector and eigenvalue for a given matrix.
def eigen(arr):
	#  Find the eigen vector and value of the array, arr.
	e, v = np.linalg.eig(arr)

	#  Find the maximum eigen value and it's corresponding eigen vector.
	val = np.amax(e)
	ind = np.argmax(e)
	i = np.unravel_index(ind,np.shape(e))

	vec = v[:,i]

	# Return the maximum eigenvalue and corresponding eigenvector.
	return val, vec

# Find the rotation matrix for a given eigen-solution.
def rotationMatrix(q):
	#  Calculate rotation matrix, R, based off quarternion input. This should be the eigenvector solution to N.
	R = np.array([[(q[0]**2+q[1]**2-q[2]**2-q[3]**2), 2*(q[1]*q[2]-q[0]*q[3]), 2*(q[1]*q[3]+q[0]*q[2])],
	[2*(q[2]*q[1]+q[0]*q[3]), (q[0]**2-q[1]**2+q[2]**2-q[3]**2), 2*(q[2]*q[3]-q[0]*q[1])],
	[2*(q[3]*q[1]-q[0]*q[2]), 2*(q[3]*q[2]+q[0]*q[1]), (q[0]**2-q[1]**2-q[2]**2+q[3]**2)]])

	# Return the rotation matrix, R. This is in the form of Rz*Ry*Rx, x -> y -> z. 
	# This matrix is orthogonal (no translations or reflections.)
	return R

# Extract individual rotations around the x, y and z axis seperately. 
def angles(R):
	# Two possible angles for y.
	y = []
	y.append(np.arcsin(R[2][0]))
	y.append(np.pi-np.arcsin(R[2][0]))

	# Angle for Z
	z = []
	for i in range(len(y)):
		z.append(np.arctan2(R[1][0]/np.cos(y[i]),R[0][0]/np.cos(y[i])))


	# Angle for X
	x = []
	for i in range(len(y)):
		x.append(np.arctan2(R[2][1]/np.cos(y[i]),R[2][2]/np.cos(y[i])))

	success = False
	while (success is False):
		for i in range(len(y)):
			xx = np.rad2deg(x[i])
			yy = np.rad2deg(y[i])
			zz = np.rad2deg(z[i])

		if ((-95 < xx < 95) & (-95 < yy < 95) & (-360 < zz < 360)):
			success = True
		else:
			try:
				del x[i]
				del y[i]
				del z[i]
			except:
				logging.critical('Cannot solve alignment. Unknown cause.')
				print('\033[91m Unable to solve for the alignment. Please select the points properly.')
				return 0, 0, 0

	# Angles must be applied in xyz order.
	return np.array([xx,yy,zz])
