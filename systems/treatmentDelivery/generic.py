class GenericBeamSequence:
	def __init__(self):
		""" A generic beam sequence for treatment delivery. """
		self.beams = []

	def addBeam(self,beam):
		""" Add a beam to the beam sequence. """
		if type(beam) is GenericBeam:
			self.beams.append(beam)

	def isDelivered(self):
		""" Return a list of delivery statuses for the beams in the sequence. """
		return [beam.delivered for beam in self.beams]

class GenericBeam:
	def __init__(self,speed,zRange,port=[0,0,0,0,0,0]):
		""" A generic beam for a beam sequence. """
		# Is the beam delivered?
		self.delivered = False
		# The speed at which to travel during the irradiation.
		self.speed = float(speed)
		# The distance in which to travel during the irradiation.
		self.zRange = tuple(zRange)
		# Specify the port location in which to deliver the beam.
		self.port = port
		# The mask shape in which to deliver.
		self.maskShape = None
		# Beam properties.
		# Filtration.
		self.quality = [None,None]
		# Field strength.
		self.fieldStrength = 4

	def setMask(self,mask):
		""" Set the desired mask. """
		# Should be a list of xy points or a binary mask image.
		raise Error("Not implemented yet.")

	def setDelivered(self):
		""" Set the beam status to delivered. """
		self.delivered = True