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
gradientPositions = []

# So if I take my contour, and resample it without loss:
granularity = 20

iterate = list(range(0,len(contour),granularity))
for i in range(len(iterate)-1):
	a = iterate[i]
	b = iterate[i+1]
	gradientConditions.append(contour[b,:] - contour[a,:])
	gradientPositions.append(contour[int((a+b)/2),:])

print((gradientConditions))
print((gradientPositions))


success = slitOptimister(speed,positions,gradientConditions)
# success = True if it all passed.
# success = {'speed': True, 'acceleration': False}
# If acceleration is too much then we need to know in which direction.
# To reduce the acceleration we need to blur it out a little bit, so give a little bit on the positions.
