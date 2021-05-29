import numpy as np
import matplotlib.pyplot as plt
import h5py as hdf

imagedir = '/mnt/tmp/'
filename = 'CanineImaging4.hdf'

f = hdf.File(imagedir+filename)
zPos = np.array(f['entry']['instrument']['NDAttributes']['Z'])
arr = np.array(f['entry']['data']['data'])
f.close()

print(zPos)

# Filter the z positions so they are averaged over 3 places.
zPos_filtered = np.convolve(zPos, np.ones(3)/3,'valid')
zPos_diff = np.absolute(np.diff(zPos_filtered))
zPos_diff = np.r_[zPos_diff[0],zPos_diff,zPos_diff[-1]]

# Find the positions that exceed the mean +/- 3 std deviations.
mean = np.mean(zPos_diff[np.where(zPos_diff!=0)])
std = np.std(zPos_diff[np.where(zPos_diff!=0)])

invalidPositions = [
	np.where(zPos_diff < mean - 2*std),
	np.where(zPos_diff > mean + 2*std)
]
invalidPositions = np.hstack(invalidPositions).ravel()

if len(invalidPositions) == 0: 
	startIdx = 0
	finishIdx = len(zPos_diff)
else:
	theSplit = np.split(invalidPositions, np.where(np.diff(invalidPositions) != 1)[0]+1)
	if len(theSplit) == 1:
		# We only have one invalid region at the start or the end?
		if 0 in theSplit[0]:
			startIdx = theSplit[0][-1]
			finishIdx = len(zPos_diff)
		elif len(zPos_diff)-1 in theSplit[0]:
			startIdx = 0
			finishIdx = theSplit[0][0]
	else:
		# We have two regions.
		if 0 in theSplit[0]:
			startIdx = theSplit[0][-1]
		else:
			startIdx = 0
		if len(zPos_diff)-1 in theSplit[-1]:
			finishIdx = theSplit[-1][0]
		else:
			finishIdx = len(zPos_diff)

arr = np.flipud(np.vstack(arr[startIdx:finishIdx,:,:]))
print(arr.shape)
zRange = [zPos[startIdx], zPos[finishIdx]]

# fig,ax = plt.subplots(2)
# extent = [0,arr.shape[1]*0.044,zRange[1],zRange[0]]
# ax[0].plot(np.arange(len(zPos)),zPos,c='k')
# ax[0].plot(np.arange(startIdx,finishIdx),zPos[startIdx:finishIdx],c='r')
# ax[0].plot(np.arange(len(zPos_diff)),zPos_diff,c='k',ls=':')
# ax[1].imshow(arr,extent=extent)
# plt.show()

fig,ax = plt.subplots(1)
extent = [0,arr.shape[1]*0.044,zRange[1],zRange[0]]
ax.imshow(arr,extent=extent,cmap='Greys')
plt.savefig(f'/home/imbl/Downloads/test.jpg')