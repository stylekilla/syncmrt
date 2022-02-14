
class beam:
	""" A beam to deliver. """
	def __init__(self,uid,velocity,port):
		"""
		A beam descriptor. Belongs in a beam sequence.

		Inputs
		------
		uid: uuid.uuid1() 
			A unique identifier for the beam.
		velocity: float
			The velocity in which to travel.
		port: [float,float,float,float,float,float]
			A 6D float vector representing the port vector in the format [x,y,z,rx,ry,rz].
		"""
		self.uid = uid
		self.velocity = velocity
		self.port = port