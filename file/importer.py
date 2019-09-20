import os
import pydicom as dicom
import numpy as np
from file.image import Image2d
from file import hdf5
from tools.opencl import gpu as gpuInterface
from tools.math import wcs2wcs
from natsort import natsorted
from PyQt5 import QtCore
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
				image.imagingAngle = _set[str(i+1)].attrs['Image Angle']
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
			# files[int(testFile.SliceLocation)] = dataset[i]
			files[list(map(float,testFile.ImagePositionPatient))[2]] = dataset[i]
		else:
			pass

	# Sort the files based on slice location.
	sortedFiles = []
	for key in sorted(files.keys()):
		sortedFiles.append(files[key])

	# Return the sorted file list.
	return sortedFiles

class dicom_ct(QtCore.QObject):
	# Qt signals.
	newCtView = QtCore.pyqtSignal()

	def __init__(self,dataset,gpu):
		# Init QObject class.
		super().__init__()
		self.fp = os.path.dirname(dataset[0])
		# Are we reading in a CT DICOM file?
		dataset = checkDicomModality(dataset,'CT')
		ref = dicom.dcmread(dataset[0])
		# Get CT shape.
		shape = np.array([int(ref.Rows), int(ref.Columns), len(dataset)])
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

		# Get current CT orientation.
		self.patientPosition = ref.PatientPosition
		# Machine coordinates defined here:
		# http://dicom.nema.org/medical/Dicom/2016c/output/chtml/part03/sect_C.8.8.25.6.html
		# Base coordinate system.
		self.BCS = np.identity(3)
		# Python coordinate system.
		self.PCS = np.array([[0,1,0],[1,0,0],[0,0,1]])
		# Patient coordinate system.
		dcmAxes =  np.array(list(map(float,ref.ImageOrientationPatient)))
		x = dcmAxes[:3]
		y = dcmAxes[3:6]
		z = np.cross(x,y)
		self.RCS = np.vstack((x,y,z))
		# Get the pixel size.
		z1 = list(map(float,ref.ImagePositionPatient))[2]
		z2 = list(map(float,dicom.dcmread(dataset[-1]).ImagePositionPatient))[2]
		spacingBetweenSlices = (z2-z1)/len(dataset)
		self.pixelSize = np.append(np.array(list(map(float,ref.PixelSpacing))),spacingBetweenSlices)
		# Top left front value (corner of voxel, NOT the centre as defined by the DICOM format).
		self.TLF = np.array(list(map(float,ref.ImagePositionPatient)))
		self.TLF +=  np.sign(self.TLF)*(self.pixelSize/2)
		# Get the top left front and bottom right back voxels for caclualting extent.
		voxelIndex1 = np.array([0,0,0,1]).reshape((4,1))
		voxelIndex2 = np.array([shape[0],shape[1],shape[2],1]).reshape((4,1))
		# Construct the transformation matrix, M.
		self.M = np.zeros((4,4))
		self.M[:3,0] = self.pixelSize[0]*x
		self.M[:3,1] = self.pixelSize[1]*y
		self.M[:3,2] = self.pixelSize[2]*z
		self.M[:3,3] = self.TLF
		self.M[3,3] = 1
		# Compute the voxel indices in mm.
		voxelPosition1 = self.M@voxelIndex1
		voxelPosition2 = self.M@voxelIndex2

		# Store the bottom right back position.
		self.BRB = voxelPosition2[:3]

		# Calculate Extent.
		# self.extent, self.labels = calculateNewImageInformation(self.patientPosition,self.RCS,shape,self.pixelSize,self.leftTopFront
		# Extent is [L,R,B,T,F,B]
		_x = [voxelPosition1[0],voxelPosition2[0]]
		_y = [voxelPosition1[1],voxelPosition2[1]]
		_z = [voxelPosition1[2],voxelPosition2[2]]
		self.extent = np.array(_x+_y+_z).reshape((6,))

		# Load array onto GPU for future reference.
		gpu.loadData(self.pixelArray,extent=self.extent)

		# Create a 2d image list for plotting.
		self.image = [Image2d(),Image2d()]
		# Set the default.
		self.changeView('AP')

	def changeView(self,view,extent=None,flatteningMode='sum'):
		"""
		This only works for 90 deg rotations. (i.e. looking down various axes). This does not work for non-orthogonal rotations.
		View must be a code: AP, PA, SI, IS, LR, RL etc.
		"""
		default = np.array([[1,0,0],[0,1,0],[0,0,1]])
		si = np.array([[-1,0,0],[0,1,0],[0,0,-1]])
		lr = np.array([[0,0,1],[0,1,0],[-1,0,0]])
		rl = np.array([[0,0,-1],[0,1,0],[1,0,0]])
		ap = np.array([[1,0,0],[0,0,1],[0,-1,0]])
		pa = np.array([[-1,0,0],[0,0,-1],[0,-1,0]])

		# Assign matrix, m, to the view matrix.
		# if view == 0:
		# 	m = si
		# 	t1 = 'SI'
		# 	t2 = 'RL'
		# if view == 1:
		# 	m = default
		# 	t1 = 'IS'
		# 	t2 = 'LR'
		# if view == 2:
		# 	m = lr
		# 	t1 = 'LR'
		# 	t2 = 'SI'
		# if view == 3:
		# 	m = rl
		# 	t1 = 'RL'
		# 	t2 = 'IS'
		if view == 'AP':
			m = ap
			t1 = 'AP'
			t2 = 'LR'
		elif view == 'PA':
			m = pa
			t1 = 'PA'
			t2 = 'RL'


		# XYZ axes are assumed to align with the DICOM XYZ (in it's default HFS orientation). 
		# Axes for numpy sum are swapped for X and Y as the 0 python axis refers to rows (which is DICOM Y) and vice versa for X.

		# Calculate the transformation matrix, M, that takes CT position in indices to mm (and vice versa).
		Mi = np.linalg.inv(self.M)

		# Calculate the selected CT ROI in mm as array indices.
		# Use the original array extent if none is provided.
		if extent == None: extent = self.extent
		logging.critical("Extent: {}".format(extent))
		x1, x2, y1, y2, z1, z2 = extent
		# Get the two extreme vertices of the array as p1 and p2.
		p1 = np.array([x1,y1,z1,1])
		p2 = np.array([x2,y2,z2,1])
		# Convert them into index location.
		i1 = Mi@p1
		i2 = Mi@p2
		# Update the indices.
		x1, y1, z1, _ = i1.astype(int)
		x2, y2, z2, _ = i2.astype(int)
		logging.critical("P1: {} P2: {}".format(p1,p2))
		logging.critical("I1: {} I2: {}".format(i1.astype(int),i2.astype(int)))

		# Get new X axis.
		_x = np.absolute(m[0,:]).argmax()
		# Direction.
		_xd = int(np.sign(m[0,:][_x]))
		# Extent.
		_xe = [extent[0],extent[1]]
		if np.sign(_xd) == np.sign(-1): _xe = _xe[::-1]
		# Now assign the direction to what the new X (global) axis is.
		_xd = int(np.sign(m[:,0][_x]))

		# Get new Y axis.
		_y = np.absolute(m[1,:]).argmax()
		# Direction.
		_yd = int(np.sign(m[1,:][_y]))
		# Extent.
		_ye = [extent[2],extent[3]]
		if np.sign(_yd) == np.sign(-1): _ye = _ye[::-1]
		# Now assign the direction to what the new Y (global) axis is.
		_yd = int(np.sign(m[:,1][_y]))

		# Get new Z axis.
		_z = np.absolute(m[2,:]).argmax()
		# Direction.
		_zd = int(np.sign(m[2,:][_z]))
		# Extent.
		_ze = [extent[4],extent[5]]
		if np.sign(_zd) == np.sign(-1): _ze = _ze[::-1]
		# Now assign the direction to what the new Z (global) axis is.
		_zd = int(np.sign(m[:,2][_z]))

		# Get the axis to sum along (the new Z axis).
		if _z == 0: _sum1 = 1
		elif _z == 1: _sum1 = 0
		elif _z == 2: _sum1 = 2
		# Get the axis to sum along (the new X axis).
		if _x == 0: _sum2 = 1
		elif _x == 1: _sum2 = 0
		elif _x == 2: _sum2 = 2

		# Get the first flattened image.
		if flatteningMode == 'sum': self.image[0].pixelArray = np.sum(self.pixelArray[y1:y2,x1:x2,z1:z2],axis=_sum1)
		elif flatteningMode == 'max': self.image[0].pixelArray = np.amax(self.pixelArray[y1:y2,x1:x2,z1:z2],axis=_sum1)
		# If we sum down axis 0 we need to transpose the array, just because of numpy.
		if _sum1 == 0: self.image[0].pixelArray = np.flipud(np.transpose(self.image[0].pixelArray))
		elif _sum1 == 1: self.image[0].pixelArray = np.flipud(np.transpose(self.image[0].pixelArray))
		# If the axis direction is negative, we need to flip it from left to right.
		if np.sign(_zd) == np.sign(-1): self.image[0].pixelArray = np.fliplr(self.image[0].pixelArray)
		# The LR extent for the array comes from the axis along 0. The extents are also already ordered to match the direction of the axis.
		if _x == 0: _lr = _xe
		elif _y == 0: _lr = _ye
		elif _z == 0: _lr = _ze
		# The BT extent for the array comes from the axis along 1. The extents are also already ordered to match the direction of the DICOM axis (not the python axis).
		if _x == 1: _tb = _xe
		elif _y == 1: _tb = _ye
		elif _z == 1: _tb = _ze
		_bt = _tb[::-1]
		self.image[0].extent = np.array(_lr+_bt)
		self.image[0].view = { 'title':t1 }

		# Get the second flattened image.
		if flatteningMode == 'sum': self.image[1].pixelArray = np.sum(self.pixelArray[y1:y2,x1:x2,z1:z2],axis=_sum2)
		elif flatteningMode == 'max': self.image[1].pixelArray = np.amax(self.pixelArray[y1:y2,x1:x2,z1:z2],axis=_sum2)
		# If we sum down axis 0 we need to transpose the array, just because of numpy.
		if _sum2 == 0: self.image[1].pixelArray = np.flipud(np.transpose(self.image[1].pixelArray))
		elif _sum2 == 1: self.image[1].pixelArray = np.fliplr(np.flipud(np.transpose(self.image[1].pixelArray)))
		# If the axis direction is negative, we need to flip it from left to right.
		if np.sign(_xd) == np.sign(-1): self.image[1].pixelArray = np.fliplr(self.image[1].pixelArray)
		# The LR extent for the array comes from the axis along 2. The extents are also already ordered to match the direction of the axis.
		if _x == 2: _lr = _xe
		elif _y == 2: _lr = _ye
		elif _z == 2: _lr = _ze
		# The BT extent for the array comes from the axis along 1. The extents are also already ordered to match the direction of the DICOM axis (not the python axis).
		if _x == 1: _tb = _xe
		elif _y == 1: _tb = _ye
		elif _z == 1: _tb = _ze
		_bt = _tb[::-1]
		self.image[1].extent = np.array(_lr+_bt)
		self.image[1].view = { 'title':t2 }

		# Emit a signal to say a new view has been loaded.
		self.newCtView.emit()

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
	def __init__(self,rtplan,ct,gpu):
		"""
			BCS: Beam Coordinate System (Linac)
			RCS: Reference Coordinate System (Patient)
			PCS: Pyhon Coordinate System (DICOM to Python)
		"""
		self.PCS = np.array([[0,1,0],[1,0,0],[0,0,1]])

		# Firstly, read in DICOM rtplan file.
		ref = dicom.dcmread(rtplan[0])
		# Construct an object array of the amount of beams to be delivered.
		self.beam = np.empty(ref.FractionGroupSequence[0].NumberOfBeams,dtype=object)
		# Get the isocenter. Current only supports a single isocenter.
		self.isocenter = np.array(list(map(float,ref.BeamSequence[0].ControlPointSequence[0].IsocenterPosition)))

		logging.info("Isocenter (DICOM) {}".format(self.isocenter))
		self.isocenter = np.array(list(map(float,ref.BeamSequence[0].ControlPointSequence[0].IsocenterPosition)))

		for i in range(len(self.beam)):
			# Get the appropriate data for each beam.
			self.beam[i] = beamClass()

			# Extract confromal mask data.
			# If a block is specified for the MLC then get it.
			if ref.BeamSequence[0].NumberOfBlocks > 0:
				temp = np.array(list(map(float,ref.BeamSequence[i].BlockSequence[0].BlockData)))
				class Mask:
					x = np.append(temp[0::2],temp[0])
					y = np.append(temp[1::2],temp[1])
				self.beam[i].mask = Mask
				self.beam[i].maskThickness = ref.BeamSequence[i].BlockSequence[0].BlockThickness
			# Get the jaws position for backup.

			# Get the machine positions.
			self.beam[i].gantry = float(ref.BeamSequence[i].ControlPointSequence[0].GantryAngle)
			self.beam[i].patientSupport = float(ref.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			self.beam[i].collimator = float(ref.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)
			# Currently... these aren't available in treatment planning. Sad face.
			self.beam[i].pitch = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
			self.beam[i].roll = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)

			logging.info("Gantry Rotation: {}".format(self.beam[i].gantry))
			logging.info("Patient Support: {}".format(self.beam[i].patientSupport))
			logging.info("Collimator Rotation: {}".format(self.beam[i].collimator))

			# Linac Coordinate System w.r.t WCS.
			LCS = np.array([[1,0,0],[0,0,1],[0,-1,0]])

			# Beam Port Coordinate system w.r.t WCS.
			BCS = np.array([[1,0,0],[0,-1,0],[0,0,-1]])

			# Calculate the rotation of the bed in the LCS.
			# rotations = [-self.beam[i].patientSupport,self.beam[i].roll,self.beam[i].pitch]
			# axes = ['y','z','x']
			# cs_bed = (LCS@activeRotation(np.identity(3),rotations,axes))@np.linalg.inv(LCS)
			rotations = [self.beam[i].patientSupport]
			axes = ['z']
			cs_bed = (LCS@activeRotation(np.identity(3),rotations,axes))@np.linalg.inv(LCS)

			# Rotate the WCS to the beam port view w.r.t the WCS.
			rotations = [90]
			axes = ['x']
			cs_beamport = activeRotation(np.identity(3),rotations,axes)

			# Rotate the gantry and collimator w.r.t to the BCS.
			rotations = [self.beam[i].gantry,self.beam[i].collimator]
			axes = ['y','z']
			cs_linac = (BCS@activeRotation(np.identity(3),rotations,axes))@np.linalg.inv(BCS)

			# Calculate the new patient coordinate system.
			# A passive rotation of the patient position w.r.t to the LCS.
			temp = ct.RCS@cs_bed
			# A passive rotation of the inverse beam port takes the WCS into the view of the BCS w.r.t the WCS.
			temp = temp@np.linalg.inv(cs_beamport)
			# A passive rotation of the BEV w.r.t the BCS.
			self.beam[i].RCS = temp@cs_linac

			# Calculate a transform, W, that takes anything from the ct RCS to the beam RCS.
			self.beam[i].W = wcs2wcs(ct.RCS, self.beam[i].RCS)

			logging.info("\nBED R:\n {}".format(cs_bed))
			logging.info("\nBEAM PORT R:\n {}".format(cs_beamport))
			logging.info("\nLINAC R:\n {}".format(cs_linac))
			# logging.info("\nCT RCS:\n {}".format(ct.RCS))
			logging.info("\nBEV RCS:\n {}".format(self.beam[i].RCS))
			logging.info("\nW:\n {}".format(self.beam[i].W))

			# Rotate the CT.
			self.beam[i].pixelArray = gpu.rotate(self.beam[i].W)

			# Calculate the new pixel size.
			self.beam[i].pixelSize = np.absolute(self.beam[i].W@ct.pixelSize)

			logging.info("\nPixelSize: {}".format(self.beam[i].pixelSize))

			# Create the 2d projection images.
			self.beam[i].image = [Image2d(),Image2d()]

			# Find which rotated axis is on which fixed global axis.
			testAxes = np.absolute(self.beam[i].W)
			# Axes (x is fixed, so which ever arg is maxed means that axis is mapped onto our x fixed axis).
			x = np.argmax(testAxes[:,0])
			y = np.argmax(testAxes[:,1])
			z = np.argmax(testAxes[:,2])
			# Directions. Add +1 to axis identifiers since you can't have -0 but you can have -1...
			xd = (x+1)*np.sign(testAxes[x,0])
			yd = (y+1)*np.sign(testAxes[y,1])
			zd = (z+1)*np.sign(testAxes[z,2])

			# Extent.
			# Axis tells us which extent modifer to take and in what order.
			xe = ct.extent[x*2:x*2+2][::np.sign(xd).astype(int)]
			ye = ct.extent[y*2:y*2+2][::np.sign(yd).astype(int)]
			ze = ct.extent[z*2:z*2+2][::np.sign(zd).astype(int)]
			self.beam[i].extent = np.hstack((xe,ye,ze)).reshape((6,))

			# Top left front.
			self.beam[i].TLF = self.beam[i].extent[::2]

			# Get each axis for transform M.
			x = self.beam[i].RCS[0,:]
			y = self.beam[i].RCS[1,:]
			z = self.beam[i].RCS[2,:]

			# Construct the transformation matrix, M.
			self.beam[i].M = np.zeros((4,4))
			self.beam[i].M[:3,0] = self.beam[i].pixelSize[0]*x
			self.beam[i].M[:3,1] = self.beam[i].pixelSize[1]*y
			self.beam[i].M[:3,2] = self.beam[i].pixelSize[2]*z
			self.beam[i].M[:3,3] = self.beam[i].TLF
			self.beam[i].M[3,3] = 1

			# Calculate new isocenter position.
			self.beam[i].isocenter = np.absolute(wcs2wcs(np.identity(3),self.beam[i].RCS))@self.isocenter

			logging.info("\nIsocenter: {}".format(self.beam[i].isocenter))

			# Flatten the 3d image to the two 2d images.
			self.beam[i].image[0].pixelArray = np.sum(self.beam[i].pixelArray,axis=2)
			self.beam[i].image[0].extent = np.array([self.beam[i].extent[0],self.beam[i].extent[1],self.beam[i].extent[2],self.beam[i].extent[3]])
			self.beam[i].image[1].pixelArray = np.sum(self.beam[i].pixelArray,axis=1)
			self.beam[i].image[1].extent = np.array([self.beam[i].extent[4],self.beam[i].extent[5],self.beam[i].extent[2],self.beam[i].extent[3]])
			# self.beam[i].image[1].pixelArray = np.sum(self.beam[i].pixelArray,axis=0)
			# self.beam[i].image[1].extent = np.array([self.beam[i].extent[0],self.beam[i].extent[1],self.beam[i].extent[4],self.beam[i].extent[5]])

	def getIsocenter(self,beamIndex):
		return self.PCS@self.beam[beamIndex].isocenter

def activeRotation(cs,theta,axis):
	""" 
	Active rotation of 'cs' by 'theta' about 'axis' for a Right Handed Coordinate System.
	When viewed from the end of an axis, a positive rotation results in an anticlockwise direction.
	When viewed from looking down the axis, a positive rotation results in an clockwise direction.
	If theta = T:
		T = T3 x T2 x T1 ...
	If cs = P:
		P' = T x P
	"""
	# Put angles into radians.
	rotations = []
	for i, _ in enumerate(theta):
		t = np.deg2rad(theta[i])
		if axis[i] == 'x': r = np.array([[1,0,0],[0,np.cos(t),-np.sin(t)],[0,np.sin(t),np.cos(t)]])
		elif axis[i] == 'y': r = np.array([[np.cos(t),0,np.sin(t)],[0,1,0],[-np.sin(t),0,np.cos(t)]])
		elif axis[i] == 'z': r = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		rotations.append(r)

	# Calculate out the combined rotations.
	m = np.identity(3)
	for i, _ in enumerate(rotations):
		m = m@rotations[i]

	# Rotate coordinate system.
	rotated_cs = m@cs

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