// Implementation of Lowe 2004.
// This is set up for 5 image scale levels and 4 DoG levels.

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
			}
			if (ny >= szy) {
				ny = szy + (szy - ny - 1);
			}
			// Add the result.
			value += gArray[ny + szy*nx] * gGaussianKernel[j + filterWidth*i];
		}
	}
	// Need to keep as float until final writing. Convert to short.
	gScaleImage[idx] = convert_short(value);
} // End Gaussian2D


__kernel void SubSample(
	__global const short *gInputArray,
	__global short *gOutputArray,
	const int stride,
	const int sizey
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
	// int idxSample = (y+stride) + szy*stride*(x+stride);
	int idxSample = (y*stride) + sizey*stride*x;
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
	if (x>0 && y>0 && x<szx-1 && y<szy-1) {
		// Calculate gradient.
		float nest = pow((float)(gScale[y + szy*(x+1)] - gScale[y + szy*(x-1)]),2.0f) + pow((float)(gScale[(y+1) + szy*x] - gScale[(y-1) + szy*x]),2.0f);
		gradient.x = sqrt(nest);
		// Calculate angle.
		// nest = (gScale[(y+1) + szy*x] - gScale[(y-1) + szy*x])/(gScale[y + szy*(x+1)] - gScale[y + szy*(x-1)]);
		gradient.y = atan2(
			(float)(gScale[(y+1) + szy*x] - gScale[(y-1) + szy*x]),
			(float)(gScale[y + szy*(x+1)] - gScale[y + szy*(x-1)])
		);
	}

	vstore2(gradient,idx,gGradientMap);

} // End GenerateGradientMap


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
	// We will not search for anything <= 16 elements of the edge of the array. This is because when we generate descriptors, we must have 16 elements of information in each direction.
	if (x > 16 && x < (szx-16) && y > 16 && y < (szy-16)) {
		// Get the value to compare to.
		short value = gDog2[idx];
		// Look at all 26 neighbours.
		for (int i=-1; i < 2; i++) {
			for (int j=-1; j < 2; j++) {
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
	// We will not search for anything <= 16 elements of the edge of the array. This is because when we generate descriptors, we must have 16 elements of information in each direction.
	if (x > 16 && x < (szx-16) && y > 16 && y < (szy-16)) {
		// Get the value to compare to.
		short value = gDog2[idx];
		// Look at all 26 neighbours.
		for (int i=-1; i < 2; i++) {
			for (int j=-1; j < 2; j++) {
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
	__global float *gKeypoints,
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
	// Setup keypoints stride.
	int stride = 3;
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
	int i5 = 0;
	int i6 = 0;
	int i7 = 0;
	int i8 = 0;
	int s0 = 0;
	int s1 = 0;
	int s2 = 0;
	float dx = 0.0f;
	float dy = 0.0f;
	float ds = 0.0f;
	float Hxx = 0.0f;
	float Hxy = 0.0f;
	float Hxs = 0.0f;
	float Hyy = 0.0f;
	float Hys = 0.0f;
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
		x = rint( gKeypoints[stride*idx + 0] );
		y = rint( gKeypoints[stride*idx + 1] );
		s = rint( gKeypoints[stride*idx + 2] );
		// Calculate second order Taylor series for vector, v(x,y,sigma).
		// First get all the indices for accessing data around our current (x,y) point.
		i0 = convert_int( (y+1) + size.y*(x-1) );
		i1 = convert_int( (y+1) + size.y*(x+0) );
		i2 = convert_int( (y+1) + size.y*(x+1) );
		i3 = convert_int( (y+0) + size.y*(x-1) );
		i4 = convert_int( (y+0) + size.y*(x+0) );
		i5 = convert_int( (y+0) + size.y*(x+1) );
		i6 = convert_int( (y-1) + size.y*(x-1) );
		i7 = convert_int( (y-1) + size.y*(x+0) );
		i8 = convert_int( (y-1) + size.y*(x+1) );
		// Scale indices.
		s0 = convert_int( s-1 );
		s1 = convert_int( s	  );
		s2 = convert_int( s+1 );
		// Calcualte the derivatives.
		dx = (ptr[s1][i5] - ptr[s1][i3])/2.0f;
		dy = (ptr[s1][i1] - ptr[s1][i7])/2.0f;
		ds = (ptr[s2][i4] - ptr[s0][i4])/2.0f;
		// Calculate the 3D Hessian matrix.
		// We use the finite difference method to approximate the Hessian.
		// Each approximation is centred on i (so we use a template [-1 0 1]).
		// We only need to calculate half the Hessian as Hxy == Hyx.
		// https://www.ipol.im/pub/art/2014/82/article_lr.pdf
		// http://web.mit.edu/16.90/BackUp/www/pdfs/Chapter12.pdf
		// https://www.mathematik.uni-dortmund.de/~kuzmin/cfdintro/lecture4.pdf
		Hxx = ( ptr[s1][i5] + ptr[s1][i3] - 2*ptr[s1][i4] );
		Hxy = ( ptr[s1][i2] - ptr[s1][i0] - ptr[s1][i8] + ptr[s1][i6] ) /4.0f;
		Hxs = ( ptr[s2][i5] - ptr[s2][i3] - ptr[s0][i5] + ptr[s0][i3] ) /4.0f;
		Hyy = ( ptr[s1][i1] + ptr[s1][i7] - 2*ptr[s1][i4] );
		Hys = ( ptr[s2][i1] - ptr[s2][i7] - ptr[s0][i1] + ptr[s0][i7] ) /4.0f;
		Hss = ( ptr[s2][i4] + ptr[s0][i4] - 2*ptr[s1][i4] );

		// Now we want to use the second order taylor series to find the local extremum of the points.
		// We take the derivative of the second order taylor series, and equate it to zero to get the stationary point.
		// The Hessian matrix describes the second order derivatives.
		// Now we use the Hessian and the first order derivatives to solve for the true point.

		// Calculate Hessian Inverse.
		determinant = (Hxx*Hyy*Hss) + (Hxy*Hys*Hxs) + (Hxs*Hxy*Hys) - (Hxx*Hys*Hys) - (Hxs*Hyy*Hxs) - (Hxy*Hxy*Hss);
		Hixx = (1/determinant)*( Hyy*Hss - Hys*Hys );
		Hixy = (1/determinant)*( Hxs*Hys - Hxy*Hss );
		Hixs = (1/determinant)*( Hxy*Hys - Hxs*Hyy );
		Hiyx = (1/determinant)*( Hys*Hxs - Hxy*Hss );
		Hiyy = (1/determinant)*( Hxx*Hss - Hxs*Hxs );
		Hiys = (1/determinant)*( Hxs*Hxy - Hxx*Hys );
		Hisx = (1/determinant)*( Hxy*Hys - Hyy*Hxs );
		Hisy = (1/determinant)*( Hxy*Hxs - Hxx*Hys );
		Hiss = (1/determinant)*( Hxx*Hyy - Hxy*Hxy );

		// Calculate offset (x,y,sigma).
		offset.x = -(Hixx*dx + Hixy*dy + Hixs*ds);
		offset.y = -(Hiyx*dx + Hiyy*dy + Hiys*ds);
		offset.z = -(Hisx*dx + Hisy*dy + Hiss*ds);

		// Add the offset.
		gKeypoints[stride*idx + 0] += offset.x;
		gKeypoints[stride*idx + 1] += offset.y;
		gKeypoints[stride*idx + 2] += offset.z;

		// Check to see if the offset is greater than 0.5 in any direction.
		if (fabs(offset.x) > 0.5 || fabs(offset.y) > 0.5 || fabs(offset.z) > 0.5) {
			// Check that our new offset points don't push the point outside our valid range.
			if ((gKeypoints[stride*idx + 0] >= size.x) || (gKeypoints[stride*idx + 1] >= size.y) || (gKeypoints[stride*idx + 2] < 1) || (gKeypoints[stride*idx + 2] > 3)) {
				// If they do, scrap the point.
				break;
			}
			// Otherwise, keep iterating.
			continue;
		}
		else {
			// It doesn't need changing. Stop with success.
			success = true;
			break;
		}
	}
	// Now that we have finished the loop, check whether we succeeded in localising the point.
	if (!success) {
		// Scrap it. Set everything to zero?
		gKeypoints[stride*idx + 0] = 0;
		gKeypoints[stride*idx + 1] = 0;
		gKeypoints[stride*idx + 2] = 0;
		return;
	}
	else {
		// Grab the (x,y,sigma) feature point.
		x = gKeypoints[stride*idx + 0];
		y = gKeypoints[stride*idx + 1];
		s = gKeypoints[stride*idx + 2];

		// Calculate value at refined position.
		int sint = convert_int(rint( s ));
		int iint = convert_int(rint(y) + size.y*rint(x));
		// The interpolated value is the original value plus half of the offset times the gradient.
		float value = ptr[sint][iint] + 0.5f*( dx*offset.x + dy*offset.y + ds+offset.z );

		// Contrast check.
		if (fabs(value) < contrastLowerLimit) {
			gKeypoints[stride*idx + 0] = 0;
			gKeypoints[stride*idx + 1] = 0;
			gKeypoints[stride*idx + 2] = 0;
			return;
		}
		// Trace and determinant of the 2D Hessian.
		float trace = Hxx+Hyy;
		determinant = Hxx*Hyy - Hxy*Hxy;
		// Ratio between eigenvalues.
		float ratio = 10.0f;
		// Curvature/edge check.
		if (pow(trace,2)/determinant >= pow(ratio+1,2)/ratio) {
			gKeypoints[stride*idx + 0] = 0;
			gKeypoints[stride*idx + 1] = 0;
			gKeypoints[stride*idx + 2] = 0;
			return;
		}
	}
} // End of LocateStableFeatures


float interpolateOrientationPeak(
	const float x1,
	const float x2,
	const float x3,
	const float y1,
	const float y2,
	const float y3
	)
{
	// Calculate the parabola constants.
	float denom = (x1-x2) * (x1-x3) * (x2-x3);
	float a 	= (x3 * (y2-y1) + x2 * (y1-y3) + x1 * (y3-y2)) / denom;
	float b 	= (x3*x3 * (y1-y2) + x2*x2 * (y3-y1) + x1*x1 * (y2-y3)) / denom;
	// float c 	= (x2 * x3 * (x2-x3) * y1+x3 * x1 * (x3-x1) * y2+x1 * x2 * (x1-x2) * y3) / denom;
	// Solve for local extrema.
	float nx = -b/(2*a);
	// float ny = a*nx*nx + b*nx * c;
	// float2 newPoint = { nx, ny };
	return nx;
}


__kernel void KeypointOrientations(
	__global float *gKeypoints,
	__global const int *gImageSize,
	__global const int *gGaussianWidths,
	__global const float *gGradient1,
	__global const float *gGradient2,
	__global const float *gGradient3,
	__global const float *gGradient4,
	__global const float *gGradient5,
	__global const float *gGaussian1,
	__global const float *gGaussian2,
	__global const float *gGaussian3,
	__global const float *gGaussian4,
	__global const float *gGaussian5
	)
{
	// Get global XY indices.
	int idx = get_global_id(0);
	// Setup keypoints stride.
	int stride = 8;
	// Grab image size.
	int2 size = vload2(0,gImageSize);
	// Pick arrays based on nearest scale.
	__global const float *gradient[5] = { gGradient1,gGradient2,gGradient3,gGradient4,gGradient5 };
	__global const float *gaussian[5] = { gGaussian1,gGaussian2,gGaussian3,gGaussian4,gGaussian5 };

	// Image x,y position and scale (rounded to nearest integer).
	int x = convert_int(rint( gKeypoints[stride*idx + 0] ));
	int y = convert_int(rint( gKeypoints[stride*idx + 1] ));
	int s = convert_int(rint( gKeypoints[stride*idx + 2] ));

	// Make a temporary histogram. Bins go from [-pi,pi] in 10 degree steps.
	float histogram[36] = { 0.0f };
	// Bin the gaussian weighted magnitudes by the orientation values.
	// Iterate over the area surrounding the point. Assumes an odd width gaussian window.
	for (int i=-(gGaussianWidths[s]-1)/2; i<(gGaussianWidths[s]+1)/2; i++) {
		for (int j=-(gGaussianWidths[s]-1)/2; j<(gGaussianWidths[s]+1)/2; j++) {
			// Calculate index of quadrant point within the scale array.
			int gradIdx = 2*(y+j) + 2*size.y*(x+i);
			// Get gradient index.
			int guassIdx = j + gGaussianWidths[s]*i;
			// Get gradient map details. Had problems with vload2, so not using that.
			float2 grad = { gradient[s][gradIdx], gradient[s][gradIdx+1] };
			// Multiply the magnitude by the gaussian weighting function.
			float value = grad.x*gaussian[s][guassIdx];
			// Calculate which bin it belongs in (via theta).
			int bin = convert_int(floor( 18 + (grad.y/(M_PI_F/18)) ));
			// Add the value to the correct bin.
			histogram[bin] = histogram[bin] + value;

		}
	}

	// Normalise the orientation histogram.
	// Find the maximum.
	float maximum = 0.0f;
	for (int i=0; i<36; i++) {
		if (histogram[i] > maximum) {
			maximum = histogram[i];
		}
	}
	// Normalise the points.
	for (int i=0; i<36; i++) {
		histogram[i] = histogram[i]/maximum;
	}

	// Identify peaks within 80% of norm.
	float orientation = 0.0f;
	int offset = 3;
	float x0 = 0;
	float x1 = 0;
	float x2 = 0;
	float y0 = 0;
	float y1 = 0;
	float y2 = 0;
	// Normalise the points.
	for (int i=0; i<36; i++) {
		if (histogram[i] >= 0.8) {
			if (offset > 4) {
				break;
			}
			// Set the x positions to be the centre of the bins.
			x0 = -M_PI_F + (i-1+0.5)*(M_PI_F/18);
			x1 = -M_PI_F + (i  +0.5)*(M_PI_F/18);
			x2 = -M_PI_F + (i+1+0.5)*(M_PI_F/18);
			// Handle histogram under/overflow conditions.
			if (i==0) {
				y0 = histogram[35];
				y1 = histogram[0];
				y2 = histogram[1];
			}
			else if (i==35) {
				y0 = histogram[34];
				y1 = histogram[35];
				y2 = histogram[0];
			}
			else {
				y0 = histogram[i-1];
				y1 = histogram[i];
				y2 = histogram[i+1];
			}

			// Continue as normal.
			orientation = interpolateOrientationPeak(
					x0,x1,x2,
					y0,y1,y2
				);

			// Add the orientation to the keypoint.
			gKeypoints[idx*stride + offset] = orientation;
			// Increase the offset.
			offset++;
		}
	}
} // End KeypointOrientations


__kernel void KeypointDescriptors(
	__global float *gDescriptors,
	__global const int *gImageSize,
	__global const float *gGaussianKernel,
	__global const float *gGradient1,
	__global const float *gGradient2,
	__global const float *gGradient3,
	__global const float *gGradient4,
	__global const float *gGradient5
	)
{
	// Get global XY indices.
	int idx = get_global_id(0);
	// Setup keypoints stride.
	int stride = 132;
	// Grab image size.
	int2 size = vload2(0,gImageSize);
	// Pick arrays based on nearest scale.
	__global const float *gradient[5] = { gGradient1,gGradient2,gGradient3,gGradient4,gGradient5 };

	// Image x,y position (floats), scale (rounded to nearest integer) and orientation (float).
	float x = gDescriptors[stride*idx + 0];
	float y = gDescriptors[stride*idx + 1];
	float scale = gDescriptors[stride*idx + 2];
	float orientation = gDescriptors[stride*idx + 3];
	// Calculate sin and cos of the orientation. Saves repeated computation later.
	float s = sin(orientation);
	float c = cos(orientation);

	// Create reusable points.
	// New offset points.
	float nx = 0.0f;
	float ny = 0.0f;
	// Rotated points.
	float rx = 0.0f;
	float ry = 0.0f;
	// Gaussian index.
	int gind = 0;
	// Descriptor index.
	int dind = 0;
	// Offset for descriptor.
	int offset = 4;

	// Iterate over the (16,16) area surrounding the point.
	// p,q: Manages the quadrant (sub-area) we are looking at: (-2,-1,0,1).
	for (int p=-2; p<2; p++) {
		for (int q=-2; q<2; q++) {
			// Histogram bins go from [-pi,pi] in 45 degree steps.
			// i,j: Manage the x,y position in that quadrant.
			for (int i=0; i<4; i++) {
				for (int j=0; j<4; j++) {
					// Calculate our grid position.
					nx = p*4 + i + 0.5f;
					ny = q*4 + j + 0.5f;
					// Now rotate our point to be in line with the keypoint orientation. This ensures orientation independence.
					// Rotate our grid (this is centred about our point) to achieve rotation invariance.
					rx = nx*c - ny*s;
					ry = nx*s + ny*c;
					// Calculate our new grid point, rotated and offset.
					nx = x + rx;
					ny = y + ry;

					// Bilinear interpolation of gradient[s] at (rx,ry)...
					// Get the difference between p0 and p (the distance of the point to the next smallest integer). Assume square voxels.
					float3 delta = { nx-floor(nx), ny-floor(ny), scale-floor(scale) };

					// Get the source indices of the voxels surrounding the sample point.
					int i00 = 2*floor(ny)	+ 2*size.y*floor(nx);
					int i10 = 2*floor(ny)	+ 2*size.y*ceil(nx);
					int i01 = 2*ceil(ny)	+ 2*size.y*floor(nx);
					int i11 = 2*ceil(ny)	+ 2*size.y*ceil(nx);
					int scale1 = convert_int(floor(scale));
					int scale2 = convert_int(ceil(scale));
					// Get first round of interpolated points in x (m,theta).
					float m00 = gradient[scale1][i00]*(1-delta.x) + gradient[scale1][i10]*delta.x;
					float m10 = gradient[scale1][i01]*(1-delta.x) + gradient[scale1][i11]*delta.x;
					float m01 = gradient[scale2][i00]*(1-delta.x) + gradient[scale2][i10]*delta.x;
					float m11 = gradient[scale2][i01]*(1-delta.x) + gradient[scale2][i11]*delta.x;
					float t00 = gradient[scale1][i00+1]*(1-delta.x) + gradient[scale1][i10+1]*delta.x;
					float t10 = gradient[scale1][i01+1]*(1-delta.x) + gradient[scale1][i11+1]*delta.x;
					float t01 = gradient[scale2][i00+1]*(1-delta.x) + gradient[scale2][i10+1]*delta.x;
					float t11 = gradient[scale2][i01+1]*(1-delta.x) + gradient[scale2][i11+1]*delta.x;
					// Interpolate in y. 
					float m0 = m00*(1-delta.y) + m10*delta.y;
					float m1 = m01*(1-delta.y) + m11*delta.y;
					float t0 = t00*(1-delta.y) + t10*delta.y;
					float t1 = t01*(1-delta.y) + t11*delta.y;
					// Interpolate over adjacent scales. This is our final interpolated value of (m,theta).
					float magnitude = m0*(1-delta.z) + m1*delta.z;
					float theta = t0*(1-delta.z) + t1*delta.z;

					// Offset theta by keypoint orientation.
					theta = theta-orientation;
					// Make sure theta is between [-pi,pi]. This assumes it can only be within 2*pi of our [-pi,pi] window.
					if (theta < -M_PI_F) {
						theta = theta + 2*M_PI_F;
					}
					else if (theta > M_PI_F) {
						theta = theta - 2*M_PI_F;
					}
					// Calculate which bin it belongs in (via theta).
					int bin = convert_int(floor( 4 + (theta/(M_PI_F/4)) ));
					// Calculate the array indices.
					gind = j+(p+2)*4 + 16*(i+(q+2)*4);
					dind = (idx*stride) + offset + 8*(q+2)+32*(p+2) + bin;
					// Add the gaussian weighted value to the correct bin.
					gDescriptors[dind] = gDescriptors[dind] + magnitude*gGaussianKernel[gind];
				}
			} // i,j
		}
	} // p,q

	// Find the maximum value...
	float maximum = 0.0f;
	for (int i=offset; i<stride; i++) {
		// Update the maximum value (to normalise to later).
		maximum = fmax(maximum,gDescriptors[idx*stride + i]);
	}
	// Create a unit feature vector.
	for (int i=offset; i<stride; i++) {
		// Noramlise the vector to the maximum value.
		gDescriptors[idx*stride + i] = gDescriptors[idx*stride + i]/maximum;
		// If greater than 0.2, set it to 0.2.
		if (gDescriptors[idx*stride + i] > 0.2f) {
			gDescriptors[idx*stride + i] = 0.2f;
		}
		// Now re-normalize it to 1.
		gDescriptors[idx*stride + i] = gDescriptors[idx*stride + i]/0.2f;
	}
} // End KeypointDescriptors