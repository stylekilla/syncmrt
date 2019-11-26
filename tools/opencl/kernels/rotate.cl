__kernel void rotate3d(
	__global const int *gpuIn,
	__global const float *gpuRotation,
	__global int *gpuOut,
	__global const int *gpuOutShape)
{
	// Get global xyz ID's.
	int x = get_global_id(0);
	int y = get_global_id(1);
	int z = get_global_id(2);

	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	int szz = get_global_size(2);

	// Get the ID number of the thread.
	int idx = z + (szz * y) + (szz * szy * x);

	// Get input origin (center of array).
	float inputOrigin[3] = {
		(szx-1)/2,
		(szy-1)/2,
		(szz-1)/2
	};

	// Move thread with respect to input origin.
	float i = x - inputOrigin[0];
	float j = y - inputOrigin[1];
	float k = z - inputOrigin[2];

	// Rotate points (active rotation?).
	float point[3] = {
		i*gpuRotation[0] + j*gpuRotation[1] + k*gpuRotation[2],
		i*gpuRotation[3] + j*gpuRotation[4] + k*gpuRotation[5],
		i*gpuRotation[6] + j*gpuRotation[7] + k*gpuRotation[8]
	};

	// New origin based of output shape size.
	float outOrigin[3] = {
		(gpuOutShape[0]-1)/2,
		(gpuOutShape[1]-1)/2,
		(gpuOutShape[2]-1)/2
	};

	// Relocate point in output shape.
	int newPoint[3] = {
		(int)(point[0] + 0.5 + outOrigin[0]),
		(int)(point[1] + 0.5 + outOrigin[1]),
		(int)(point[2] + 0.5 + outOrigin[2])
	};

	// idx is the new point id.
	int idxNew = newPoint[2] + 
		(gpuOutShape[2] * newPoint[1]) +
		(gpuOutShape[2] * gpuOutShape[1] * newPoint[0]);

	// Check if index is inside data region. If not, set it to the maximum index.
	if(idxNew > (gpuOutShape[0]*gpuOutShape[1]*gpuOutShape[2]) - 1)
	{
		idxNew = (gpuOutShape[0]*gpuOutShape[1]*gpuOutShape[2]) - 1;
	};
	// Push data to new point.
	gpuOut[idxNew] = gpuIn[idx];
}