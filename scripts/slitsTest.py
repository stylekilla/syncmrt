import numpy as np


# Create a contour.
n = 180
r = 5
contour = np.array([(np.cos(2*np.pi/n*x)*r,np.sin(2*np.pi/n*x)*r) for x in range(0,n+1)])

# Plot the contour for sanity's sake.
# from matplotlib import pyplot as plt
# fig = plt.figure()
# ax = fig.add_axes((0,0,1,1))
# ax.scatter(contour[:,0],contour[:,1])
# plt.show()

# I need to give a list of points in X/Y and the tangent condition required by each point.
gradientConditions = []

# So if I take my contour, and resample it without loss:
granularity = 1
for i,j in (range(0,len(contour)-granularity,granularity),range(granularity,len(contour),granularity)):
	gradientConditions.append(contour[:,j] - contour[:,i])

print(gradientConditions)

# np.atan(theta)