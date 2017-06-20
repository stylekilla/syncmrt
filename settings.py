import numpy as np

class globalVariables():
	def __init__(self):
		self.markerQuantity = 3
		self.markerSize = 2.00

		self.chairOrientation = '-ap-hf'

		self.hamamatsuPixelSize = 0.16145
		self.hamamatsuImageSize = np.array([1216,616])
		self.hamamatsuAlignmentIsoc = np.array([637.5,238.5,637.5])

		# rename to imagingIsoc?