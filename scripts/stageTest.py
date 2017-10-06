import numpy as np

'''
transform.py
'''
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

'''
INPUTS
'''
# Q = some quaternion that is the solution.
Q = np.identity(4)
# solution = [0,0,0,0,0,0]
solution = [0,10,5,10,0,90]
# Working distance from object
wdfo = 100

'''
STAGE SETUP
'''
# M is made up of LargeZ, LargeY, TiltX, TiltY, RotZ, SampleX, SampleY
M1 = translation(2,solution[2])
# M2 = translation(1,solution[1])
M2 = translation(1,0)
M3 = rotation(0,solution[3],(0,0,wdfo))
M4 = rotation(1,solution[4],(0,0,wdfo))
M5 = rotation(2,solution[5],(0,0,0))
M6 = translation(0,solution[0])
M7 = translation(1,solution[1])
M = (M1,M2,M3,M4,M5,M6,M7)

'''
WORK
'''
Mtotal = np.identity(4)
for m in M:
	Mtotal = Mtotal@m


'''
OUTPUTS
'''
print('Q:')
print(np.around(Q,3))
print('M:')
print(np.around(Mtotal,3))
print('Difference:')
diff = Q-Mtotal
print(np.around(diff,3))