import numpy as np
import matplotlib.pyplot as plt
import h5py as hdf

imagedir = '/mnt/tmp/'
filename = 'UUID.hdf'

f = hdf.File(imagedir+filename)
arr = np.vstack(f['entry']['data']['data'])
# arr = np.average(f['entry']['data']['data'],axis=1)
f.close()

fig,ax = plt.subplots(1)
# extent = [0,arr.shape[1],arr.shape[0]*5,0]
# ax.imshow(arr,extent=extent)
ax.imshow(arr)
plt.show()