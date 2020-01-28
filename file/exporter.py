# General imports.
import os, io
from pathlib import Path
from file.importer import sync_dx
import imageio
import numpy as np
# Plotting tools.
import matplotlib as mpl
mpl.use('Qt5Agg')
mpl.rcParams['toolbar'] = 'toolmanager'
mpl.rcParams['datapath'] = './QsWidgets/QsMpl/mpl-data'
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, FigureManagerQT
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
# Other.
import logging

def mm2inch(*tupl):
	inch = 25.4
	if isinstance(tupl[0], tuple):
		return tuple(i/inch for i in tupl[0])
	else:
		return tuple(i/inch for i in tupl)

def xrayImages(file):
	""" Given a HDF5 file (currently open with h5py), export all the images. """
	logging.info(file)
	# Get the file name of the dataset.
	fp = Path(file.file.filename)
	fp_base = fp.parent
	fn_base = fp.stem
	# Get the image list from the HDF5 file.
	imageList = file.getImageList()
	if imageList is None:
		return
	else:
		logging.info("Exporting images {}.".format(imageList))
		# Iterate over the image list.
		for key in imageList:
			# Get the image set.
			_set = file.getImageSet(int(key))
			logging.info("Set number {} contains {} images".format(int(key),len(_set)))
			for i in range(len(_set)):
				# Get the image.
				array = _set[i].pixelArray
				imageExtent = _set[i].extent
				maskSize = 7
				sizex = np.absolute(imageExtent[0])+np.absolute(imageExtent[1])
				sizey = np.absolute(imageExtent[2])+np.absolute(imageExtent[3])
				# Create a blank figure/canvas.
				fig = plt.figure(figsize=mm2inch(sizex, sizey), dpi=300)
				canvas = FigureCanvasQTAgg(fig)
				# Add some axes.
				ax = fig.add_axes([0,0,1,1])
				ax.set_axis_off()
				# Plot the image.
				ax.imshow(array,extent=imageExtent,cmap='gray')
				# Create the beam patch.
				beam = Rectangle((-maskSize/2,-maskSize/2), maskSize, maskSize,fc='r',ec='none',alpha=0.2)
				# Make the patch collection.
				patches = PatchCollection([beam],match_original=True)
				# Add the patch collection.
				ax.add_collection(patches)
				# Save the canvas to a buffer.
				buf = io.BytesIO()
				fig.savefig(buf, format='png')
				buf.seek(0)
				# Create a file name for the image.
				image_fn = os.path.join(fp_base, fn_base + key + '_' + str(i).zfill(2) + '.png')
				# Save the image.
				logging.info("Saving {}".format(image_fn))
				with open(image_fn,'wb') as outputFile:
					outputFile.write(buf.read())