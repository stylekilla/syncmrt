import numpy as np

def wcs2wcs(left,right):
	'''
	Left and right coordinate systems must be presented by a 3x3 matrix that describes the
	mapping of the X Y and Z (rows) axes onto i j and k (cols).
	'''
	# Find the quaternion matrix, N.
	N = quaternion(left,right)
	# Solve eigenvals and vec that maximises rotation.
	val, vec = eigen(N)
	# Extract transformation quarternion from evec.
	q = np.zeros((4,))
	q[0] = vec[0][0]
	q[1] = vec[1][0]
	q[2] = vec[2][0]
	q[3] = vec[3][0]
	# Compute rotation matrix, M.
	M = rotationMatrix(q)
	M = np.reshape(M,(3,3))
	return M

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