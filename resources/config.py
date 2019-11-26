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
	isocenter = [232.9,579.625]
	# Pixel size is SAX/SID which is 1.2m / 1.5m.
	pixelSize = [0.16,0.16]
	sad = 1.2
	sid = 1.5 
	# magnification = sad/sid
	# pixelSize = [0.2,0.2]*magnification