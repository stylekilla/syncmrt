import numpy as np

class settings():
	def __init__(self):
		self.markerQuantity = 3
		self.markerSize = 2.00

		self.chairOrientation = '-ap-hf'

		self.hamamatsuPixelSize = 0.2/1.24
		self.hamamatsuAlignmentIsoc = np.array([107.9032,107.9032,79.3548])