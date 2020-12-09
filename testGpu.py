import pyopencl as cl
import numpy as np
import logging
import os, inspect

logging.info("Adding MPL support for debugging.")
import matplotlib as mpl
from matplotlib import pyplot as plt

# os.environ['PYOPENCL_NO_CACHE'] = '1'
# os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

# Supress other logs.
ocl_logger = logging.getLogger('cl')
ocl_logger.setLevel(logging.CRITICAL)
ocl_logger.propagate = False
mpl_logger = logging.getLogger('mpl')
mpl_logger.setLevel(logging.CRITICAL)
mpl_logger.propagate = False
plt_logger = logging.getLogger('plt')
plt_logger.setLevel(logging.CRITICAL)
plt_logger.propagate = False

class gpu:
	def __init__(self):
		"""
		1. Initialise some parameters
		2. Find a suitable device
		3. Create a context and queue for work to take place in
		"""
		# Find avail devices.
		platforms = cl.get_platforms()
		cpuList = []
		gpuList = []
		for plt in platforms:
			cpuList += plt.get_devices(cl.device_type.CPU)
			gpuList += plt.get_devices(cl.device_type.GPU)
		# Create a device context, one for the CPU, one for the GPU.
		cpu = [cpuList[0]]
		for device in gpuList:
			try:
				gpu = [device]
			except:
				# Use the CPU if no GPU found.
				gpu = [cpuList[0]]

		self.ctx = cl.Context(devices=gpu)
		logging.debug('Using {} for computation.'.format(gpu[0]))
			
		# Create a device queue.
		self.queue = cl.CommandQueue(self.ctx)

	def _generateDeviceMemoryObjects(self,context,size,amount):
		""" Return a list of references to new memory objects. """
		buffers = []
		for i in range(amount):
			buffers.append( cl.Buffer(context, cl.mem_flags.READ_WRITE, size=size) )
		return buffers

	def findFeaturesSIFT(self,array,**kwargs):
		""" Implementation of Lowe 2004 and Allaire 2008 """
		if len(array.shape) == 2:
			return self.SIFT2D(array,**kwargs)
		elif len(array.shape) == 3:
			return self.SIFT3D(array,**kwargs)
		else:
			raise Exception("Cannot find features with SIFT for array with {} dimensions. Only 2 or 3 dimensions are accepted.".format(len(array.shape)))

	def SIFT2D(self,array,
			sigma=1.6,
			contrast=3,
			curvature=10,
			upsample=False,
			plot=False
		):
		"""
		Array gets turned into float and rescaled between [0,1].
		If you want to clamp your array you should do it before calling this method.
		How to build in a way to choose how many octaves/scales you want?
			Octaves are easy...
			Scale levels - not so easy. Requires kernel changes.
		"""
		logging.info("Starting SIFT 2D algorithm on GPU.")

		# Array will be a float between [0,1].
		datatype = cl.cltypes.float
		# Contrast rejection threshold is provided as a percentage, we convert this to be between [0,1].
		contrastRejectionThreshold = contrast/100

		"""
		SETUP.
		"""
		# (!) Changing nOctaves will require changes to the OpenCL kernel.
		# The number of octaves is fixed.
		nOctaves = 3
		# The number of scale levels is tied to the number of octave levels. 
		nScaleLevels = nOctaves+3
		# Normalise the array to be within [0,1].
		array = (1/array.ptp())*(array-array.min())
		array = np.ascontiguousarray(array,dtype=datatype)
		# Descriptors to return.
		arrayDescriptors = []

		# Memory flags.
		mf = cl.mem_flags
		# Keep the original array in the CPU RAM.
		ogArray = cl.Buffer(self.ctx, mf.READ_ONLY | mf.USE_HOST_PTR, hostbuf=array)
		# Get kernel source.
		fp = os.path.dirname(inspect.getfile(gpu))
		kernel = open(fp+"/tools/opencl/kernels/sift2d.cl", "r").read()
		# Compile kernel.
		program = cl.Program(self.ctx,kernel).build()

		"""
		MEMORY OVERHEAD.
		"""
		# Data for first octave.
		if upsample:
			# We want to upscale the first octave.
			subSamplingFactors = [0.5]
		else:
			# We want to skip the upsampling stage (default).
			subSamplingFactors = [1]
		# Lists for storing octave data and GPU memory objects.
		octaveShapes = []
		octaveScaleImageSets = []
		octaveDogImageSets = []
		# Data for n octaves.
		for i in range(nOctaves):
			# The subsampling factor for each octave should be double the last.
			if i > 0: subSamplingFactors.append(subSamplingFactors[-1]*2)
			# Adjust the image shape for the octave.
			octaveShapes.append(tuple(np.array(np.array(array.shape)/subSamplingFactors[-1],dtype=int)))
			# Memory objects for this octave.
			octaveScaleImageSets.append(self._generateDeviceMemoryObjects(self.ctx,np.dtype(datatype).itemsize*np.product(octaveShapes[-1]),nScaleLevels))
			octaveDogImageSets.append(self._generateDeviceMemoryObjects(self.ctx,np.dtype(datatype).itemsize*np.product(octaveShapes[-1]),nScaleLevels-1))

		"""
		PROCESSING: PER OCTAVE.
		"""
		# Iterate over all octaves and scales.
		for scaleImages,dogImages,octaveShape,subSamplingFactor in zip(octaveScaleImageSets,octaveDogImageSets,octaveShapes,subSamplingFactors):
			# Save the octave number (same as enumerate: [0,n-1]).
			octaveNumber = subSamplingFactors.index(subSamplingFactor)
			# Choosing a value of sigma for the octave.
			octaveSigma = sigma*subSamplingFactor
			logging.info("Starting calculations for Octave {}.".format(octaveNumber+1))
			logging.debug("Octave Image Shape: {}".format(octaveShape))

			# If our octave requires resampling, do it.
			if subSamplingFactor != 1:
				logging.info("Subsampling array at {} intervals.".format(subSamplingFactor))
				imageArray = cl.Buffer(self.ctx, mf.READ_WRITE, size=np.dtype(datatype).itemsize*np.product(octaveShape))
				# Program args.
				args = (
					imageArray,
					cl.cltypes.float(subSamplingFactor),
					cl.cltypes.int(array.shape[1]),
					ogArray
				)
				# Run the program
				program.BilinearInterpolation(self.queue,octaveShape,None,*(args))
			else:
				# Otherwise, just pass the original data on.
				imageArray = ogArray

			if plot:
				testArray = np.zeros(octaveShape,dtype=datatype)
				cl.enqueue_copy(self.queue, testArray, imageArray)
				fig,ax = plt.subplots(2,7,sharex=True,sharey=True)
				fig.set_size_inches(20,10)
				ax[0,0].imshow(testArray,cmap='Greys')
				ax[0,0].set_title("Octave Image")

			"""
			STEP 1.1: SCALE IMAGES (GAUSSIAN BLUR).
			"""
			if plot: testImages = []
			# Calculate scale images.
			for i in range(nScaleLevels):
				# Our sigma for this image.
				scaleSigma = octaveSigma*2**(i/nOctaves)
				logging.debug("Calculating Scale Image {} with sigma {}.".format(i+1,scaleSigma))
				# Filter width should be 5 times the standard deviation and rounded up to the next odd integer.
				filterWidth = cl.cltypes.int( 6*scaleSigma + (6*(scaleSigma+1)%2) )
				# Calculate an offset for the filter so that it is centred about zero (i.e. so it goes from -1,0,+1 instead of 0,1,2...).
				filterOffset = (filterWidth-1)/2
				# Calculate xy values for filter (centred on zero, as described above).
				x,y = np.indices((filterWidth,filterWidth))-filterOffset
				# We are now on a per-buffer level within an octave.
				gScaleImage = scaleImages[i]
				# Generate gaussian kernel.
				gaussianKernel = np.array(np.exp( -(x**2 + y**2)/(2*(scaleSigma)**2) )/( 2*np.pi * (scaleSigma)**2 ),dtype=cl.cltypes.float)
				# Allocate the gaussian kernel to GPU memory.
				gGaussianKernel = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gaussianKernel)
				# Program args.
				args = (
					imageArray,
					gGaussianKernel,
					filterWidth,
					gScaleImage
				)
				# Run the program
				program.Gaussian2D(self.queue,octaveShape,None,*(args))

				if plot:
					testArray = np.zeros(octaveShape,dtype=datatype)
					cl.enqueue_copy(self.queue, testArray, gScaleImage)
					testImages.append(testArray)

			if plot:
				for i in range(nScaleLevels):
					ax[0,i+1].imshow(testImages[i],cmap='Greys')
					ax[0,i+1].set_title("Scale Image {}".format(i+1))

			"""
			STEP 1.2: DIFFERENCE OF GAUSSIAN.
			"""
			if plot: testImages = []

			# Calculate Difference of Gaussian.
			for i,j in zip(range(0,nScaleLevels-1),range(1,nScaleLevels)):
				logging.info("Calculating Difference of Gaussian between scale images {} and {}.".format(i+1,j+1))
				# Grab pairs of octaves and a dog image to fill in.
				args = (
					scaleImages[i],
					scaleImages[j],
					dogImages[i]
				)
				program.Difference(self.queue,octaveShape,None,*(args))

				if plot:
					testArray = np.zeros(octaveShape,dtype=datatype)
					cl.enqueue_copy(self.queue, testArray, dogImages[i])
					testImages.append(testArray)

			if plot:
				for i in range(nScaleLevels-1):
					ax[1,i].imshow(testImages[i],cmap='Greys')
					ax[1,i].set_title("DoG Image {}".format(i+1))

			"""
			STEP 1.3: GENERATE GRADIENT MAPS.
			"""
			# Gradient maps are an (m,n,2) array). Their size is the shape product times the cl datatype.
			nbytes = np.prod(octaveShape) * np.dtype(cl.cltypes.float).itemsize * 2
			gradientMaps = self._generateDeviceMemoryObjects(self.ctx,nbytes,nScaleLevels)
			# Create one gradient map for each scale image.
			for idx in range(nScaleLevels):
				args = (
					scaleImages[idx],
					gradientMaps[idx]
				)
				program.GenerateGradientMap(self.queue,octaveShape,None,*(args))

			if plot:
				testImageShape = tuple(list(octaveShape)+[2])
				tempArray = np.zeros(testImageShape,dtype=cl.cltypes.float)
				cl.enqueue_copy(self.queue, tempArray, gradientMaps[0])
				ax[1,5].imshow(tempArray[:,:,0],cmap='Greys')
				ax[1,6].imshow(tempArray[:,:,1],cmap='Greys')
				ax[1,5].set_title("Gradient (Scale 1)")
				ax[1,6].set_title("Theta (Scale 1)")

			"""
			STEP 2.1: FIND KEYPOINTS
			"""
			# Create features map.
			features = np.zeros(octaveShape,dtype=cl.cltypes.int)
			gFeatures = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=features)
			# For each Dog map, find the local minima and maxima.
			for i in range(1,len(dogImages)-1):
				logging.info("Finding local extrema in DoG Images {} to {}.".format(i,i+2))
				gDog1 = dogImages[i-1]
				gDog2 = dogImages[i]
				gDog3 = dogImages[i+1]
				# Program args.
				args = (
					gDog1,
					gDog2,
					gDog3,
					cl.cltypes.int(i),
					gFeatures
				)
				# These will write the scale factor, s, at the xy position in which the extrema was found.
				program.FindLocalMinima(self.queue,octaveShape,None,*(args))
				program.FindLocalMaxima(self.queue,octaveShape,None,*(args))

			# Bring back our list of features.
			cl.enqueue_copy(self.queue, features, gFeatures)
			# Features array is no longer required.
			gFeatures.release()

			# Find out how many features there were. The function np.nonzero() searches the array for all non zero values and returns their positions.
			x,y = np.nonzero(features)
			# Now we know how many features we have identified in this octave.
			nFeatures = len(x)
			if nFeatures == 0: 
				logging.warning("No initial features found in Octave {}.".format(octaveNumber+1))
				continue
			# This grabs the scale values at those non-zero positions.
			scale = features[tuple([x,y])]
			# Create a keypoint tracker that allows for (x,y,sigma,36-bin orientation histogram).
			keypoints = np.zeros((nFeatures,3),dtype=cl.cltypes.float)
			# Assign (x,y,scale) to each keypoint.
			keypoints[:,0] = x
			keypoints[:,1] = y
			keypoints[:,2] = scale

			logging.info("Found {} initial keypoints.".format(nFeatures))

			if plot:
				# We want to plot about 100 kp's.
				kpstride = int(len(keypoints)/100)+1
				for index,kp in enumerate(keypoints):
					# Only plot every 50 kp's.
					if index%kpstride != 0: continue
					x,y,s = kp
					ax[1,int(s)].scatter(y,x,c='k',marker='x')
				plt.tight_layout()
				plt.show()

				kepointsOriginal = np.array(keypoints)

			"""
			STEP 2.2: FIND STABLE KEYPOINTS
			"""
			# Assign gpu memory for the featurelist. This will be the main call of our kernel.
			gKeypoints = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=keypoints)
			# We also need to pass the kernel information on how big the images are. For each octave this has been previously described as octaveShape.
			imageSize = np.array(octaveShape,dtype=cl.cltypes.int)
			gImageSize = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=imageSize)

			# Now we want to refine the local positions with sub-pixel accuracy and identify the stable features.
			args = (
				gKeypoints,
				gImageSize,
				cl.cltypes.float(contrastRejectionThreshold),
				cl.cltypes.float(curvature),
				dogImages[0],
				dogImages[1],
				dogImages[2],
				dogImages[3],
				dogImages[4]
			)
			program.LocateStableFeatures(self.queue,(nFeatures,),None,*(args))

			# Bring back our list of stable features.
			cl.enqueue_copy(self.queue, keypoints, gKeypoints)
			gKeypoints.release()

			# Reduce the feature list into valid components. Remove everything set to (0,0,0).
			mask = np.all(keypoints>0,axis=1)
			temp = keypoints[mask]
			nFeatures = len(temp)
			if nFeatures == 0: 
				logging.warning("No image stable features found in Octave {}.".format(octaveNumber+1))
				continue

			logging.info("Identified {} stable features.".format(nFeatures))

			"""
			STEP 2.3: ASSIGN OREITNATION TO KEYPOINTS.
			"""
			# (!) Changing this requires changes the to the OpenCL kernel.
			# Create a keypoint tracker that allows for (x,y,sigma, and up to 5 orientations).
			keypoints = np.zeros((nFeatures,8),dtype=cl.cltypes.float)
			keypoints[:,:3] = temp
			# Re-assign GPU space.
			gKeypoints = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=keypoints)

			# Gaussian kernels for each scale level.
			gaussianKernels = []
			kernelSizes = []
			for i in range(nScaleLevels):
				# Gaussian kernels..
				orientationSigma = 1.5*octaveSigma*2**(i/nOctaves)
				filterWidth = cl.cltypes.int( int(6*orientationSigma + (6*(orientationSigma+1)%2)) )
				filterOffset = (filterWidth-1)/2
				x,y = np.indices((filterWidth,filterWidth))-filterOffset
				kernel = np.array(np.exp( -(x**2 + y**2)/(2*(orientationSigma)**2) )/( 2*np.pi * (orientationSigma)**2 ),dtype=cl.cltypes.float)
				# Save the kernel and it's width.
				gaussianKernels.append(kernel)
				kernelSizes.append(filterWidth)

			gaussianKernelBuffers = []
			for kernel in gaussianKernels:
				gaussianKernelBuffers.append(cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=kernel))

			kernelSizes = np.array(kernelSizes, dtype=cl.cltypes.int)
			gGaussianWidths = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=kernelSizes)

			# To create orientation histograms, we need the features and the gradient maps.
			args = (
				gKeypoints,
				gImageSize,
				gGaussianWidths,
				gradientMaps[0],
				gradientMaps[1],
				gradientMaps[2],
				gradientMaps[3],
				gradientMaps[4],
				gaussianKernelBuffers[0],
				gaussianKernelBuffers[1],
				gaussianKernelBuffers[2],
				gaussianKernelBuffers[3],
				gaussianKernelBuffers[4]
			)
			# Generate the descriptors for the stable features.
			program.KeypointOrientations(self.queue,(nFeatures,),None,*(args))
			# Bring back our list of stable features.
			cl.enqueue_copy(self.queue, keypoints, gKeypoints)

			# New keypoints.
			newKeypoints = []
			# Grab all the keypoints with multiple orientations.
			for keypoint in keypoints:
				orientations = keypoint[3:][keypoint[3:]>0]
				if len(orientations) > 1:
					for i in range(len(orientations)):
						newKeypoints.append( np.hstack([keypoint[:3],orientations[i]]) )

			# Combine them.
			if len(newKeypoints) > 0:
				allKeypoints = np.vstack([keypoints[:,:4],newKeypoints])
			else:
				allKeypoints = np.array(keypoints[:,:4])
			# Find out how many features we now have.
			nFeatures = len(allKeypoints)
			if nFeatures == 0: 
				logging.warning("No image features found in Octave {}.".format(octaveNumber+1))
				continue
			logging.info("Created {} uniquely orientated keypoints.".format(nFeatures))

			"""
			STEP 2.4: GENERATE 128 ELEMENT DESCRIPTORS FOR KEYPOINTS.
			"""
			# Make a descriptor array that is (nKeypoints, {x,y,scale(octave number),orientation,8*4*4 descriptor array}).
			descriptors = np.zeros((nFeatures,132),dtype=cl.cltypes.float)
			# Fill the keypoint values (x,y,sigma (octave number),theta. The memory at (sigma (octave number),theta) will get reused in the kernel for the descriptor.
			descriptors[:,:4] = allKeypoints

			# Copy it to the gpu.
			gDescriptors = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=descriptors)

			# Create a Gaussian weighting function unique to the scale level...?
			# Choose a filter width (16 x 16 window).
			filterWidth = cl.cltypes.int(16)
			# Calculate xy values for filter (centred on zero, as described above).
			x,y = np.indices((filterWidth,filterWidth)) - filterWidth/2 + 0.5
			# Sigma should be one half of the filter width.
			descriptorSigma = filterWidth/2
			# Generate gaussian kernel.
			gaussianKernel = np.array(np.exp( -(x**2 + y**2)/(2*(descriptorSigma**2)) )/( 2*np.pi * (descriptorSigma**2) ),dtype=cl.cltypes.float)
			# Allocate the gaussian kernel to GPU memory.
			gGaussianKernel = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gaussianKernel)
			# To generate descriptors, we need the features and the scale.
			args = (
				gDescriptors,
				gImageSize,
				gGaussianKernel,
				gradientMaps[0],
				gradientMaps[1],
				gradientMaps[2],
				gradientMaps[3],
				gradientMaps[4]
			)
			# Generate the descriptors for the stable features.
			program.KeypointDescriptors(self.queue,(nFeatures,),None,*(args))
			# Copy the descriptors back.
			cl.enqueue_copy(self.queue, descriptors, gDescriptors)
			descriptors = descriptors.reshape(nFeatures,132)
			# Make them scale correctly to the original image.
			# if subSamplingFactor > 1: descriptors[:,:2] *= subSamplingFactor
			# Assign the octave number to the keypoint.
			descriptors[:,2] = subSamplingFactor
			# Save them to the global descriptors.
			arrayDescriptors.append(descriptors)

		"""
		Comments
		--------
		-	I am unsure whether it is useful to allocate memory to the GPU for this and just re-use it and if it is bigger than needed then so be it ...
			... or whether it is useful to copy down, assess and then allocate more memory as we go.
			+	I think memory allocation is expensive and time consuming. So maybe it is better to initialise the data first and then just reduce how much of it we use.
		-	I think I need to re-visit scale, k*sigma where k = 2^(1/s).
		-	The Gradient and Orientation assignment could be done by re-using the DoG memory?
		- 	Is it better to do Grad and Ori assignment for each point or pre-compute it for an entire array?

		References used
		---------------
		2D Implenetation:
			https://dsp.stackexchange.com/questions/10403/sift-taylor-expansion
			https://math.stackexchange.com/questions/302160/correct-way-to-calculate-numeric-derivative-in-discrete-time
			http://vnit.ac.in/ece/wp-content/uploads/2019/10/lecture10_1.pdf
			https://robo.fish/wiki/images/5/58/Image_Features_From_Scale_Invariant_Keypoints_Lowe_2004.pdf
		3D Implementation:
			Allaire, S., Kim, J. J., Breen, S. L., Jaffray, D. A., & Pekar, V. (2008). Full orientation invarlance and improved feature selectivity of 3D SIFT with application to medical image analysis. 2008 IEEE Computer Society Conference on Computer Vision and Pattern Recognition Workshops, CVPR Workshops. https://doi.org/10.1109/CVPRW.2008.4563023
		"""

		if len(arrayDescriptors) > 0:
			arrayDescriptors = np.vstack(arrayDescriptors)

		logging.info("Returning {} keypoints.".format(len(arrayDescriptors)))
		return array, arrayDescriptors

	def SIFT3D(self,array):
		# Array will be signed two's complement 16-bit integer.
		# array = np.ascontiguousarray(array,dtype=datatype)

		logging.warning("Not implemented yet, doing nothing.")

		return None

	# def nnMatch