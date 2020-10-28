import pyopencl as cl
import numpy as np
import logging
import os, inspect

logging.info("Adding MPL support for debugging.")
from matplotlib import pyplot as plt

# os.environ['PYOPENCL_NO_CACHE'] = '1'
# os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

# Supress pyopencl debugging output. NOT WORKING.
ocl_logger = logging.getLogger('cl')
ocl_logger.setLevel(logging.CRITICAL)

class gpu:
	def __init__(self):
		"""
		1. Initialise some parameters
		2. Find a suitable device
		3. Create a context and queue_gpu for work to take place in
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

		self.ctx_cpu = cl.Context(devices=cpu)
		self.ctx_gpu = cl.Context(devices=gpu)
		logging.debug('Using {} (CPU) and {} (GPU) for computation.'.format(cpu[0],gpu[0]))
			
		# Create a device queue_gpu.
		self.queue_cpu = cl.CommandQueue(self.ctx_cpu)
		self.queue_gpu = cl.CommandQueue(self.ctx_gpu)

	def _generateDeviceMemoryObjects(self,context,size,amount):
		""" Return a list of references to new memory objects. """
		buffers = []
		for i in range(amount):
			buffers.append( cl.Buffer(context, cl.mem_flags.READ_WRITE, size=size) )
		return buffers

	def findFeaturesSIFT(self,array):
		""" Implementation of Lowe 2004 and Allaire 2008 """
		if len(array.shape) == 2:
			return self.SIFT2D(array)
		elif len(array.shape) == 3:
			return self.SIFT3D(array)
		else:
			raise Exception("Cannot find features with SIFT for array with {} dimensions. Only 2 or 3 dimensions are accepted.".format(len(array.shape)))

	def SIFT2D(self,array):
		logging.info("Starting SIFT 2D algorithm on GPU.")
		# Variable inputs:
		sigma = np.sqrt(2)/2
		lowerDataThreshold = 0.0
		# Use 8-bit for now... can up to 16-bit images later.
		bits = 8
		# Our rejection threshold is 3% of half the available bit space.
		contrastRejectionThreshold = 0.03*(2**bits)/2

		# Fixed inputs:
		# Number of octaves = 3
		nScaleLevels = 6

		# Ideally, here we would filter out HU values that are not useful to us.
		array[array<lowerDataThreshold] = 0.0
		# Array will be signed two's complement 16-bit integer.
		array = np.ascontiguousarray(array,dtype=cl.cltypes.short)

		# Memory overhead.
		mf = cl.mem_flags
		# Keep the original array in the CPU RAM.
		gArray = cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.USE_HOST_PTR, hostbuf=array)

		# Get kernel source.
		fp = os.path.dirname(inspect.getfile(gpu))
		kernel = open(fp+"/tools/opencl/kernels/sift2d.cl", "r").read()
		# Compile kernel.
		program = cl.Program(self.ctx_gpu,kernel).build()

		"""
		STEP 1: Calculate scale images (Gaussian Convolution)
		"""
		# Memory overhead.
		octavesShape = [array.shape, tuple(np.array(np.array(array.shape)/2,dtype=int)), tuple(np.array(np.array(array.shape)/4,dtype=int))]
		subSamplingFactors = [1,2,4]
		octaveScaleImages = [
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[0]),nScaleLevels),
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[1]),nScaleLevels),
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[2]),nScaleLevels)
		]
		octaveDogImages = [
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[0]),nScaleLevels),
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[1]),nScaleLevels),
			self._generateDeviceMemoryObjects(self.ctx_gpu,int(array.nbytes/subSamplingFactors[2]),nScaleLevels)
		]

		# Iterate over all octaves and scales.
		for scaleImage,dogImage,kernelShape,subSamplingFactor in zip(octaveScaleImages,octaveDogImages,octavesShape,subSamplingFactors):
			logging.info("Starting calculations for Octave {}.".format(subSamplingFactors.index(subSamplingFactor)+1))
			# We are now on a per-octave level.
			# If our octave requires resampling, do it.
			if subSamplingFactor > 1:
				logging.info("Subsampling array at {} intervals.".format(subSamplingFactor))
				imageArray = cl.Buffer(self.ctx_gpu, mf.READ_WRITE, size=int(array.nbytes/subSamplingFactor))
				# Program args.
				args = (
					gArray,
					imageArray,
					cl.cltypes.int(subSamplingFactor)
				)
				# Run the program
				program.SubSample(self.queue_gpu,kernelShape,None,*(args))
			else:
				# Otherwise, just pass the original data on.
				imageArray = gArray

			"""
			STEP 1.1: SCALE IMAGES (GAUSSIAN BLUR).
			"""
			# Calculate scale images.
			for i in range(nScaleLevels):
				# We are now on a per-buffer level within an octave.
				gScaleImage = scaleImage[i]
				# k, our factor in which we scale sigma by.
				k = np.sqrt(2)**i
				# Our sigma for this image.
				sig = sigma*subSamplingFactor*k
				logging.info("Calculating Scale Image {} with sigma {}.".format(i+1,sig))
				# Choose a filter width that is rounded up to the next odd integer.
				filterWidth = cl.cltypes.int( int(3*sig + (3*(sig)+1)%2) )
				# Calculate an offset for the filter so that it is centred about zero (i.e. so it goes from -1,0,+1 instead of 0,1,2...).
				filterOffset = (filterWidth-1)/2
				# Calculate xy values for filter (centred on zero, as described above).
				x,y = np.indices((filterWidth,filterWidth))-filterOffset
				# Generate gaussian kernel.
				gaussianKernel = np.array(np.exp( -(x**2 + y**2)/(2*(sig)**2) )/( 2*np.pi * (sig)**2 ),dtype=cl.cltypes.float)
				# Allocate the gaussian kernel to GPU memory.
				gGaussianKernel = cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gaussianKernel)
				# Program args.
				args = (
					gArray,
					gGaussianKernel,
					filterWidth,
					gScaleImage
				)
				# Run the program
				program.Gaussian2D(self.queue_gpu,kernelShape,None,*(args))


			"""
			STEP 1.2: DIFFERENCE OF GAUSSIAN.
			"""
			# Calculate Difference of Gaussian.
			for i,j in zip(range(0,nScaleLevels-1),range(1,nScaleLevels)):
				logging.info("Calculating Difference of Gaussian between scale images {} and {}.".format(i+1,j+1))
				# Grab pairs of octaves and a dog image to fill in.
				args = (
					scaleImage[i],
					scaleImage[j],
					dogImage[i]
				)
				program.Difference(self.queue_gpu,kernelShape,None,*(args))

			"""
			STEP 1.3: GENERATE GRADIENT MAPS.
			"""
			# Gradient maps are an (m,n,2) array). Their size is the shape product times the cl datatype.
			nbytes = np.prod(kernelShape) * np.dtype(cl.cltypes.float).itemsize * 2
			gradientMaps = self._generateDeviceMemoryObjects(self.ctx_gpu,nbytes,nScaleLevels)
			# Create one gradient map for each scale image.
			for idx in range(nScaleLevels):
				args = (
					scaleImage[idx],
					gradientMaps[idx]
				)
				program.GenerateGradientMap(self.queue_gpu,kernelShape,None,*(args))

			# # START PLOT DEBUGING
			# tempArray = np.zeros(616*1216*2,dtype=cl.cltypes.float)
			# cl.enqueue_copy(self.queue_gpu, tempArray, gradientMaps[5])
			# tempArray = tempArray.reshape(616,1216,2)
			# # print(tempArray[:10])
			# # tempArray = tempArray.reshape(array.shape)
			# fig, (ax1,ax2) = plt.subplots(1,2)
			# # ax1.imshow(array)
			# ax1.imshow(tempArray[:,:,0])
			# ax2.imshow(tempArray[:,:,1])
			# plt.show()
			# exit()
			# # END PLOT DEBUGING		



			"""
			STEP 2.1: FIND KEYPOINTS
			"""
			# Create features map.
			features = np.zeros(array.shape,dtype=cl.cltypes.int)
			gFeatures = cl.Buffer(self.ctx_gpu, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=features)
			# For each Dog map, find the local minima and maxima.
			for i in range(1,len(dogImage)-1):
				logging.info("Finding local extrema in DoG Images {} to {}.".format(i,i+2))
				gDog1 = dogImage[i-1]
				gDog2 = dogImage[i]
				gDog3 = dogImage[i+1]
				# Program args.
				args = (
					gDog1,
					gDog2,
					gDog3,
					cl.cltypes.int(i),
					gFeatures
				)
				# These will write the scale factor, s, at the xy position in which the extrema was found.
				program.FindLocalMinima(self.queue_gpu,kernelShape,None,*(args))
				program.FindLocalMaxima(self.queue_gpu,kernelShape,None,*(args))
			# Bring back our list of features.
			cl.enqueue_copy(self.queue_gpu, features, gFeatures)
			# Features array is no longer required.
			gFeatures.release()

			"""
			STEP 2.2: FIND STABLE KEYPOINTS
			"""
			# Find out how many features there were. The function np.nonzero() searches the array for all non zero values and returns their positions.
			x,y = np.nonzero(features)
			# This grabs the scale values at those non-zero positions.
			scale = features[tuple([x,y])]
			# Now we know how many features we have identified in this octave.
			nFeatures = len(x)
			# Create a keypoint tracker that allows for (x,y,sigma,36-bin orientation histogram).
			keypoints = np.zeros((nFeatures,3),dtype=cl.cltypes.float)
			# Assign (x,y,scale) to each keypoint.
			keypoints[:,0] = x
			keypoints[:,1] = y
			keypoints[:,2] = scale

			logging.info("Found {} initial keypoints.".format(nFeatures))

			# Assign gpu memory for the featurelist. This will be the main call of our kernel.
			gKeypoints = cl.Buffer(self.ctx_gpu, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=keypoints)
			# We also need to pass the kernel information on how big the images are. For each octave this has been previously described as kernelShape.
			imageSize = np.array(kernelShape,dtype=cl.cltypes.int)
			gImageSize = cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=imageSize)
			# Now we want to refine the local positions with sub-pixel accuracy and identify the stable features.
			args = (
				gKeypoints,
				gImageSize,
				cl.cltypes.float(contrastRejectionThreshold),
				dogImage[0],
				dogImage[1],
				dogImage[2],
				dogImage[3],
				dogImage[4]
			)
			program.LocateStableFeatures(self.queue_gpu,(nFeatures,),None,*(args))

			# Bring back our list of stable features.
			cl.enqueue_copy(self.queue_gpu, keypoints, gKeypoints)
			gKeypoints.release()

			# START PLOT DEBUGING
			# fig, ax = plt.subplots(1,1)
			# ax.imshow(array)
			# ax.scatter(featureList[:,1],featureList[:,0],c='k',marker='x')
			# plt.show()
			# exit()
			# END PLOT DEBUGING

			"""
			STEP 2.3: ASSIGN OREITNATION TO KEYPOINTS.
			"""
			# Reduce the feature list into valid components. Remove everything set to (0,0,0).
			mask = np.all(keypoints>0,axis=1)
			temp = keypoints[mask]
			nFeatures = len(temp)

			logging.info("Identified {} stable keypoints.".format(nFeatures))

			# Create a keypoint tracker that allows for (x,y,sigma,36-bin orientation histogram).
			keypoints = np.zeros((nFeatures,39),dtype=cl.cltypes.float)
			keypoints[:,:3] = temp
			# Re-assign GPU space.
			gKeypoints = cl.Buffer(self.ctx_gpu, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=keypoints)

			# Gaussian kernels for each scale level.
			gaussianKernels = []
			kernelSizes = []
			for i in range(nScaleLevels):
				# Calculate the Gaussian kernels...
				k = np.sqrt(2)**i
				sig = 1.5*sigma*subSamplingFactor*k
				filterWidth = int(3*sig + (3*(sig)+1)%2)
				filterOffset = (filterWidth-1)/2
				x,y = np.indices((filterWidth,filterWidth))-filterOffset
				kernel = np.array(np.exp( -(x**2 + y**2)/(2*(sig)**2) )/( 2*np.pi * (sig)**2 ),dtype=cl.cltypes.float)
				# Save the kernel and it's width.
				gaussianKernels.append(kernel)
				kernelSizes.append(filterWidth)

			gaussianKernelBuffers = []
			for kernel in gaussianKernels:
				gaussianKernelBuffers.append(cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=kernel))

			kernelSizes = np.array(kernelSizes, dtype=cl.cltypes.int)
			gGaussianWidths = cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=kernelSizes)

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
				gradientMaps[5],
				gaussianKernelBuffers[0],
				gaussianKernelBuffers[1],
				gaussianKernelBuffers[2],
				gaussianKernelBuffers[3],
				gaussianKernelBuffers[4],
				gaussianKernelBuffers[5]
			)
			# Generate the descriptors for the stable features.
			program.KeypointOrientations(self.queue_gpu,(nFeatures,),None,*(args))

			# Bring back our list of stable features.
			cl.enqueue_copy(self.queue_gpu, keypoints, gKeypoints)

			# print(keypoints[0])
			# tempArray = np.zeros(616*1216*2,dtype=cl.cltypes.float)
			# cl.enqueue_copy(self.queue_gpu, tempArray, gradientMaps[int(kepoints[0][2])])
			# tempArray = tempArray.reshape(616,1216,2)
			# print(tempArray[16:25,465:474,0])
			# print(tempArray[16:25,465:474,1])
			# fig, ax = plt.subplots(1,1)
			# ax.bar(np.arange(0,360,10),keypoints[0][3:])
			# plt.show()

			exit()



			# Make a descriptors array that is (n,2 + {8*4*4}). That is (x,y,8x4x4 descriptor array).
			descriptors = np.zeros((nFeatures,130),dtype=cl.cltypes.float)
			# Assign the known information to the descriptors (x,y,sigma).
			descriptors[:,:3] = featureList
			# Copy it to the gpu.
			gDescriptors = cl.Buffer(self.ctx_gpu, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=descriptors)

			# Create a Gaussian weighting function unique to the scale level...?
			# Choose a filter width (16 x 16 window).
			# filterWidth = cl.cltypes.int(8)
			# Calculate an offset for the filter so that it is centred about zero (i.e. so it goes from -1,0,+1 instead of 0,1,2...).
			# filterOffset = (filterWidth-1)/2
			# Calculate xy values for filter (centred on zero, as described above).
			# x,y = np.indices((filterWidth,filterWidth))-filterOffset
			# Generate gaussian kernel.
			# gaussianKernel = np.array(np.exp( -(x**2 + y**2)/(2*(k*sigma)**2) )/( 2*np.pi * (k*sigma)**2 ),dtype=cl.cltypes.float)
			# Allocate the gaussian kernel to GPU memory.
			# gGaussianKernel = cl.Buffer(self.ctx_gpu, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gaussianKernel)
			# To generate descriptors, we need the features and the scale.
			args = (
				gDescriptors,
				gImageSize,
				gradientMaps[0],
				gradientMaps[1],
				gradientMaps[2],
				gradientMaps[3],
				gradientMaps[4],
				gradientMaps[5]
			)
			# Generate the descriptors for the stable features.
			program.KeypointOrientations(self.queue_gpu,(nFeatures,),None,*(args))

			cl.enqueue_copy(self.queue_gpu, descriptors, gDescriptors)
			descriptors = descriptors.reshape(nFeatures,130)
			# for n in range(nFeatures):
			print(descriptors[0][:10])
			exit()
			# # START PLOT DEBUGING
			# fig, ax = plt.subplots(1,1)
			# ax.imshow(array)
			# ax.scatter(featureList[:,1],featureList[:,0],c='k',marker='x')
			# plt.show()
			# exit()
			# # END PLOT DEBUGING

			# Make a descriptors array that is (n,2 + {8*4*4}). That is (x,y,8x4x4 descriptor array).
			descriptors = np.zeros((nFeatures,130),dtype=cl.cltypes.float)
			# Assign the known information to the descriptors (x,y,sigma).
			descriptors[:,:3] = featureList
			# Copy it to the gpu.
			gDescriptors = cl.Buffer(self.ctx_gpu, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=descriptors)

			# To generate descriptors, we need the features and the scale.
			args = (
				gDescriptors,
				gImageSize,
				gradientMaps[0],
				gradientMaps[1],
				gradientMaps[2],
				gradientMaps[3],
				gradientMaps[4],
				gradientMaps[5]
			)
			# Generate the descriptors for the stable features.
			program.GenerateDescriptors(self.queue_gpu,(nFeatures,),None,*(args))


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

		return None

	def SIFT3D(self,array):
		# Array will be signed two's complement 16-bit integer.
		# array = np.ascontiguousarray(array,dtype=cl.cltypes.short)

		logging.warning("Not implemented yet, doing nothing.")

		return None