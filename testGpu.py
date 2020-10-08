import pyopencl as cl
import numpy as np
import logging
import os, inspect

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
			buffer.append( cl.Buffer(context, mf.READ_WRITE, size=size) )
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
		sigma = 1.0
		lowerDataThreshold = 0.0

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
		octavesSize = [array.size, int(array.size/2), int(array.size/4)]
		octaveScaleImages = [
			_generateDeviceMemoryObjects(context,octaveSize[0],nScaleLevels),
			_generateDeviceMemoryObjects(context,octaveSize[1],nScaleLevels),
			_generateDeviceMemoryObjects(context,octaveSize[2],nScaleLevels)
		]
		octaveDogImages = [
			_generateDeviceMemoryObjects(context,octaveSize[0],nScaleLevels-1),
			_generateDeviceMemoryObjects(context,octaveSize[1],nScaleLevels-1),
			_generateDeviceMemoryObjects(context,octaveSize[2],nScaleLevels-1)
		]

		# Iterate over all octaves and scales.
		for scaleImage,dogImage,kernelShape in zip(octaveScaleImages,octaveDogImages,octavesShape):
			# We are now on a per-octave level.
			# Calculate scale images.
			for i in range(nScaleLevels):
				# We are now on a per-buffer level within an octave.
				gScaleImage = scaleImage[i]
				# Scale, k, should start at 1, not 0.
				k = i+1
				# Choose a filter width that is rounded up to the next odd integer.
				filterWidth = cl.cltypes.int( 3*(k*sigma) + (3*(k*sigma)+1)%2 )
				# Calculate an offset for the filter so that it is centred about zero (i.e. so it goes from -1,0,+1 instead of 0,1,2...).
				filterOffset = (filterWidth-1)/2
				# Calculate xy values for filter (centred on zero, as described above).
				x,y = np.indices((filterWidth,filterWidth))-filterOffset
				# Generate gaussian kernel.
				gaussianKernel = np.array(np.exp( -(x**2 + y**2)/(2*(k*sigma)**2) )/( 2*np.pi * (k*sigma)**2 ),dtype=cl.cltypes.float)
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
			# Calculate Difference of Gaussian.
			for i,j in zip(range(0,nScaleLevels-1),range(1,nScaleLevels)):
				# Grab pairs of octaves and a dog image to fill in.
				args = (
					scaleImage[i],
					scaleImage[j],
					dogImage
				)
				program.Difference(self.queue_gpu,kernelShape,None,*(args))				

		"""
		STEP 2: Locate stable local extrema positions.
		"""

		# Find local extrema in DoG's.
		gExtrema = cl.Buffer(self.ctx_gpu, mf.READ_WRITE, size=array.size)
		for i in range(1,len(octave1dog)-1):
			gArray1 = octave1dog[i-1]
			gArray2 = octave1dog[i]
			gArray3 = octave1dog[i+1]
			# Program args.
			args = (
				gArray1,
				gArray2,
				gArray3,
				i,
				gExtrema
			)
			program.FindLocalMinima(self.queue_gpu,array.shape,None,*(args))
			program.FindLocalMaxima(self.queue_gpu,array.shape,None,*(args))
			program.RefineLocalPositions(self.queue_gpu,array.shape,None,*(args))
			program.LocateStableFeatures(self.queue_gpu,array.shape,None,*(args))
			program.GenerateDescriptors(self.queue_gpu,array.shape,None,*(args))


		# Remove low contrast extrema.
		# https://dsp.stackexchange.com/questions/10403/sift-taylor-expansion
		# https://math.stackexchange.com/questions/302160/correct-way-to-calculate-numeric-derivative-in-discrete-time

		# Eliminate edge responses.

		return None

	def SIFT3D(self,array):
		# Array will be signed two's complement 16-bit integer.
		array = np.ascontiguousarray(array,dtype=cl.cltypes.short)