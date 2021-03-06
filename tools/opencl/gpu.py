import pyopencl as cl
import numpy as np
import inspect, os
from tools.math import wcs2wcs
import logging

'''
This uses OpenCL for GPU parallel methods.
OpenCL is understood to be a Right-Handed Coordinate system, which is good for us.
Written ocl kernels are stored in ./kernels.
Workflow is:
	1. Initialise GPU class
	2. Copy data to device to be used
	3. Run a kernel on that data
	4. Recieve an output
'''

class gpu:
	def __init__(self):
		'''
		1. Initialise some parameters
		2. Find a suitable device
		3. Create a context and queue for work to take place in
		'''
		# Some class members.
		self.pixelSize = None
		self.isocenter = None
		self.extent = None
		self.zeroExtent = False

		# Find avail devices.
		platforms = cl.get_platforms()
		cpuList = []
		gpuList = []
		for plt in platforms:
			cpuList += plt.get_devices(cl.device_type.CPU)
			gpuList += plt.get_devices(cl.device_type.GPU)
		# Create a device context.
		chosenDevice = None
		for device in gpuList:
			try:
				# if device.vendor.contains('NVIDIA'):
				chosenDevice = [device]  
					# self.ctx = cl.Context(devices=[device])
			except:
				pass
		if chosenDevice is None:
			# Use the CPU if no GPU found.
			chosenDevice = [cpuList[0]]
		else:
			pass

		self.ctx = cl.Context(devices=chosenDevice)
		logging.info('Using '+ str(chosenDevice) +' for computation.')
			
		# Create a device queue.
		self.queue = cl.CommandQueue(self.ctx)

	def loadData(self,data,extent=None):
		""" Load an array onto the GPU. """
		array = np.array(data,order='C').astype(np.int32)
		self._inputBuffer = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=array)
		self._inputBufferShape = np.shape(array)
		# If an extent for the array is specified, save that too.
		if (type(extent) != type(None)) & (len(np.array(extent).shape) == 6): 
			self._inputExtent = extent
		# Set an output buffer.
		self._outputBuffer = None
		self._outputBufferShape = None

	def getData(self):
		""" Should return the last calculated output. """
		# Only do this if there is an outputBuffer.
		if type(self._outputBuffer) is type(None):
			return
		else:
			arrOut = np.zeros(self._outputBufferShape)
			cl.enqueue_copy(self.queue, arrOut, self._outputBuffer)
			return arrOut

	def rotate(self,rotationMatrix):
		"""
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce datatypes as we are dealing with c and memory access/copies.
		Rotations happen about a pre-defined world coordinate system (x,y,z) axes (as according to HFS patient position in DICOM standard).
		"""
		# OpenCL Coordinate System w.r.t WCS.
		OCS = np.array([[0,-1,0],[-1,0,0],[0,0,-1]])
		# Put the rotation matrix in the context of the OCL CS, then take it back into the frame of reference of the origin RCS.
		gpuRotationMatrix = (OCS@rotationMatrix)@np.linalg.inv(OCS)
		# Create a basic box for calculations of a cube. Built off (row,cols,depth).
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
		# Input array shape
		inputShape =  basicBox*self._inputBufferShape
		# Output array shape after rotation.
		outputShape = np.empty((8,3),dtype=float)
		for i in range(8):
			outputShape[i,:] = gpuRotationMatrix@inputShape[i,:]
		mins = np.absolute(np.amin(outputShape,axis=0))
		maxs = np.absolute(np.amax(outputShape,axis=0))
		outputShape = np.rint(mins+maxs).astype(int)
		# Create empty output array set to -1000.
		arrOut = np.zeros(outputShape).astype(np.int32)-1000
		# Swap the x and y size of the arr shape.
		arrOutShape = np.array(arrOut.shape).astype(np.int32)
		"""
		The GPU wizardry:
			- First we do the data transfer from host to device.
			- Then we run the program.
			- Then we get the results.
		"""
		# Create memory flags.
		mf = cl.mem_flags
		# GPU buffers.
		gpuRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gpuRotationMatrix.astype('float32'))
		self._outputBuffer = cl.Buffer(self.ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOut)
		self._outputBufferShape = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOutShape)
		# Get kernel source.
		fp = os.path.dirname(inspect.getfile(gpu))
		kernel = open(fp+"/kernels/rotate.cl", "r").read()
		# Compile kernel.
		program = cl.Program(self.ctx,kernel).build()
		# Kwargs
		kwargs = ( self._inputBuffer,
			gpuRotation,
			self._outputBuffer,
			self._outputBufferShape
		)
		# Run the program.
		# __call__(queue, global_size, local_size, *args, global_offset=None, wait_for=None, g_times_l=False)
		program.rotate3d(self.queue,self._inputBufferShape,None,*(kwargs))
		# Get results
		cl.enqueue_copy(self.queue, arrOut, self._outputBuffer)
		# Remove any dirty array values in the output.
		# arrOut = np.nan_to_num(arrOut)
		return arrOut

	def copy(self):
		arrOut = np.zeros(self._inputBufferShape).astype(np.int32)-1000
		# arrOutShape = np.array(arrOut.shape).astype(np.int32)
		'''
		The GPU wizardry:
			- First we do the data transfer from host to device.
			- Then we run the program.
			- Then we get the results.
		'''
		# Create memory flags.
		mf = cl.mem_flags
		# GPU buffers.
		gpuOut = cl.Buffer(self.ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOut)
		# Get kernel source.
		fp = os.path.dirname(inspect.getfile(gpu))
		kernel = open(fp+"/kernels/copy.cl", "r").read()
		# Compile kernel.
		program = cl.Program(self.ctx,kernel).build()
		# Kwargs
		kwargs = ( self._inputBuffer,
			gpuOut
		)
		# Run the program.
		program.copy(self.queue,self._inputBufferShape,None,*(kwargs))
		# Get results
		cl.enqueue_copy(self.queue, arrOut, gpuOut)
		# Remove any dirty array values in the output.
		arrOut = np.nan_to_num(arrOut)
		return arrOut

	def generateRotationMatrix(self,rotationList):
		"""
		Generate a 3x3 rotation matrix.
		Here we make the following assumptions:
			- Axes are 0/1/2 which match real world x/y/z which match python y/x/z (as python is row-major).
			- Inputs are a list of strings in the format of: 
				- '190' means take the first axis, '1' and rotate '90' degrees about it.
				- '0-90' means take the first axis, '0' and rotate '-90' degrees about it.
		"""
		# Begin with identity matrix.
		pymat = np.identity(3)
		gpumat = np.identity(3)
		# Iterate through desired rotations.
		# CW IS NEGATIVE 
		# CCW IS POSITIVE (AS PER TRIG CIRCLE)
		for i in range(len(rotationList)):
			axis = int(rotationList[i][0])
			value = np.deg2rad(float(rotationList[i][1:]))
			if axis == 0:
				# Rotation about real world x.
				py = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
				# py = np.array([[1,0,0],[0,np.cos(value),np.sin(value)],[0,-np.sin(value),np.cos(value)]])
				# Rotation about real world y (GPU x).
				gpu = np.array([[np.cos(value),0,-np.sin(value)],[0,1,0],[np.sin(value),0,np.cos(value)]])
			elif axis == 1:
				# Rotation about real world y.
				py = np.array([[np.cos(value),0,np.sin(value)],[0,1,0],[-np.sin(value),0,np.cos(value)]])
				gpu = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
			elif axis == 2:
				# Rotation about real world z.
				py = np.array([[np.cos(value),-np.sin(value),0],[np.sin(value),np.cos(value),0],[0,0,1]])
				gpu = np.array([[np.cos(value),np.sin(value),0],[-np.sin(value),np.cos(value),0],[0,0,1]])
			else:
				py = np.identity(3)
				gpu = np.identity(3)
			# Multiply into final matrix.
			pymat = pymat@py
			gpumat = gpumat@gpu

		return np.array(pymat).astype(np.float32), np.array(gpumat).astype(np.float32)

	def rotateWithOffset(self,point,rotation,offset):
		'''
		Rotate a point about an offset.
		'''
		# Rotation matrix.
		R = np.identity(4)
		R[:3,:3] = rotation
		# Translation matrix.
		T = np.identity(4)
		T[:3,3] = -offset
		# Inverse translation.
		Ti = np.identity(4)
		# Ti[:3,3] = offset
		Ti[:3,3] = (R@np.hstack([offset,1]))[:3]
		# Make the point.
		p = np.hstack([point,1])
		# Translate, rotate, and reposition the point.
		P = T@p
		P = R@P
		P = Ti@P

		# P = T@R@Ti@p

		return P[:3]

