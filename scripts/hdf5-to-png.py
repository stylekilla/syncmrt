# General imports.
import os
from file import importer,exporter
# Colored logs.
import logging, coloredlogs
coloredlogs.install(
	fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
	datefmt='%H:%M:%S',
	level=logging.INFO
	)


folder = '/Users/micahbarnes/OneDrive/Scratch/archive/'
logging.info("Searching {} for files.".format(folder))
for root, subdir, fp in os.walk(folder):
	logging.info("Checking {} for files.".format(subdir))
	for fn in fp:
		if fn.endswith(tuple('.hdf5')):
			logging.info("Found {}.".format(os.path.join(root,fn)))
			# Load the images.
			_file = importer.sync_dx(os.path.join(root,fn),new=False)
			# Convert the images.
			exporter.xrayImages(_file)