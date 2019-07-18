''' 
3x3 transformation matrices.
With no parameters passed the default is to return a diagonal matrix.

Uses:
	translation(x,y,z)
	rotation(x,y,z)
	offset(x,y,z)

Modes:
	0	no transform
	1	translation only
	2	rotation only
	3	translation and rotation
	4	translation, rotation and offset
'''
import numpy as np

# class motor:
# 	def __init__(self):
# 		self.axis = 0, 1 or 2 for x y or z
# 		self.range = [-10,20]
# 		self.type = 'r' or 't'
# 		self.transform = transformationMatrix()
# 		self.pv = pv base
# 		self.ui = user interface object

class transformationMatrix:
	def __init__(self,translation=False,rotation=False,rotationOffset=False):
		M = np.identity(4)
		if translation:
			T = self._translation(translation)
			M = M@T
		if rotation & (not rotationOffset): 
			R = self._rotation(rotation)
			M = M@R
		elif rotation & rotationOffset:
			R = self._rotation(rotation)
			Rt = self._translation(translation)
			Rti = self._inverseTranslation(translation)
			M = Rt@R@Rti

		# Return matrix, M.
		return M

	def _translation(self,translation):
		# translation = tuple of length 3 for x, y and z.
		T = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[translation[0],translation[1],translation[2],1]])
		return T

	# def _rotation(self):
	# 	return R

	# def _inverseTranslation(self):
	# 	return Ti

	# def _rotationOffset(self):
	# 	pass