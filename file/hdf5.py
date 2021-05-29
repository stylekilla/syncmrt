import h5py as h5
from datetime import datetime as dt
import logging

_xrayImageAttributes = [
		"Date",
		"Time",
		"datetime",
		"Comment",
		"PatientSupport",
		"PatientSupportAngle",
		"PatientSupportPosition",
		"Detector",
		"ImageSize",
		"PixelSize",
		"ROI",
		"AcquisitionTime",
		"AcquisitionPeriod",
		"WigglerField",
		"Filtration",
		"Mode",
		"BeamEnergy",
		"FieldSize",
		"M",
		"Mi",
	]

def new(fp):
	logging.info("Creating {}".format(fp))
	f = file(fp,'w') #: Create a new HDF5 file.
	#: Set the file up.
	f.create_group('Patient') 
	f.create_group('Image')
	# Save it.
	f.flush()
	#: Return the file.
	return f

# Load a HDF5 file.
def load(fp):
	logging.info("Loading {}".format(fp))
	return file(fp,'a')

class file(h5.File):
	""" A reclass of the H5Py module. Added specific functionality for reading and writing image sets. """
	def __init__(self,fp,mode,*args,**kwargs):
		super().__init__(fp,mode,*args,**kwargs)

	def getImageSet(self,index=-1):
		logging.debug("Reading image set {}.".format(index))
		if index == -1:
			index = len(self['Image'])
		try:
			return self['Image'][str(index).zfill(2)]
		except:
			return []

	def addImageSet(self,images,metadata={}):
		setName = str(len(self['Image'])+1).zfill(2)
		numImages = len(images)
		logging.debug(f"Writing {setName} containing {numImages} images to HDF5 file {self}.")
		# Create the group set.
		newSet = self['Image'].create_group(setName)
		# Write the metadata for the image set (if any).
		for key,val in metadata.items():
			newSet.attrs[key] = val
		# Add the images to the set one by one.
		for i in range(numImages):
			image = newSet.create_dataset(str(i+1),data=images[i][0])
			# Add the image attributes (metadata).
			for key, val in images[i][1].items():
				image.attrs[key] = val
		# Write changes to disk.
		self.flush()
		return setName, numImages