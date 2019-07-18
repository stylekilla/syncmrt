import os
import pydicom as dicom
import numpy as np
from file.image import Image2d
from file import hdf5
from tools.opencl import gpu as gpuInterface
from tools.math import wcs2wcs
from natsort import natsorted
import logging

np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

'''
The importer class takes DICOM/HDF5 images and turns them into a
	class (image2d or image3d) for plotting in QsWidgets.QPlot().
	This is where we disconnect the DICOM information and take
	only what the internals of SyncMRT requires to operate. Maybe
	in the future such integrations could just see the use of
	DICOM throughout but then things would have to be re-written
	to understand DICOM. This is just currently my own interface.
Think of this class as the interface to QPlot. As such it should
	probably be packaged with it.
'''

class sync_dx:
	def __init__(self,dataset,new=False):
		# Read in hdf5 dataset.
		if new:
			self.file = hdf5.new(dataset)
		else:
			self.file = hdf5.load(dataset)
			
	def getImageList(self):
		""" Reads the image names in the HDF5 file. Return as list. """
		return list(self.file['Image'].keys())

	def getImageSet(self,idx):
		logging.debug("Reading image set {}.".format(idx))
		_set = self.file.getImageSet(idx)
		imageSet = []
		try:
			for i in range(len(_set)):
				# Get the image and its attributes.
				image = Image2d()
				image.pixelArray = _set[str(i+1)][()]
				image.extent = _set[str(i+1)].attrs['Extent']
				image.patientIsocenter = _set[str(i+1)].attrs['Image Isocenter']
				image.patientPosition = list(_set[str(i+1)].attrs['Patient Support Position']) + list(_set[str(i+1)].attrs['Patient Support Angle'])
				image.view['title'] = str(_set[str(i+1)].attrs['Image Angle'])+"\u00B0"
				image.M = _set[str(i+1)].attrs['M']
				image.Mi = _set[str(i+1)].attrs['Mi']
				# Append the image.
				imageSet.append(image)
		except:
			logging.critical("Unable to load image set. Most likely does not contain the correct attributes.")
			
		return imageSet


def checkDicomModality(dataset,modality):
	""" Check the modality of each dicom file and return only the files that match the desired modality. """
	# Start with empty list of files.
	files = {}
	for i in range(len(dataset)):
		# Read the file in.
		testFile = dicom.dcmread(dataset[i])
		if testFile.Modality == modality:
			# Save in dict where the key is the slice position.
			files[int(testFile.SliceLocation)] = dataset[i]
		else:
			pass

	# Sort the files based on slice location.
	sortedFiles = []
	for key in sorted(files.keys()):
		sortedFiles.append(files[key])

	# Return the sorted file list.
	return sortedFiles

class dicom_ct:
	def __init__(self,dataset,gpu):
		self.fp = os.path.dirname(dataset[0])
		# Are we reading in a CT DICOM file?
		dataset = checkDicomModality(dataset,'CT')
		ref = dicom.dcmread(dataset[0])
		# Get CT shape.
		shape = np.array([int(ref.Columns), int(ref.Rows), len(dataset)])
		# Initialize image with array of zeros.
		self.pixelArray = np.zeros(shape, dtype=np.int32)
		# Read array in one slice at a time.
		for fn in dataset:
			slice = dicom.dcmread(fn)
			self.pixelArray[:,:,dataset.index(fn)] = slice.pixel_array
			# self.pixelArray[:,:,shape[2]-dataset.index(fn)-1] = slice.pixel_array
			# Should send signal of import status here.
			# pct = dataset.index(fn)/len(dataset)
			# progress.emit(pct)
		# Rescale the Hounsfield Units.
		self.pixelArray = (self.pixelArray*ref.RescaleSlope) + ref.RescaleIntercept

		# '''
		# Map the DICOM CS (RCS) to the python CS (WCS):
		# '''
		# Get current CT orientation.
		self.patientPosition = ref.PatientPosition
		# Machine coordinates defined here:
		# http://dicom.nema.org/medical/Dicom/2016c/output/chtml/part03/sect_C.8.8.25.6.html
		dcmAxes =  np.array(list(map(float,ref.ImageOrientationPatient)))
		x = dcmAxes[:3]
		y = dcmAxes[3:6]
		z = np.cross(x,y)
		self.orientation = np.vstack((x,y,z))
		self.RCS = np.vstack((x,y,z))
		z1 = list(map(float,ref.ImagePositionPatient))[2]
		z2 = list(map(float,dicom.dcmread(dataset[-1]).ImagePositionPatient))[2]
		spacingBetweenSlices = (z2-z1)/len(dataset)
		# Get vars for transform.
		self.pixelSize = np.append(np.array(list(map(float,ref.PixelSpacing))),spacingBetweenSlices)
		self.leftTopFront = np.array(list(map(float,ref.ImagePositionPatient)))
		# Calculate Extent.
		self.extent, self.labels = calculateNewImageInformation(self.patientPosition,self.RCS,shape,self.pixelSize,self.leftTopFront)
		# Load array onto GPU for future reference.
		gpu.loadData(self.pixelArray)

		# Create a 2d image list for plotting.
		self.image = [Image2d(),Image2d()]
		# Flatten the 3d image to the two 2d images.
		# Extent: [left, right, bottom, top, front, back]
		self.image[0].pixelArray = np.sum(self.pixelArray,axis=2)
		self.image[0].extent = np.array([self.extent[0],self.extent[1],self.extent[2],self.extent[3]])
		self.image[0].view = { 'title':self.labels[2], 'xLabel': self.labels[1], 'yLabel': self.labels[0] }
		self.image[1].pixelArray = np.sum(self.pixelArray,axis=1)
		self.image[1].extent = np.array([ self.extent[4], self.extent[5], self.extent[2], self.extent[3] ])
		self.image[1].view = { 'title':self.labels[1], 'xLabel': self.labels[2], 'yLabel': self.labels[0] }

		# Save and write fp and ds.
		# np.save(self.fp+'/dicom_ct.npy',self.pixelArray)
		# self.ds = [self.fp+'/dicom_ct.npy']
		self.fp = os.path.dirname(self.fp)

class beamClass:
	def __init__(self):
		self.image = None
		self.mask = None
		self.maskThickness = None
		self.gantry = None
		self.patientSupport = None
		self.collimator = None
		self.pitch = None
		self.roll = None
		self.isocenter = None
		self.BCS = None
		self._arr2bcs = None
		self._dcm2bcs = None

class dicom_rtplan:
	def __init__(self,dataset,rcs,rcsLeftTopFront,ctArrayShape,ctArrayPixelSize,ctPatientPosition,gpuContext):
		# BCS: Beam Coordinate System (Linac)
		# RCS: Reference Coordinate System (Patient)
		# Conversion of dicom coordinates to python coordinates.
		dcm2python = np.array([[0,1,0],[1,0,0],[0,0,1]])
		# Firstly, read in DICOM rtplan file.
		ref = dicom.dcmread(dataset[0])
		# Set file path.
		self.fp = os.path.dirname(dataset[0])
		# Construct an object array of the amount of beams to be delivered.
		self.beam = np.empty(ref.FractionGroupSequence[0].NumberOfBeams,dtype=object)
		self.isocenter = dcm2python@np.array(list(map(float,ref.BeamSequence[0].ControlPointSequence[0].IsocenterPosition)))

		# Extract confromal mask data.
		for i in range(len(self.beam)):
			self.beam[i] = beamClass()
			# If a block is specified for the MLC then get it.
			if ref.BeamSequence[0].NumberOfBlocks > 0:
				temp = np.array(list(map(float,ref.BeamSequence[i].BlockSequence[0].BlockData)))
				class _data:
					x = np.append(temp[0::2],temp[0])
					y = np.append(temp[1::2],temp[1])
				self.beam[i].mask = _data
				self.beam[i].maskThickness = ref.BeamSequence[i].BlockSequence[0].BlockThickness
			# Get the jaws position for backup.
			# Get the machine positions.
			self.beam[i].gantry = float(ref.BeamSequence[i].ControlPointSequence[0].GantryAngle)
			self.beam[i].patientSupport = float(ref.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			self.beam[i].collimator = float(ref.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)
			self.beam[i].pitch = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
			self.beam[i].roll = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)

			# Rotate everything in the RCS frame to match the bed position.
			cs_bed = rotate_cs(np.identity(3),[self.beam[i].pitch],['y'])
			cs_bed = rotate_cs(cs_bed,[self.beam[i].roll],['z'])
			cs_bed = rotate_cs(cs_bed,[-self.beam[i].patientSupport],['x'])
			# Bring the patient RCS into the beam view.
			cs_machine = rotate_cs(cs_bed,[90],['y'])
			# Rotate the bed position to match the machine position.
			bcs = rotate_cs(cs_machine,[-self.beam[i].collimator,-self.beam[i].gantry],['z','x'])
			self.beam[i]._arr2bcs = (bcs)
			self.beam[i].BCS = (bcs)
			self.beam[i].isocenter = np.absolute(bcs)@self.isocenter
			# Rotate the dataset.
			pixelArray = gpuContext.rotate(self.beam[i]._arr2bcs)
			# Create the 2d projection images.
			self.beam[i].image = [image2d(),image2d()]
			# Get the relevant information for the new image.
			pixelSize = bcs@dcm2python@ctArrayPixelSize
			arrayShape = np.array(pixelArray.shape)
			extent, labels = calculateNewImageInformation(ctPatientPosition,bcs,arrayShape,pixelSize,rcsLeftTopFront)
			# Flatten the 3d image to the two 2d images.
			self.beam[i].image[0].pixelArray = np.sum(pixelArray,axis=2)
			self.beam[i].image[0].extent = np.array([extent[0],extent[1],extent[2],extent[3]])
			self.beam[i].image[0].view = { 'title':labels[2], 'xLabel':labels[0], 'yLabel':labels[1] }
			self.beam[i].image[1].pixelArray = np.sum(pixelArray,axis=1)
			self.beam[i].image[1].extent = np.array([ extent[4], extent[5], extent[2], extent[3] ])
			self.beam[i].image[1].view = { 'title':labels[0], 'xLabel':labels[2], 'yLabel':labels[1] }

def rotate_cs(cs,theta,axis):
	# Put angles into radians.
	rotations = []
	for i in range(len(theta)):
		t = np.deg2rad(theta[i])
		if axis[i] == 'x': r = np.array([[1,0,0],[0,np.cos(t),-np.sin(t)],[0,np.sin(t),np.cos(t)]])
		elif axis[i] == 'y': r = np.array([[np.cos(t),0,np.sin(t)],[0,1,0],[-np.sin(t),0,np.cos(t)]])
		elif axis[i] == 'z': r = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		rotations.append(r)

	# Calculate out the combined rotations.
	m = np.identity(3)
	for i in range(len(rotations)):
		m = m@rotations[-(i+1)]

	rotated_cs = np.zeros(cs.shape)
	# Rotate coordinate system.
	for i in range(3):
		rotated_cs[i] = m@np.transpose(cs[i])

	return rotated_cs

def calculateNewImageInformation(patientPosition,cs,arraySize,pixelSize,leftTopFront):
	# Find which python axes the dicom axes are maximised in.
	magnitudes = np.argmax(np.absolute(cs),axis=0)
	sx = np.sign(cs[:,0][magnitudes[0]])
	sy = np.sign(cs[:,1][magnitudes[1]])
	sz = np.sign(cs[:,2][magnitudes[2]])
	signs = np.array([sx,sy,sz])

	# Set the labels for the patient position.
	rcsLabels = np.array(['?','?','?','?','?','?'])
	if patientPosition == 'HFS': rcsLabels = np.array(['P','A','R','L','I','S'])
	elif patientPosition == 'HFP': rcsLabels = np.array(['A','P','R','L','I','S'])
	elif patientPosition == 'FFS': rcsLabels = np.array(['P','A','L','R','S','I'])
	elif patientPosition == 'FFP': rcsLabels = np.array(['A','P','L','R','S','I'])

	# If magnitudes[0] = 0, then this is the DCM X axis mapped onto the python X axis.
	# DCM X Axis = Right to Left (- to +).
	# DCM Input for TLF corner is always assigned to (-x,-y,-z), otherwise described as (-0,-1,-2).
	# The extent is then that corner + the pixelsize * arraysize * direction (from R to L, T to B, F to B).
	for i in range(len(magnitudes)):
		if magnitudes[i] == 0:
			if signs[i] == +1: 
				xAxis = str(rcsLabels[0]+rcsLabels[1])
				top = leftTopFront[0]
				bottom = top + (pixelSize[0]*arraySize[0]*signs[i])
			elif signs[i] == -1:
				xAxis = str(rcsLabels[1]+rcsLabels[0])
				bottom = leftTopFront[0]
				top = bottom + (pixelSize[0]*arraySize[0]*signs[i])
		elif magnitudes[i] == 1:
			if signs[i] == +1:
				yAxis = str(rcsLabels[2]+rcsLabels[3])
				left = leftTopFront[1]
				right = left + (pixelSize[1]*arraySize[1]*signs[i])
			elif signs[i] == -1:
				yAxis = str(rcsLabels[3]+rcsLabels[2])
				right = leftTopFront[1]
				left = right + (pixelSize[1]*arraySize[1]*signs[i])
		elif magnitudes[i] == 2:
			if signs[i] == +1:
				zAxis = str(rcsLabels[4]+rcsLabels[5])
				front = leftTopFront[2]
				back = front + (pixelSize[2]*arraySize[2]*signs[i])
			elif signs[i] == -1:
				zAxis = str(rcsLabels[5]+rcsLabels[4])
				back = leftTopFront[2]
				front = back + (pixelSize[2]*arraySize[2]*signs[i])

	extent = np.array([left,right,bottom,top,front,back])
	labels = np.array([xAxis,yAxis,zAxis])

	return extent, labels