class ct(QtCore.QObject):
	newCtView = QtCore.pyqtSignal()

	def __init__(self,dataset,gpu):
		# QProgressDialog
		progress = QtWidgets.QProgressDialog()
		progress.setMaximum(len(dataset))
		progress.setMinimum(0)
		progress.setAutoClose(True)
		progress.setLabel("Loading DICOM Files")
		progress.open()

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
			# Emit the load percentage.
			progress.setValue(index+1)

		progress.setValue(0)
		progress.setLabel("Initialising the data")
		progress.setMaximum(3)
		# Rescale the Hounsfield Units.
		self.pixelArray = (self.pixelArray*ref.RescaleSlope) + ref.RescaleIntercept

		progress.setValue(1)
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
		spacingBetweenSlices = (z2-z1)/len(dataset)
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

		progress.setValue(2)

		# Get the top left front and bottom right back indices for caclualting extent.
		voxelIndex1 = np.array([0,0,0,1]).reshape((4,1))
		voxelIndex2 = np.array([shape[0],shape[1],shape[2],1]).reshape((4,1))
		# Compute the voxel indices in mm.
		voxelPosition1 = self.M@voxelIndex1
		voxelPosition2 = self.M@voxelIndex2
		# Store the bottom right back position.
		self.BRB = voxelPosition2[:3]
		# Extent is [Left,Right,Bottom,Top,Front,Back]
		_x = [voxelPosition1[0],voxelPosition2[0]]
		_y = [voxelPosition1[1],voxelPosition2[1]]
		_z = [voxelPosition1[2],voxelPosition2[2]]
		self.extent = np.array(_x+_y+_z).reshape((6,))
		# Calculate the base extent.
		self.baseExtent = np.array(sorted(_x)+sorted(_y)+sorted(_z)).reshape((6,))

		# Load array onto GPU for future reference.
		gpu.loadData(self.pixelArray,extent=self.extent)

		progress.setValue(3)
		# Create a 2d image list for plotting.
		self.image = [Image2d(),Image2d()]

		# Create an isocenter for treatment if desired. This must be in DICOM XYZ.
		self.isocenter = None

		# Close the progress bar.
		progress.reset()

		# Set the default.
		self.calculateView('AP')

	def calculateExtent(self,RCS,roi=None):
		""" Calculate the extent of the CT for a given view. """
		# The RCS is the reference coordinate system for the desired ct view.
		RCS = np.array(RCS)
		# Start an empty extent list. This is [Left, Right, Top, Bottom, Front, Back]; note the difference from matplotlib's extent!
		extent = []
		# Iterate through each axis and take the correct extent values in the correct order.
		for ax in RCS:
			a = 2*(np.abs(ax)-1)
			b = a+2
			c = int(np.sign(ax))
			if type(roi) is type(None):
				extent += list(self.baseExtent[a:b][::c])
			else:
				extent += list(roi[a:b][::c])
		return extent

	def calculateIndices(self,extent):
		""" Calculate the indices of the CT array for a given ROI. """
		# Start an empty extent list. This is [Left, Right, Top, Bottom, Front, Back]; note the difference from matplotlib's extent!
		indices = []
		# Iterate through each axis and take the correct extent values in the correct order.
		for point in extent:
			index = np.linalg.inv(self.M)@point
			indices.append(index)
		return extent

	def calculateView(self,view,roi=None,flatteningMethod='sum'):
		""" Rotate the CT array for a new view of the dataset. """
		default = np.array([[1,0,0],[0,1,0],[0,0,1]])
		si = np.array([[-1,0,0],[0,1,0],[0,0,-1]])
		lr = np.array([[0,0,1],[0,1,0],[-1,0,0]])
		rl = np.array([[0,0,-1],[0,1,0],[1,0,0]])
		ap = np.array([[1,0,0],[0,0,1],[0,-1,0]])
		pa = np.array([[-1,0,0],[0,0,-1],[0,-1,0]])
		# Assign matrix, m, to the view matrix and axis titles.
		if view == 'SI':
			M = si
			t1 = 'SI'
			t2 = 'RL'
		elif view == 'IS':
			M = default
			t1 = 'IS'
			t2 = 'LR'
		elif view == 'LR':
			M = lr
			t1 = 'LR'
			t2 = 'SI'
		elif view == 'RL':
			M = rl
			t1 = 'RL'
			t2 = 'IS'
		elif view == 'AP':
			M = ap
			t1 = 'AP'
			t2 = 'LR'
		elif view == 'PA':
			M = pa
			t1 = 'PA'
			t2 = 'RL'

		# Calculate a transform, W, that takes us from the original CT RCS to the new RCS.
		W = wcs2wcs(self.RCS, M)
		# Rotate the CT if required.
		if np.array_equal(W,np.identity(3)):
			pixelArray = self.pixelArray
		else:
			pixelArray = gpu.rotate(W)

		if type(roi) is type(None):
			# Calculate the new extent using the existing extent.
			extent = self.calculateExtent(M)
			# Make the array indices encompass the full array.
			x1,y1,z1 = [0,0,0]
			x2,y2,z2 = [-1,-1,-1]
		else:
			# If an ROI is defined, we must take it from the standard DICOM XYZ CS and convert it into the desired RCS.
			extent = self.calculateExtent(M,roi)
			# Get the array indices that match the roi.
			x1,y1,z1 = [0,0,0]
			x2,y2,z2 = [-1,-1,-1]
		# Split up into x, y and z extents.
		x,y,z = [extent[i:i+2] for i in range(0,len(extent),2)]

		# If an roi is specified, calculate the indices for array slicing.
		extent = self.calculateExtent(self.RCS,roi)
		indices = self.calculateIndices(extent)
		x1,x2,y1,y2,z1,z2 = indices

		# Get the first flattened image.
		if flatteningMethod == 'sum': self.image[0].pixelArray = np.sum(pixelArray[y1:y2+1,x1:x2+1,z1:z2+1],axis=0)
		elif flatteningMethod == 'max': self.image[0].pixelArray = np.amax(pixelArray[y1:y2+1,x1:x2+1,z1:z2+1],axis=0)
		self.image[0].extent = np.array(x+y[::-1])
		self.image[0].view = { 'title':t1 }
		# Get the second flattened image.
		if flatteningMethod == 'sum': self.image[1].pixelArray = np.sum(pixelArray[y1:y2+1,x1:x2+1,z1:z2+1],axis=2)
		elif flatteningMethod == 'max': self.image[1].pixelArray = np.amax(pixelArray[y1:y2+1,x1:x2+1,z1:z2+1],axis=2)
		self.image[1].extent = np.array(z+y[::-1])
		self.image[1].view = { 'title':t2 }

		# Emit a signal to say a new view has been loaded.
		self.newCtView.emit()