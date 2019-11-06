# 50 micron pixel size
pixelsize = 0.05
# 20cm high object
height = 200
# field size mm (w x h) set by the slits
fieldsize = [100,10] 
# fieldsize = [100,0.1] 
# Final Image size in pixels.
imageheight = height/pixelsize
imagewidth = 100/pixelsize
imagesize = [imagewidth,imageheight]
# exposure time
exposuretime = 0.03
gst = 1.1
# acquire time
acquiretime = exposuretime * gst
# calc stage speed
stagespeed = pixelsize/acquiretime

