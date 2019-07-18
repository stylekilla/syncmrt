// __kernel __attribute__((overloadable)) void rotate(
__kernel void rotate(__global const float *in,
					__global const float *active,
					__global const float *passive,
					__global float *out,
					const float outShape)
{
	// Get global xyz ID's.
	int x = get_global_id(0);
	int y = get_global_id(1);
	int z = get_global_id(2);

	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	int szz = get_global_size(2);

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

	// printf("Global ID (%i %i %i) \n",x,y,z);
	// printf("Input Size (%i %i %i) \n",szx,szy,szz);
	// printf("Input origin (%f %f %f) \n",inputOrigin[0],inputOrigin[1],inputOrigin[2]);
	// printf("Origin centered point (%f %f %f) \n",i,j,k);
	// printf("GPU Rotation (%f) \n",active[5]);
	// printf("Input Array (%f) \n",in[0]);

	// Rotate points (active).
	float point[3] = {
		i*active[0] + j*active[1] + k*active[2],
		i*active[3] + j*active[4] + k*active[5],
		i*active[6] + j*active[7] + k*active[8]
	};

	// Rotate points again (passive).
	float point2[3] = {
		point[0]*passive[0] + point[1]*passive[1] + point[2]*passive[2],
		point[0]*passive[3] + point[1]*passive[4] + point[2]*passive[5],
		point[0]*passive[6] + point[1]*passive[7] + point[2]*passive[8]
	};

	// printf("Rotated Point: %f,%f,%f \n",point[0],point[1],point[2]);

	// New origin based of output shape size.
	float outOrigin[3] = {
		(outShape[0]-1)/2,
		(outShape[1]-1)/2,
		(outShape[2]-1)/2
	};

	// printf("Output Origin: %f,%f,%f \n",outOrigin[0],outOrigin[1],outOrigin[2]);

	// Relocate point in output shape.
	int newPoint[3] = {
		(int)round(point2[0] + outOrigin[0]),
		(int)round(point2[1] + outOrigin[1]),
		(int)round(point2[2] + outOrigin[2])
	};

	// printf("New Point: %i,%i,%i \n",newPoint[0],newPoint[1],newPoint[2]);

	int idx = newPoint[2] + 
		(outShape[2] * newPoint[1]) +
		(outShape[2] * outShape[1] * newPoint[0]);

	// printf("Idx: %i",idx);

	int idx2 = z + (szz * y) + (szz * szy * x);

	// printf("New Point: %i,%i.%i",newPoint[0],newPoint[1],newPoint[2]);

	if (idx < (outShape[0]*outShape[1]*outShape[2])) {
		out[idx] = in[idx2];
	}
	else {
	}

}











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
		i*gpuRotation[0] + j*gpuRotation[3] + k*gpuRotation[6],
		i*gpuRotation[1] + j*gpuRotation[4] + k*gpuRotation[7],
		i*gpuRotation[2] + j*gpuRotation[5] + k*gpuRotation[8]
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