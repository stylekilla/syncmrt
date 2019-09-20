from file import importer
from file import hdf5
from tools.opencl import gpu
from PyQt5 import QtCore
import logging

class Patient(QtCore.QObject):
	"""
	This holds information about the patient. Files, datasets, gpu context, imported dicom information etc.
	"""
	newDXfile = QtCore.pyqtSignal(str)

	def __init__(self,name='Default'):
		super().__init__()
		self.name = name
		self.dx = None
		self.ct = None
		self.rtplan = None
		# Program internals.
		self._gpuContext = None

	def load(self,dataset,modality):
		""" Load Patient Data. """
		logging.info("Loading {} with {} files.".format(modality,len(dataset)))
		if modality == 'DX': 
			# Close the open one first.
			if self.dx != None: 
				self.dx.file.close()
			# Now open the dataset.
			self.dx = importer.sync_dx(dataset)
			self.newDXfile.emit(dataset)

		elif modality == 'CT': 
			# Create a GPU context for the ct array.
			self._gpuContext = gpu()
			self.ct = importer.dicom_ct(dataset,self._gpuContext)
			
		elif modality == 'RTPLAN': 
			if self.ct != None: 
				self.rtplan = importer.dicom_rtplan(
						dataset,
						self.ct,
						self._gpuContext
					)
			else: 
				logging.critical('No CT Dataset loaded. Cannot import treatment plan.')
		else: logging.critical('No importer for file type: ',modality)

	def new(self,fp,modality):
		""" Create a new HDF5 file for x-ray data. """
		if modality == 'DX':
			if self.dx != None:
				self.dx.file.close()
			self.dx = importer.sync_dx(fp,new=True)
			self.newDXfile.emit(fp)