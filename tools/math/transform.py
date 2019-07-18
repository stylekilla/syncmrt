import numpy as np

# User-defined errors.
class AxisOutOfBoundsError(Exception):
	"Raised when axis selection is out of bounds."
	pass

# Tramsform for a linear translation stage.
def translation(axis,value):
	# Default to no transformation.
	T = np.identity(4)
	# Input axis must be defined as 0, 1 or 2.
	if axis in (0,1,2):
		T[axis,3] = value
	else:
		raise AxisOutOfBoundsError
	return T

# Transform for a rotation stage.
def rotation(axis,value,origin):
	# Default to no transformation.
	T = np.identity(4)
	R = np.identity(4)
	Ti = np.identity(4)
	# Force value to be angle in radians.
	angle = np.deg2rad(value)
	# Add rotation origin.
	T[:3,3] = np.array(origin).reshape(1,3)
	Ti[:3,3] = -np.array(origin).reshape(1,3)
	# Input axis must be defined as 0, 1 or 2.
	if axis == 0:
		R[:3,:3] = np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]])
	elif axis == 1:
		R[:3,:3] = np.array([[np.cos(angle),0,-np.sin(angle)],[0,1,0],[np.sin(angle),0,np.cos(angle)]])
	elif axis == 2:
		R[:3,:3] = np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])	
	else:
		raise AxisOutOfBoundsError
	M = T@R@Ti
	return M