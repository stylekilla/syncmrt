import epics

# HHL (Primary)
Slits1A = epics.PV('SR08ID01SLW01:VPOS.VAL')
# Baby Bear
Slits1B = epics.PV('SR08ID01SLM12:VCENTRE.VAL')
# Mama Bear
Slits2A = epics.PV('SR08ID01TBL21:Z.VAL')
# Papa Bear
Slits3B = epics.PV('SR08ID01SLM03:ZCENTRE.VAL')
# Ruby position.
RubyTranslation = epics.PV('SR08ID01DST31:Y.VAL')
# Mono position.
Mono = epics.PV('SR08ID01DCM01:Z1.VAL')
# MRTShutter.
MRTShutter = epics.PV('SR08ID01SST21:YTrans.VAL')

"""
Things to add:
- LAPS movement offset.
"""

def goToMono():
	"""
	Moves all the slits up to 20.00 mm level.
	Moves RUBY into the beam (in +Y direction).
	Moves the mono into the beam.
	"""
	Slits1B.put(20.00)
	Slits2A.put(20.00)
	Slits3B.put(20.00)
	RubyTranslation.put(732.00)
	Mono.put(0.00)
	MRTShutter.put(0)

def goToWhite():
	"""
	Moves all the slits back down to 0.00 mm level.
	Moves RUBY out of the beam (in -Y direction).
	Moves the mono out of the beam.
	"""
	Slits1B.put(0.00)
	Slits2A.put(0.00)
	Slits3B.put(0.00)
	RubyTranslation.put(-15.00)
	Mono.put(-45.00)
	MRTShutter.put(-300)