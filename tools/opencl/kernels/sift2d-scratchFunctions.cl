__kernel void RefineLocalPositions(
	__global const short *gArray1,
	__global const short *gArray2,
	__global const short *gArray3,
	__global short *gExtrema,
	__global short contrastLowerLimit
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
	// If the value is 1, it is a point of interest.
	if (gExtrema[idx] == 1) {
		// Calculate second order Taylor series for vector, v(x,y,sigma).
		// Calcualte the derivatives.
		float dx = (gArray2[y + szy*(x+1)] - gArray2[y + szy*(x-1)])/2.0f;
		float dy = (gArray2[(y+1) + szy*x] - gArray2[(y-1) + szy*x])/2.0f;
		float ds = (gArray3[y + szy*x] - gArray1[y + szy*x])/2.0f;
		// Calculate the >3D Hessian matrix.
		// https://math.stackexchange.com/questions/302160/correct-way-to-calculate-numeric-derivative-in-discrete-time
		float Hxx = ( gArray2[y + szy*(x+1)] - 2*gArray2[y + szy*x] + gArray2[y + szy*(x-1)] )/4.0f;
		float Hxy = dx*dy;
		float Hxs = dx*ds;
		float Hyx = dy*dx;
		float Hyy = ( gArray2[(y+1) + szy*x] - 2*gArray2[y + szy*x] + gArray2[(y-1) + szy*x] )/4.0f;
		float Hys = dy*ds;
		float Hsx = ds*dx;
		float Hsy = ds*dy;
		float Hss = ( gArray3[y + szy*x] - 2*gArray2[y + szy*x] + gArray1[y + szy*x] )/4.0f;
		// Calculate Hessian Inverse.
		float determinant = Hxx*Hyy*Hss + Hyx*Hsy*Hxs + Hsx*Hxy*Hys - Hxx*Hsy*Hys - Hsx*Hyy*Hxs - Hyx*Hxy*Hss;
		float Hixx = determinant*( Hyy*Hss - Hys*Hsy );
		float Hixy = determinant*( Hxs*Hsy - Hxy*Hss );
		float Hixs = determinant*( Hxy*Hys - Hxs*Hyy );
		float Hiyx = determinant*( Hys*Hsx - Hyx*Hss );
		float Hiyy = determinant*( Hxx*Hss - Hxs*Hsx );
		float Hiys = determinant*( Hxs*Hyx - Hxx*Hys );
		float Hisx = determinant*( Hyx*Hsy - Hyy*Hsx );
		float Hisy = determinant*( Hxy*Hsx - Hxx*Hsy );
		float Hiss = determinant*( Hxx*Hyy - Hxy*Hyx );
		// Calculate offset (x,y,sigma).
		float3 offset = {
			Hixx*x + Hixy*y + Hixs*1,
			Hiyx*x + Hiyy*y + Hiys*1,
			Hisx*x + Hisy*y + Hiss*1
		};
		// Calculate new position (x,y,sigma).
		float3 newPos = {
			x + offset.x,
			y + offset.y,
			s + offset.z
		};
		// Calculate value at position.
		float value = fabs( gArray2[idx] + 0.5f*( dx*offset.x + dy*offset.y + ds+offset.z ) );
		// Contrast check.
		if (value < contrastLowerLimit) {
			gExtrema[idx] = 0;
		}
		// Trace and determinant of the 2D Hessian.
		float trace = Hxx+Hyy;
		determinant = Hxx*Hyy - Dxy*Dxy;
		// Ratio between eigenvalues.
		float ratio = 10;
		// Curvature/edge check.
		if (trace*trace/determinant > pow(ratio+1,2)/ratio) {
			gExtrema[idx] = 0;
		}
		// Shift extrema position to new location if required.
		if (fabs(offset.x) > 0.5 | fabs(offset.y) > 0.5 | fabs(offset.z) > 0.5) {
			gExtrema[idx] = 0;
		}

	} 
} // End of SubPixelLocalization

// __kernel void GenerateDescriptors(
// 	__global const short *keyPoints,
// 	__global short *descriptors,
// 	__global const short *gArray1,
// 	)
// {
// 	// Get global XY indices.
// 	int x = get_global_id(0);

// 	// Calculate gradient.
// 	float nest = pow(gArray[y + szy*(x+1)] - gArray[y + szy*(x-1)],2) + pow(gArray[(y+1) + szy*x] - gArray[(y-1) + szy*x] ,2);
// 	float m = sqrt(nest);
// 	// Calculate angle.
// 	nest = (gArray[(y+1) + szy*x] - gArray[(y-1) + szy*x])/(gArray[y + szy*(x+1)] - gArray[y + szy*(x-1)])
// 	float theta = atan2(nest)

// } // End GenerateDescriptors