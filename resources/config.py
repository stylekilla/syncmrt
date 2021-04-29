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
	# Does the detector image need to be flipped?
	flipud = True
	fliplr = False
	roi = [0,1,0,1]
	# Pixel size is SAX/SID which is 1.2m / 1.5m.
	sad = 1.2
	sid = 1.5 
	magnification = sad/sid
	# Pixel size and isocenter specified as (row,col).
	pixelSize = [0.1*magnification,0.1*magnification]
	isocenter = [985.531,544.469]