__all__ = ['Image2d']

class Image2d:
	def __init__(self):
		# Array data for image.
		self.pixelArray = None
		# Extent of image, BT-LR-FB.
		self.extent = None
		# Patient isocenter within image, assumes single isoc.
		self.patientIsocenter = None
		# Patient position at the time of the image.
		self.patientPosition = None
		# Image view.
		self.view = {
			'title':'None',
			'xLabel':'None',
			'yLabel':'None',
		}
		# Transform for getting into and out of the image frame of reference.
		self.M = None
		self.Mi = None

	def forIn(self,points):
		pass

	def forOut(self,points):
		pass

# class image3d:
# 	def __init__(self):
# 		super()
# 		self.orientation = None
# 		self.fp = None
# 		self.ds = None
# 		'''
# 		FOR RTPLANS
# 		'''
# 		# Mask Options
# 		self.mask = None
# 		self.maskThickness = None
# 		# Rotation options
# 		self.collimator = None
# 		self.gantry = None
# 		self.patientSupport = None
# 		# Support mutiple views of the image?
# 		self.views = None