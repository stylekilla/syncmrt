import numpy as np

class globalVariables():
	def __init__(self):
		self.markerQuantity = 3
		self.markerSize = 2.00

		self.chairOrientation = '-ap-hf'

		self.hamamatsuPixelSize = 0.16145
		self.hamamatsuAlignmentIsoc = np.array([566.5,213.5,566.5])
		# self.hamamatsuPixelSize = 0.0208
		# self.hamamatsuAlignmentIsoc = np.array([1165,89,1165])

		# rename to imagingIsoc?