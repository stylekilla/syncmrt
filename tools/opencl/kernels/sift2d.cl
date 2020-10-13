// Implementation of Lowe 2004.

__kernel void Gaussian2D(
	__global const short *gArray,
	__global const float *gGaussianKernel,
	const int filterWidth,
	__global short *gScaleImage
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	// Temporary value storage.
	float value = 0;
	// Iterate over the entire filter, boundary conditions are handled within.
	for (int i=0; i<filterWidth; i++) {
		for (int j=0; j<filterWidth; j++) {
			// Calculate the offsets.
			int dx = -((filterWidth-1)/2)+i;
			int dy = -((filterWidth-1)/2)+j;
			// Calculate new x and y (with offset).
			int nx = x+dx;
			int ny = y+dy;
			// If we are past the boundaries, reflect.
			if (nx < 0) {
				nx = -nx;
			}
			if (ny < 0) {
				ny = -ny;
			}
			if (nx >= szx) {
				nx = szx + (szx - nx - 1);
				// printf("(x,y)=%i,%i   (szx,szy)=%i,%i \n",x,y,szx,szy);
			}
			if (ny >= szy) {
				ny = szy + (szy - ny - 1);
			}
			// Add the result.
			value += gArray[ny + szy*nx] * gGaussianKernel[j + filterWidth*i];
		}
	}
	// Need to keep as float until final writing. Convert to short.
	gScaleImage[idx] += convert_short(value);
} // End Gaussian2D


__kernel void SubSample(
	__global const short *gInputArray,
	__global short *gOutputArray,
	const int amount
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	// int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	int idxSample = (y+amount) + szy*(x+amount);
	// Copy the sample value across.
	gOutputArray[idx] = gInputArray[idxSample];
} // End SubSample


__kernel void Difference(
	__global const short *gArray1,
	__global const short *gArray2,
	__global short *gDifference
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	// int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	// Save the difference.
	gDifference[idx] = gArray2[idx] - gArray1[idx];
} // End Difference


__kernel void FindLocalMinima(
	__global const short *gDog1,
	__global const short *gDog2,
	__global const short *gDog3,
	const int s,
	__global int *gFeatures
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	// We will not search for anything <= 3 elements of the edge of the array. This is because when we generate descriptors, we must have 3 elements of information in each direction.
	if (x > 3 && x < (szx-3) && y > 3 && y < (szy-3)) {
		// Get the value to compare to.
		short value = gDog2[idx];
		// Look at all 26 neighbours.
		for (int i=-1; i <= 1; i++) {
			for (int j=-1; j <= 1; j++) {
				// Create a test index, offset by 1 in each direction.
				int testIdx = (y+j) + szy*(x+i);
				if (testIdx == idx) {
					// If our test index is the same as our array index, we only need to check arrays 1 and 3.
					if (value >= gDog1[testIdx] || value >= gDog3[testIdx]) {
						return;
					}
				}
				else {
					if (value >= gDog1[testIdx] || value >= gDog2[testIdx] || value >= gDog3[testIdx]) {
						return;
					}
				}
			}
		}
		// If we make it past all the checks, identify the current point as a local extreme.
		gFeatures[idx] = s;
	}
} // End of FindLocalExtrema


__kernel void FindLocalMaxima(
	__global const short *gDog1,
	__global const short *gDog2,
	__global const short *gDog3,
	const int s,
	__global int *gFeatures
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	// We will not search for anything <= 3 elements of the edge of the array. This is because when we generate descriptors, we must have 3 elements of information in each direction.
	if (x > 3 && x < (szx-3) && y > 3 && y < (szy-3)) {
		// Get the value to compare to.
		short value = gDog2[idx];
		// Look at all 26 neighbours.
		for (int i=-1; i <= 1; i++) {
			for (int j=-1; j <= 1; j++) {
				// Create a test index, offset by 1 in each direction.
				int testIdx = (y+j) + szy*(x+i);
				if (testIdx == idx) {
					// If our test index is the same as our array index, we only need to check arrays 1 and 3.
					if (value <= gDog1[testIdx] || value <= gDog3[testIdx]) {
						return;
					}
				}
				else {
					if (value <= gDog1[testIdx] || value <= gDog2[testIdx] || value <= gDog3[testIdx]) {
						return;
					}
				}
			}
		}
		// If we make it past all the checks, identify the current point as a local extreme.
		gFeatures[idx] = s;
	}
} // End of FindLocalMaxima


__kernel void LocateStableFeatures(
	__global float *gFeatures,
	__global int *gImageSize,
	const float contrastLowerLimit,
	__global const short *gDog1,
	__global const short *gDog2,
	__global const short *gDog3,
	__global const short *gDog4,
	__global const short *gDog5
	)
{
	// Get global indice.
	int idx = get_global_id(0);
	// Grab image size.
	int2 size = vload2(0,gImageSize);
	// Pick arrays based on s.
	__global const short *ptr[5] = { gDog1,gDog2,gDog3,gDog4,gDog5 };
	// Data initilization.
	float x = 0.0f;
	float y = 0.0f;
	float s = 0.0f;
	int i0 = 0;
	int i1 = 0;
	int i2 = 0;
	int i3 = 0;
	int i4 = 0;
	int s0 = 0;
	int s1 = 0;
	int s2 = 0;
	float dx = 0.0f;
	float dy = 0.0f;
	float ds = 0.0f;
	float Hxx = 0.0f;
	float Hxy = 0.0f;
	float Hxs = 0.0f;
	float Hyx = 0.0f;
	float Hyy = 0.0f;
	float Hys = 0.0f;
	float Hsx = 0.0f;
	float Hsy = 0.0f;
	float Hss = 0.0f;
	float determinant = 0.0f;
	float Hixx = 0.0f;
	float Hixy = 0.0f;
	float Hixs = 0.0f;
	float Hiyx = 0.0f;
	float Hiyy = 0.0f;
	float Hiys = 0.0f;
	float Hisx = 0.0f;
	float Hisy = 0.0f;
	float Hiss = 0.0f;
	float3 offset = { 0.0f, 0.0f, 0.0f };

	bool success = false;
	for (int i=0; i<4; i++) {
		// Grab the (x,y,sigma) feature point.
		x = gFeatures[3*idx + 0];
		y = gFeatures[3*idx + 1];
		s = gFeatures[3*idx + 2];
		// Calculate second order Taylor series for vector, v(x,y,sigma).
		i0 = convert_int(y + size.y*x);
		i1 = convert_int(y + size.y*(x+1));
		i2 = convert_int(y + size.y*(x-1));
		i3 = convert_int((y+1) + size.y*x);
		i4 = convert_int((y-1) + size.y*x);
		s0 = convert_int(s);
		s1 = convert_int(s+1);
		s2 = convert_int(s-1);
		// Calcualte the derivatives.
		dx = (ptr[s0][i1] - ptr[s0][i2])/2.0f;
		dy = (ptr[s0][i3] - ptr[s0][i4])/2.0f;
		ds = (ptr[s1][i0] - ptr[s2][i0])/2.0f;
		// Calculate the >3D Hessian matrix.
		// https://math.stackexchange.com/questions/302160/correct-way-to-calculate-numeric-derivative-in-discrete-time
		Hxx = ( ptr[s0][i1] - 2*ptr[s0][i0] + ptr[s0][i2] )/4.0f;
		Hxy = dx*dy;
		Hxs = dx*ds;
		Hyx = dy*dx;
		Hyy = ( ptr[s0][i3] - 2*ptr[s0][i0] + ptr[s0][i4] )/4.0f;
		Hys = dy*ds;
		Hsx = ds*dx;
		Hsy = ds*dy;
		Hss = ( ptr[s1][i0] - 2*ptr[s0][i0] + ptr[s2][i0] )/4.0f;
		// Calculate Hessian Inverse.
		determinant = Hxx*Hyy*Hss + Hyx*Hsy*Hxs + Hsx*Hxy*Hys - Hxx*Hsy*Hys - Hsx*Hyy*Hxs - Hyx*Hxy*Hss;
		Hixx = determinant*( Hyy*Hss - Hys*Hsy );
		Hixy = determinant*( Hxs*Hsy - Hxy*Hss );
		Hixs = determinant*( Hxy*Hys - Hxs*Hyy );
		Hiyx = determinant*( Hys*Hsx - Hyx*Hss );
		Hiyy = determinant*( Hxx*Hss - Hxs*Hsx );
		Hiys = determinant*( Hxs*Hyx - Hxx*Hys );
		Hisx = determinant*( Hyx*Hsy - Hyy*Hsx );
		Hisy = determinant*( Hxy*Hsx - Hxx*Hsy );
		Hiss = determinant*( Hxx*Hyy - Hxy*Hyx );
		// Calculate offset (x,y,sigma).
		offset.x = Hixx*x + Hixy*y + Hixs;
		offset.y = Hiyx*x + Hiyy*y + Hiys;
		offset.z = Hisx*x + Hisy*y + Hiss;
		// Check to see if the offset is greater than 0.5 in any direction.
		if (fabs(offset.x) >= 0.5 || fabs(offset.y) >= 0.5 || fabs(offset.z) >= 0.5) {
			// If it is, add a step in those directions to the coordinates (x,y,sigma).
			gFeatures[3*idx + 0] += round(offset.x);
			gFeatures[3*idx + 1] += round(offset.y);
			gFeatures[3*idx + 2] += round(offset.z);
			// It was changed, keep changing it.
			continue;
		}
		else {
			// It doesn't need changing. Stop.
			gFeatures[3*idx + 0] += offset.x;
			gFeatures[3*idx + 1] += offset.y;
			gFeatures[3*idx + 2] += offset.z;
			success = true;
			break;
		}
	}
	// Now that we have finished the loop, if it's last state was changed, consider the point unstable.
	if (!success) {
		// Scrap it. Set everything to zero?
		gFeatures[3*idx + 0] = 0;
		gFeatures[3*idx + 1] = 0;
		gFeatures[3*idx + 2] = 0;
		return;
	}
	else {
		// Grab the (x,y,sigma) feature point.
		x = gFeatures[3*idx + 0];
		y = gFeatures[3*idx + 1];
		s = gFeatures[3*idx + 2];

		// Calculate value at refined position.
		int s0 = convert_int(s);
		float value = ptr[s0][idx] + 0.5f*( dx*offset.x + dy*offset.y + ds+offset.z );
		// Contrast check.
		if (fabs(value) < contrastLowerLimit) {
			gFeatures[3*idx + 0] = 0;
			gFeatures[3*idx + 1] = 0;
			gFeatures[3*idx + 2] = 0;
			return;
		}
		// Trace and determinant of the 2D Hessian.
		float trace = Hxx+Hyy;
		determinant = Hxx*Hyy - Hxy*Hxy;
		// Ratio between eigenvalues.
		float ratio = 10;
		// Curvature/edge check.
		if (pow(trace,2)/determinant > pow(ratio+1,2)/ratio) {
			gFeatures[3*idx + 0] = 0;
			gFeatures[3*idx + 1] = 0;
			gFeatures[3*idx + 2] = 0;
			return;
		}
	}
} // End of SubPixelLocalization


__kernel void GenerateGradientMap(
	__global const short *gScale,
	__global float *gGradientMap
	)
{
	// Get global XY indices.
	int x = get_global_id(0);
	int y = get_global_id(1);
	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	// Get the ID number of the thread.
	int idx = y + szy*x;
	// Create a datapoint.
	float2 gradient = { 0.0f, 0.0f };
	// Skip the border pixels.
	if (x>1 && y>1 && x<szx-1 && y<szx-1) {
		// Calculate gradient.
		float nest = pow((float)(gScale[y + szy*(x+1)] - gScale[y + szy*(x-1)]),2.0f) + pow((float)(gScale[(y+1) + szy*x] - gScale[(y-1) + szy*x]),2.0f);
		gradient.x = sqrt(nest);
		// Calculate angle.
		nest = (gScale[(y+1) + szy*x] - gScale[(y-1) + szy*x])/(gScale[y + szy*(x+1)] - gScale[y + szy*(x-1)]);
		gradient.y = atan(nest);
		// Store them.
		vstore2(gradient,idx,gGradientMap);
	}
	else {
		// Set them to zeroes.
		vstore2(gradient,idx,gGradientMap);
	}
} // End GenerateGradientMap


__kernel void GenerateDescriptors(
	__global float *gDescriptors,
	__global const float *gImageSize,
	__global const short *gScale1,
	__global const short *gScale2,
	__global const short *gScale3,
	__global const short *gScale4,
	__global const short *gScale5,
	__global const short *gScale6,
	__global const short *gGradient1,
	__global const short *gGradient2,
	__global const short *gGradient3,
	__global const short *gGradient4,
	__global const short *gGradient5,
	__global const short *gGradient6
	)
{
	// Get global XY indices.
	int idx = get_global_id(0);
	// Grab image size.
	int2 size = vload2(0,gImageSize);
	// Pick arrays based on s.
	__global const short *ptr[6] = { gScale1,gScale2,gScale3,gScale4,gScale5,gScale6 };
	// Image x,y position (rounded to nearest integer).
	float x = convert_int( round(gDescriptors[3*idx + 0]) );
	float y = convert_int( round(gDescriptors[3*idx + 1]) );
	// Round scale to nearest integer.
	float s = convert_int( round(gDescriptors[3*idx + 2]) );

	// Calculate the gradient and angle for a 16x16 area around the point.
	// OpenCL can only take up to float16
	for (int i=0; i<8; i++) {
		for (int j=0; j<8; j++) {
			// Calculate gradient.
			float nest = pow(ptr[s][y + szy*(x+1)] - ptr[s][y + szy*(x-1)],2) + pow(ptr[s][(y+1) + szy*x] - ptr[s][(y-1) + szy*x] ,2);
			float gradient = sqrt(nest);
			// Calculate angle.
			nest = (ptr[s][(y+1) + szy*x] - ptr[s][(y-1) + szy*x])/(ptr[s][y + szy*(x+1)] - ptr[s][y + szy*(x-1)]);
			float theta = atan(nest);
	}
} // End GenerateDescriptors