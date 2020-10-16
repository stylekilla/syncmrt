class markers:
	""" Marker settings for fiducials. """
	quantity = 3
	size = 2.00
 
class files:
	""" Relative file locations. """
	patientSupports = '/database/patientSupports.csv'
	detectors = '/database/detectors.csv'

class imager:
	""" Settings for the imager configuration. """
	# Pixel size and isocenter specified as (row,col).
	isocenter = [2160/2,2560/2]
	# Pixel size is SAX/SID which is 1.2m / 1.5m.
	pixelSize = [0.0182,0.0182]
	sad = 1.2
	sid = 1.5 
	# magnification = sad/sid
	# pixelSize = [0.2,0.2]*magnification