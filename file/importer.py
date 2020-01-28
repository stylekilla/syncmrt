import os
import pydicom as dicom
import numpy as np
from file.image import Image2d
from file import hdf5
from tools.opencl import gpu as gpuInterface
from tools.math import wcs2wcs
from natsort import natsorted
from PyQt5 import QtCore, QtWidgets
import csv
import logging

np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})

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
		try:
			return list(self.file['Image'].keys())
		except:
			logging.critical("No images found.")
			return None

	def getImageSet(self,idx):
		logging.debug("Reading image set {}.".format(idx))
		_set = self.file.getImageSet(idx)
		imageSet = []
		for i in range(len(_set)):
			# Get the image and its attributes.
			image = Image2d()
			image.pixelArray = _set[str(i+1)][()]
			image.extent = _set[str(i+1)].attrs.get('Extent',default=None)
			image.patientIsocenter = _set[str(i+1)].attrs.get('Image Isocenter',default=None)
			image.patientPosition = list(_set[str(i+1)].attrs.get('Patient Support Position',default=None)) + list(_set[str(i+1)].attrs.get('Patient Support Angle',default=None))
			image.view['title'] = str(_set[str(i+1)].attrs.get('Image Angle',default="None"))+"\u00B0"
			image.imagingAngle = _set[str(i+1)].attrs.get('Image Angle',default=None)
			image.M = _set[str(i+1)].attrs.get('M',default=None)
			image.Mi = _set[str(i+1)].attrs.get('Mi',default=None)
			image.comment = _set[str(i+1)].attrs.get('Comment',default=None)
			# Append the image.
			imageSet.append(image)
		
		return imageSet

class csvPlan(QtCore.QObject):
	newSequence = QtCore.pyqtSignal()

	def __init__(self,file=None):
		"""
		Create a customised treatment plan that can be delivered on the beamline.
		"""
		super().__init__()
		# Create an empty sequence.
		self.sequence = []
		if type(file) != type(None):
			self.loadPlan(file)

	def addSequence(self,position,speed,contour):
		""" Add a new delivery sequence to the plan. """
		kwargs = {}
		kwargs['position'] = position
		kwargs['speed'] = speed
		kwargs['contour'] = contour
		kwargs['treated'] = False
		self.sequence.append(kwargs)

	def insertSequence(self,index,position,speed,contour):
		""" Insert a new delivery sequence in the plan. """
		kwargs = {}
		kwargs['position'] = position
		kwargs['speed'] = speed
		kwargs['contour'] = contour
		kwargs['treated'] = False
		self.sequence.insert(index,kwargs)

	def removeSequence(self,index):
		""" Remove a beam delivery sequence. """
		del self.sequence[index]

	def getSequence(self,index):
		""" Get a specified delivery sequence. """
		return self.sequence[index]

	def numberOfBeams(self):
		""" Return the number of beam delivery sequences present in the plan. """
		return len(self.sequence)

	def loadPlan(self,file):
		""" Load a csv file containing the plan. """
		import csv
		with open(file) as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				row['Sequence'] = int(row['Sequence'])
				# row['Position'] = list(map(float,row['Position'][1:-1].split(',')))
				row['Angle'] = float(row['Angle'])
				row['Speed'] = float(row['Speed'])
				self.sequence.append(row)

		self.newSequence.emit()

	def reset(self):
		""" Reset the plan. This removes all sequences. """
		self.sequence = []


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

class ct(QtCore.QObject):
	newCtView = QtCore.pyqtSignal()

	def __init__(self,dataset,gpu):
		super().__init__()
		# Hold a reference to the gpu instance.
		self.gpu = gpu

		# Check that the dataset is indeed a DICOM CT dataset.
		dataset = checkDicomModality(dataset,'CT')

		if len(dataset) is 0:
			# If the dataset has no CT files, then exit this function.
			return
		else:
			# Else, read the first one as a reference point.
			ref = dicom.dcmread(dataset[0])

		# Get the 3D CT array shape.
		shape = np.array([int(ref.Rows), int(ref.Columns), len(dataset)])
		# Create an empty python array to dump the CT data into.
		self.pixelArray = np.zeros(shape, dtype=np.int32)
		# Read array in one slice at a time.
		for index,fn in enumerate(dataset):
			ctSlice = dicom.dcmread(fn)
			self.pixelArray[:,:,dataset.index(fn)] = ctSlice.pixel_array

		# Rescale the Hounsfield Units.
		self.pixelArray = (self.pixelArray*ref.RescaleSlope) + ref.RescaleIntercept
		# Get current CT orientation.
		self.patientPosition = ref.PatientPosition
		# Python coordinate system.
		self.PCS = np.array([[0,1,0],[1,0,0],[0,0,1]])
		# Patient reference coordinate system (RCS).
		dcmAxes =  np.array(list(map(float,ref.ImageOrientationPatient)))
		x = dcmAxes[:3]
		y = dcmAxes[3:6]
		z = np.cross(x,y)
		self.RCS = np.vstack((x,y,z))
		# Calculate spacing between slices as it isn't always provided.
		z1 = list(map(float,ref.ImagePositionPatient))[2]
		z2 = list(map(float,dicom.dcmread(dataset[-1]).ImagePositionPatient))[2]
		spacingBetweenSlices = (z2-z1)/(len(dataset)-1)
		# Get the pixel size.
		self.pixelSize = np.append(np.array(list(map(float,ref.PixelSpacing))),spacingBetweenSlices)
		# Get the top left front pixel position in the RCS (set as the centre of the voxel).
		self.TLF = np.array(list(map(float,ref.ImagePositionPatient)))
		# Adjust the TLF to sit on the outside corner of the voxel (to align with the expected inputs for matplotlib's extent).
		self.TLF +=  np.sign(self.TLF)*(self.pixelSize/2)
		# Construct the transformation matrix, M.
		self.M = np.zeros((4,4))
		self.M[:3,0] = self.pixelSize[0]*x
		self.M[:3,1] = self.pixelSize[1]*y
		self.M[:3,2] = self.pixelSize[2]*z
		self.M[:3,3] = self.TLF
		self.M[3,3] = 1

		# Get the top left front and bottom right back indices for caclualting extent.
		voxelIndex1 = np.array([0,0,0,1]).reshape((4,1))
		voxelIndex2 = np.array([shape[0],shape[1],shape[2],1]).reshape((4,1))
		# Compute the voxel indices in mm.
		voxelPosition1 = self.M@voxelIndex1
		voxelPosition2 = self.M@voxelIndex2
		# Extent is [Left,Right,Bottom,Top,Front,Back]
		_x = [voxelPosition1[0],voxelPosition2[0]]
		_y = [voxelPosition2[1],voxelPosition1[1]]
		_z = [voxelPosition1[2],voxelPosition2[2]]
		self.extent = np.array(_x+_y+_z).reshape((6,))

		# Placeholder for a view extent.
		self.viewExtent = np.zeros(self.extent.shape)

		# Calculate the base extent.
		# self.baseExtent = np.array(sorted(_x)+sorted(_y)+sorted(_z)).reshape((6,))
		# Find the (0,0,0) mm as an 'index' (float).
		# self.zeroIndex = np.linalg.inv(self.M)@np.array([0,0,0,1])

		# Load array onto GPU for future reference.
		self.gpu.loadData(self.pixelArray)
		# Create a 2d image list for plotting.
		self.image = [Image2d(),Image2d()]

		# Create an isocenter for treatment if desired. This must be in DICOM XYZ.
		self.isocenter = None

		# Set the default.
		self.calculateView('AP')

	def calculateView(self,view,roi=None,flatteningMethod='sum'):
		""" Rotate the CT array for a new view of the dataset. """
		# Make the RCS for each view. 
		default = np.array([[1,0,0],[0,1,0],[0,0,1]])
		si = np.array([[-1,0,0],[0,1,0],[0,0,-1]])
		lr = np.array([[0,0,1],[0,1,0],[-1,0,0]])
		rl = np.array([[0,0,-1],[0,1,0],[1,0,0]])
		ap = np.array([[1,0,0],[0,0,1],[0,-1,0]])
		pa = np.array([[-1,0,0],[0,0,-1],[0,-1,0]])
		# Assign matrix, m, to the view matrix and axis titles.
		if view == 'SI':
			RCS = si
			t1 = 'SI'
			t2 = 'RL'
		elif view == 'IS':
			RCS = default
			t1 = 'IS'
			t2 = 'LR'
		elif view == 'LR':
			RCS = lr
			t1 = 'LR'
			t2 = 'SI'
		elif view == 'RL':
			RCS = rl
			t1 = 'RL'
			t2 = 'IS'
		elif view == 'AP':
			RCS = ap
			t1 = 'AP'
			t2 = 'LR'
		elif view == 'PA':
			RCS = pa
			t1 = 'PA'
			t2 = 'RL'

		# Calculate a transform, W, that takes us from the original CT RCS to the new RCS.
		W = wcs2wcs(self.RCS,RCS)
		# Rotate the CT if required.
		if np.array_equal(W,np.identity(3)):
			pixelArray = self.pixelArray
		else:
			pixelArray = self.gpu.rotate(W)
		# Calculate the new extent.
		# Find Origin
		origin = (np.linalg.inv(self.M)@np.array([0,0,0,1]))[:3]
		# Rotate the Origin
		origin_rot = W@origin
		# Rotate the pixel size.
		pixelSize_rot = np.absolute(W@self.pixelSize)
		# Find bounding box of output array.
		basicBox = np.array([
			[0,0,0],
			[1,0,0],
			[0,1,0],
			[1,1,0],
			[0,0,1],
			[1,0,1],
			[0,1,1],
			[1,1,1]
		])
		inputShape = basicBox * self.pixelArray.shape
		outputShape = np.zeros(basicBox.shape)
		for index in range(8):
			outputShape[index,:] = W@inputShape[index,:]
		mins = np.absolute(np.amin(outputShape,axis=0))
		outputShape += mins
		# Calculate new origin situated in output array.
		origin_new = origin_rot + mins
		# Calculate new extent.
		extent = np.zeros(self.extent.shape)
		TLF = -origin_new * np.sum(RCS,axis=0) * pixelSize_rot
		extent[::2] = TLF
		extent[1::2] = TLF + np.amax(outputShape,axis=0) * np.sum(RCS,axis=0) * pixelSize_rot
		# Extent is calculated as: [left, right, BOTTOM, TOP, front, back]. Swap top/bot values.
		extent[2], extent[3] = extent[3], extent[2]
		self.viewExtent = extent
		# Calculate the view matrix.
		self.viewM = np.zeros((4,4))
		self.viewM[0,:3] = pixelSize_rot[0] * (np.sign(np.sum(RCS[:,0]))*np.array([1,0,0]))
		self.viewM[1,:3] = pixelSize_rot[1] * (np.sign(np.sum(RCS[:,1]))*np.array([0,1,0]))
		self.viewM[2,:3] = pixelSize_rot[2] * (np.sign(np.sum(RCS[:,2]))*np.array([0,0,1]))
		self.viewM[:3,3] = TLF
		self.viewM[3,3] = 1

		if np.array_equal(roi,self.viewExtent):
			# This does not work...
			temporary_extent = self.viewExtent
		elif type(roi) is not type(None):
			# Set the view extent to the ROI.
			temporary_extent = roi
			# Get the array indices that match the roi.
			indices = self.calculateIndices(temporary_extent)

			x1,x2,y1,y2,z1,z2 = indices
			# Calculate new extent based of approximate indices of input ROI.
			p1 = self.viewM@np.array([x1,y1,z1,1])
			p2 = self.viewM@np.array([x2,y2,z2,1])
			temporary_extent = np.zeros(extent.shape)
			temporary_extent[::2] = p1[:3]
			temporary_extent[1::2] = p2[:3]
			# Order the indices
			x1,x2 = sorted([x1,x2])
			y1,y2 = sorted([y1,y2])
			z1,z2 = sorted([z1,z2])
			# Slice the array.
			pixelArray = pixelArray[y1:y2,x1:x2,z1:z2]
		else:
			temporary_extent = self.viewExtent

		# Split up into x, y and z extents for 2D image.
		x,y,z = [temporary_extent[i:i+2] for i in range(0,len(temporary_extent),2)]
		# Get the first flattened image.
		if flatteningMethod == 'sum': self.image[0].pixelArray = np.sum(pixelArray,axis=2)
		elif flatteningMethod == 'max': self.image[0].pixelArray = np.amax(pixelArray,axis=2)
		self.image[0].extent = np.array(list(x)+list(y))
		self.image[0].view = { 'title':t1 }
		# Get the second flattened image.
		if flatteningMethod == 'sum': self.image[1].pixelArray = np.sum(pixelArray,axis=1)
		elif flatteningMethod == 'max': self.image[1].pixelArray = np.amax(pixelArray,axis=1)
		self.image[1].extent = np.array(list(z)+list(y))
		self.image[1].view = { 'title':t2 }

		# Emit a signal to say a new view has been loaded.
		self.newCtView.emit()

	def calculateIndices(self,extent):
		""" Calculate the indices of the CT array for a given ROI. """
		p1 = np.insert(extent[::2],3,1)
		p2 = np.insert(extent[1::2],3,1)
		i1 = (np.linalg.inv(self.viewM)@p1)[:3]
		i2 = (np.linalg.inv(self.viewM)@p2)[:3]
		indices = np.zeros(np.array(self.extent.shape))
		indices[::2] = i1
		indices[1::2] = i2
		indices = list(map(int,indices))
		return indices

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

class rtplan:
	def __init__(self,rtplan,ct,gpu):
		"""
			RCS: Reference Coordinate System (Patient)
			BCS: Beam Coordinate System (Linac)
			PCS: Pyhon Coordinate System (DICOM to Python)
		"""
		self.PCS = np.array([[0,1,0],[1,0,0],[0,0,1]])

		# Firstly, read in DICOM rtplan file.
		ref = dicom.dcmread(rtplan[0])
		# Construct an object array of the amount of beams to be delivered.
		self.beam = np.empty(ref.FractionGroupSequence[0].NumberOfBeams,dtype=object)
		# Get the isocenter. Current only supports a single isocenter.
		self.isocenter = np.array(list(map(float,ref.BeamSequence[0].ControlPointSequence[0].IsocenterPosition)))

		# logging.info("Isocenter (DICOM) {}".format(self.isocenter))

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

			# Calculate the new patient coordin ate system.
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

			# testAxes = np.absolute(self.beam[i].W)
			# Find the RCS of the beam view.
			testAxes = np.absolute(self.beam[i].RCS)
			# Axes (x is fixed, so which ever arg is maxed means that axis is mapped onto our x fixed axis).
			x = np.argmax(testAxes[:,0])
			y = np.argmax(testAxes[:,1])
			z = np.argmax(testAxes[:,2])
			# Directions. Add +1 to axis identifiers since you can't have -0 but you can have -1...
			xd = (x+1)*np.sign(self.beam[i].RCS[x,0])
			yd = (y+1)*np.sign(self.beam[i].RCS[y,1])
			zd = (z+1)*np.sign(self.beam[i].RCS[z,2])

			# Extent.
			# Axis tells us which extent modifer to take and in what order.
			xe = ct.baseExtent[x*2:x*2+2][::np.sign(xd).astype(int)]
			ye = ct.baseExtent[y*2:y*2+2][::np.sign(yd).astype(int)]
			ze = ct.baseExtent[z*2:z*2+2][::np.sign(zd).astype(int)]
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
			self.beam[i].image[0].extent = np.array([self.beam[i].extent[0],self.beam[i].extent[1],self.beam[i].extent[3],self.beam[i].extent[2]])
			self.beam[i].image[1].pixelArray = np.sum(self.beam[i].pixelArray,axis=1)
			self.beam[i].image[1].extent = np.array([self.beam[i].extent[4],self.beam[i].extent[5],self.beam[i].extent[3],self.beam[i].extent[2]])

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