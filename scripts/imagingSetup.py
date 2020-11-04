import epics
import logging

# HHL (Primary)
# Slits1A = epics.PV('SR08ID01SLW01:VPOS.VAL')
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
# Zorro position.
Zorro = epics.PV('SR08ID01ZORRO:LARGE_Z.VAL')
# MRTShutter.
# MRTShutter = epics.PV('SR08ID01SST21:YTrans.VAL')

# List of commands.
logging.info("Moving to imaging setup.")
logging.info("Moving slits.")
# Slits1B.put(20.00)
# Slits2A.put(20.00)
# Slits3B.put(20.00)
logging.info("Moving Ruby.")
RubyTranslation.put(42.125)
logging.info("Moving Zorro.")
Zorro.put(-200.0)
logging.info("Moving Mono.")
Mono.put(0.00,wait=True)
logging.info("Done...?")

# def goToWhite():
# 	"""
# 	Moves all the slits back down to 0.00 mm level.
# 	Moves RUBY out of the beam (in -Y direction).
# 	Moves the mono out of the beam.
# 	"""
# 	Slits1B.put(0.00)
# 	Slits2A.put(0.00)
# 	Slits3B.put(0.00)
# 	RubyTranslation.put(-15.00)
# 	Mono.put(-45.00)
# 	MRTShutter.put(-300)