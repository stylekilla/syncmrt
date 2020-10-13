import numpy as np
import itertools

# Four points.
p1 = np.identity(4)
p2 = np.identity(4)
p3 = np.identity(4)
p4 = np.identity(4)

# Grab rotations and translations for each point.
R = []
T = []
for point in [p1,p2,p3,p4]:
	R.append(point[:3,:3])
	T.append(point[:3,3])

# Solve RX = -T for X (where X = TCP).
TCP = []
for i,j in itertools.combinations(range(4),2):
	TCP.append( (R[i]-R[j])@(T[j]+T[i]) )

# Find true TCP by solving least squares.
# w,v = np.linalg.eig(TCP)
w = np.linalg.eigvals(TCP)

print(TCP)
print(w)
# print(v)

# http://www.jpe-innovations.com/downloads/Fit-sphere-through-points.pdf