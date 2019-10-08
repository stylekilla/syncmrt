class markers:
	""" Marker settings for fiducials. """
	quantity = 4
	size = 2.00
 
class files:
	""" Relative file locations. """
	patientSupports = '/database/patientSupports.csv'
	detectors = '/database/detectors.csv'

class imager:
	""" Settings for the imager configuration. """
	# Pixel size and isocenter specified as (row,col).
	isocenter = [232.5,578.5]
	pixelSize = [0.16,0.16]
	sad = 0
	sid = 0