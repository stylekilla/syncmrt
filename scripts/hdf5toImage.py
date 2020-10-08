import numpy as np
import h5py as h5
import imageio
import os
import logging

def exportToImages(hdf5file,outputFormat):
	# Grab the directory and name of the specified HDF5 file.
	fileDirectory,fileName = os.path.split(hdf5file)
	# Load the HDF5 file as read only.
	logging.info("Opening file: {}".format(fileName))
	f = h5.File(hdf5file,'r')
	# Iterate over all the image pairs.
	for imagePair in f['Image']:
		for image in f['Image'][imagePair]:
			fn = "{}_{}-{}{}".format(fileName[:-5],imagePair,image,outputFormat)
			# Write the image.
			imageio.imwrite(
				os.path.join(fileDirectory,fn),
				f['Image'][imagePair][image],
				outputFormat
			)


# USER OPTIONS:
# Specify either a filename (single file) or a folder to iterate over. Leave the other as None.
fileName = '/Users/barnesmicah/Documents/dumpingGround/CT_Xray_pair_for_Micah/A2.hdf5'
folder = None
# Image type to save.
outputFormat = '.jpg'

# SCRIPT START:
if (fileName is not None) and (folder is None): 
	# Export a single file.
	exportToImages(fileName,outputFormat)
elif (folder is not None) and (fileName is None):
	# Export all files in a folder.
	for root,dirs,files in os.walk(folder):
		for file in files:
			if file.endswith('.hdf5'):
				exportToImages(os.join(root,file),outputFormat)
else:
	raise Exception("Could not process data whilst either both the fileName and folder are set/unset. Ensure that either one or the either is set, not both.")
