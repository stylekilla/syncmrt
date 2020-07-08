#include <stdio.h>
#include <cmath>

texture<float, 3, cudaReadModeElementType> tex;

__global__ void rotate(
	float *out,
	float r00,
	float r01,
	float r02,
	float r10,
	float r11,
	float r12,
	float r20,
	float r21,
	float r22,
	float texX,
	float texY,
	float texZ,
	int outX,
	int outY,
	int outZ)
{
	// Global thread indexes in each axis.
	int x = blockIdx.x*blockDim.x + threadIdx.x;
	int y = blockIdx.y*blockDim.y + threadIdx.y;
	int z = blockIdx.z*blockDim.z + threadIdx.z;

	if ((x < texX) && (y < texY) && (z < texZ)) {
		// Center array (new origin). Relocated to 000.
		float texOrigin[3] = { 
			(texX-1)/2,
			(texY-1)/2,
			(texZ-1)/2 
		};

		// Adjust for origin.
		float i = x - texOrigin[0];
		float j = y - texOrigin[1];
		float k = z - texOrigin[2];

		// Reconstruct rotation array.
		float R[3][3] = {
			{ r00, r01, r02 },
			{ r10, r11, r12 },
			{ r20, r21, r22}
		};

		// Rotate points.
		float point[3] = {
			i*R[0][0] + j*R[0][1] + k*R[0][2],
			i*R[1][0] + j*R[1][1] + k*R[1][2],
			i*R[2][0] + j*R[2][1] + k*R[2][2]
		};

		// New origin based of output shape size.
		float outOrigin[3] = {
			((float)outX-1)/2,
			((float)outY-1)/2,
			((float)outZ-1)/2
		};

		// Relocate point in output shape.
		int newPoint[3] = {
			(int)roundf(point[0] + outOrigin[0]),
			(int)roundf(point[1] + outOrigin[1]),
			(int)roundf(point[2] + outOrigin[2])
		};

		int idx = newPoint[2] + 
		(outZ * newPoint[1]) +
		(outZ * outY * newPoint[0]);

		// printf("Cuda thread (%i %i %i); Center origin (%f %f %f); New location (%f %f %f); Un-centered origin (%i %i %i) \n",x,y,z,i,j,k,point[0],point[1],point[2],newPoint[0],newPoint[1],newPoint[2]);

		if (idx < (outX*outY*outZ)) {
			out[idx] = tex3D(tex, z, y, x);
		}
		else {
		}

	}

}