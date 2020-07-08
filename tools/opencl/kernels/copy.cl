__kernel void copy(
		__global const int *gpuIn,
		__global int *gpuOut
	)
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

	// Push data to new point.
	gpuOut[idx] = gpuIn[idx];
}