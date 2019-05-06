import numpy as np
import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

f = open('/Users/micahbarnes/Documents/scratch/blockData.txt','r')
arr = f.read()
print(arr)
test = np.array(arr[2:-2].split("', '")).astype(float)
print(test)
x = test[0::2]
y = test[1::2]
f.close()
x = np.append(x,x[0])
y = np.append(y,y[0])

ax = plt.plot(x,y)
plt.show()