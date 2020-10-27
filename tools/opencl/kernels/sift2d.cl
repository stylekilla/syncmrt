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
		// Grab the (x,y,sigma) feature point; sigma must be reduced by one to let indexing begin at zero (it is saved as n+1).
		x = gFeatures[3*idx + 0];
		y = gFeatures[3*idx + 1];
		s = gFeatures[3*idx + 2] - 1;
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
		s0 = convert_int(rint( s-1	));
		s1 = convert_int(rint( s	));
		s2 = convert_int(rint( s+1	));
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
		Hxx = ( ptr[s1][i5] + ptr[s1][i3] - 2*ptr[s1][i4] )/4.0f;
		Hxy = ( ptr[s1][i2] - ptr[s1][i0] - ptr[s1][i8] + ptr[s1][i6] ) /4.0f;
		Hxs = ( ptr[s2][i5] - ptr[s2][i3] - ptr[s0][i5] + ptr[s0][i3] ) /4.0f;
		Hyy = ( ptr[s1][i1] + ptr[s1][i7] - 2*ptr[s1][i4] )/4.0f;
		Hys = ( ptr[s2][i1] - ptr[s2][i7] - ptr[s0][i1] + ptr[s0][i7] ) /4.0f;
		Hss = ( ptr[s2][i4] + ptr[s0][i4] - 2*ptr[s1][i4] )/4.0f;

		// Now we want to use the second order taylor series to find the local extremum of the points.
		// We take the derivative of the second order taylor series, and equate it to zero to get the stationary point.
		// The Hessian matrix describes the second order derivatives.
		// Now we use the Hessian and the first order derivatives to solve for the true point.

		// Calculate Hessian Inverse.
		determinant = Hxx*Hyy*Hss + Hxy*Hys*Hxs + Hxs*Hxy*Hys - Hxx*Hys*Hys - Hxs*Hyy*Hxs - Hxy*Hxy*Hss;
		Hixx = determinant*( Hyy*Hss - Hys*Hys );
		Hixy = determinant*( Hxs*Hys - Hxy*Hss );
		Hixs = determinant*( Hxy*Hys - Hxs*Hyy );
		Hiyx = determinant*( Hys*Hxs - Hxy*Hss );
		Hiyy = determinant*( Hxx*Hss - Hxs*Hxs );
		Hiys = determinant*( Hxs*Hxy - Hxx*Hys );
		Hisx = determinant*( Hxy*Hys - Hyy*Hxs );
		Hisy = determinant*( Hxy*Hxs - Hxx*Hys );
		Hiss = determinant*( Hxx*Hyy - Hxy*Hxy );

		// Calculate offset (x,y,sigma).
		offset.x = -(Hixx*dx + Hixy*dy + Hixs*ds);
		offset.y = -(Hiyx*dx + Hiyy*dy + Hiys*ds);
		offset.z = -(Hisx*dx + Hisy*dy + Hiss*ds);

		if (idx==129) {
			printf("(x,y,s): (%f, %f, %f) on iteration %i\n",x,y,s,i);
			printf("Derivatives: %f, %f, %f\n",dx,dy,ds);
			printf("8 Points in original scale: \n %d, %d, %d | %d, %d, %d | %d, %d, %d \n %d, %d, %d | %d, %d, %d | %d, %d, %d \n %d, %d, %d | %d, %d, %d | %d, %d, %d \n",
				ptr[s0][i0],ptr[s0][i1],ptr[s0][i2],  ptr[s1][i0],ptr[s1][i1],ptr[s1][i2],  ptr[s2][i0],ptr[s2][i1],ptr[s2][i2],
				ptr[s0][i3],ptr[s0][i4],ptr[s0][i5],  ptr[s1][i3],ptr[s1][i4],ptr[s1][i5],  ptr[s2][i3],ptr[s2][i4],ptr[s2][i5],
				ptr[s0][i6],ptr[s0][i7],ptr[s0][i8],  ptr[s1][i6],ptr[s1][i7],ptr[s1][i8],  ptr[s2][i6],ptr[s2][i7],ptr[s2][i8]
			);
			printf("Hessian Matrix: \n %f, %f, %f\n %f, %f, %f\n %f, %f, %f\n",
				Hxx,Hxy,Hxs,
				Hxy,Hyy,Hys,
				Hxs,Hys,Hss
			);
			printf("Determinant: %f\n",determinant);
			printf("Hessian Matrix Inverse: \n %f, %f, %f\n %f, %f, %f\n %f, %f, %f\n",
				Hixx,Hixy,Hixs,
				Hiyx,Hiyy,Hiys,
				Hisx,Hisy,Hiss
			);
			printf("Offset: %f, %f, %f\n",offset.x,offset.y,offset.z);
		}

		// Check to see if the offset is greater than 0.5 in any direction.
		if (fabs(offset.x) > 0.5 || fabs(offset.y) > 0.5 || fabs(offset.z) > 0.5) {
			// If it is, add a step in those directions to the coordinates (x,y,sigma).
			gFeatures[3*idx + 0] += round(offset.x);
			gFeatures[3*idx + 1] += round(offset.y);
			gFeatures[3*idx + 2] += round(offset.z);
			// Check that our updates don't push the point outside our valid range.
			if ((gFeatures[3*idx + 0] >= size.x) || (gFeatures[3*idx + 1] >= size.y) || (gFeatures[3*idx + 2] < 1) || (gFeatures[3*idx + 2] > 5)) {
				// If they do, scrap the point.
				break;
			}
			// The point was changed, keep changing it.
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
		s = gFeatures[3*idx + 2] - 1;

		// Calculate value at refined position.
		int sint = convert_int(rint( s ));
		int iint = convert_int(rint(y) + size.y*rint(x));
		// The interpolated value is the original value plus half of the offset times the gradient.
		float value = ptr[sint][iint] + 0.5f*( dx*offset.x + dy*offset.y + ds+offset.z );

		if (idx==129) {
			printf("Refined point: (x,y,s) (%f, %f, %f)\n",x,y,s);
			printf("Original value: %d \n",ptr[sint][iint]);
			printf("Refined value: %f \n",value);
			// printf("Derivatives: %f, %f, %f\n",dx,dy,ds);
			// printf("8 Points: \n %d, %d, %d \n %d, %d, %d \n %d, %d, %d \n",
			// 	ptr[s1][i0],ptr[s1][i1],ptr[s1][i2],
			// 	ptr[s1][i3],ptr[s1][i4],ptr[s1][i5],
			// 	ptr[s1][i6],ptr[s1][i7],ptr[s1][i8]
			// );
			// printf("Hessian Matrix: \n %f, %f, %f\n %f, %f, %f\n %f, %f, %f\n",
			// 	Hxx,Hxy,Hxs,
			// 	Hxy,Hyy,Hys,
			// 	Hxs,Hys,Hss
			// );
			// printf("Determinant: %f\n",determinant);
			// printf("Hessian Matrix Inverse: \n %f, %f, %f\n %f, %f, %f\n %f, %f, %f\n",
			// 	Hixx,Hixy,Hixs,
			// 	Hiyx,Hiyy,Hiys,
			// 	Hisx,Hisy,Hiss
			// );
			// printf("Offset: %f, %f, %f\n",offset.x,offset.y,offset.z);
		}

		// Contrast check.
		if (fabs(value) < contrastLowerLimit) {
			gFeatures[3*idx + 0] = 0;
			gFeatures[3*idx + 1] = 0;
			gFeatures[3*idx + 2] = 0;
			// printf("Dropping point (%f,%f:%f) because contrast %f < %f.\n",
			// 	x,y,s,
			// 	value,
			// 	contrastLowerLimit
			// );
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
			// printf("Dropping point (%f,%f:%f) because curvature %f > 12.1 with trace = %f and det = %f \n",
			// 	x,y,s,
			// 	pow(trace,2)/determinant,
			// 	trace,
			// 	determinant
			// 	);
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
	__global const int *gImageSize,
	__global const float *gGradient1,
	__global const float *gGradient2,
	__global const float *gGradient3,
	__global const float *gGradient4,
	__global const float *gGradient5,
	__global const float *gGradient6
	)
{
	// Get global XY indices.
	int idx = get_global_id(0);
	// Grab image size.
	int2 size = vload2(0,gImageSize);
	// Pick arrays based on nearest scale.
	__global const float *gradient[6] = { gGradient1,gGradient2,gGradient3,gGradient4,gGradient5,gGradient6 };
	// Image x,y position (rounded to nearest integer).
	int x = convert_int( round(gDescriptors[3*idx + 0]) );
	int y = convert_int( round(gDescriptors[3*idx + 1]) );
	// Round scale to nearest integer.
	int s = convert_int( round(gDescriptors[3*idx + 2]) );

	// Create a Gaussian Weighting function of size (16,16).
	float gaussianKernel[256] = { 0 };
	for (int i=0; i<16; i++) {
		for (int j=0; j<16; j++) {
			// Calcaulte the offset point of the Gaussian Window.
			float2 index = (float2)(i-7.5,j-7.5);
			// Save the value of the kernel.
			gaussianKernel[j + 16*i] = exp( -(pow(index.x,2) + pow(index.y,2))/(2*pow(1.5*s,2)) )/( 2*M_PI_F * pow(1.5*s,2) );
		}
	}

	// Iterate over the (16,16) area surrounding the point.
	// p,q: Manages the quadrant (sub-area) we are looking at.
	for (int p=0; p<4; p++) {
		for (int q=0; q<4; q++) {
			// i,j: Manage the x,y position in that quadrant.
			for (int i=0; i<4; i++) {
				for (int j=0; j<4; j++) {
					// Calculate index of quadrant point within the scale array. WRONG I THINK...
					int gradIdx = y + size.y*x;
					// Get gradient index.
					int guassIdx = (4*q+j) + 16*(4*p+i);
					// Get gradient map details.
					float2 grad = { gradient[s][gradIdx], gradient[s][gradIdx+1] };
					// Multiply the magnitude by the gaussian weighting function.
					float value = grad.x*gaussianKernel[guassIdx];
					// Calculate which bin it belongs in (via theta).
					int bin = convert_int( floor(grad.y/(M_PI_F/2)) );
					// Calculate distance of point from bin centre.
					// float d = 
					// Add value to correct bin.
					// idx*130		Descriptor: idx (all 130 elements each).
					// +2			First two elements are (x,y) position.
					// q+8*p 		This is the quadrant we are in (row,col).
					// bin 			This is the bin we are assigning the value to.
					// gDescriptors[idx*130 + 2 + q+8*p + bin] = gDescriptors[idx*130 + 2 + q+8*p + bin] + value*(1 − d);
					gDescriptors[idx*130 + 2 + q+8*p + bin] = gDescriptors[idx*130 + 2 + q+8*p + bin] + value;
				}
			} // i,j
		}
	} // p,q
} // End GenerateDescriptors