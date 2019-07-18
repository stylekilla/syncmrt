import numpy as np

''' Find point after a 3D rotation about a fixed axis. '''
def fixedRotation(p,cor,rx,ry,rz):
	# Define point P with P[3]=1 to include translations.
	P = np.array([
		[p[0]],
		[p[1]],
		[p[2]],
		[1]
		])

	# Translation from origin to cor.
	T = np.array([
		[1,0,0,cor[0]],
		[0,1,0,cor[1]],
		[0,0,1,cor[2]],
		[0,0,0,1]
		])

	# Translation from point to origin.
	Ti = np.array([
		[1,0,0,-1],
		[0,1,0,-1],
		[0,0,1,-1],
		[0,0,0,1]
		])

	Ti = T*Ti

	# 4x4 Rotation matrix.
	R = np.array([
		[1,0,0,0],
		[0,1,0,0],
		[0,0,1,0],
		[0,0,0,1]
		])

	# Make rotation matrix of angles x y and z.
	x = np.deg2rad(rx)
	y = np.deg2rad(ry)
	z = np.deg2rad(rz)
	rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
	ry = np.array([[np.cos(y),0,-np.sin(y)],[0,1,0],[np.sin(y),0,np.cos(y)]])
	rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
	r = rz @ ry @ rx

	# Add 3x3 rotation matrix, r, to 4x4 Rotation matrix, R.
	R[:3,:3] = r

	print(R)
	print(T)
	print(P)
	# Transform to cor, complete rotation, then translate back to origin.
	transform = T@R@Ti

	# Return result.
	result = np.dot(transform,P).reshape(4,)[0:3]
	print(result)
	# return transform@P
	return result

