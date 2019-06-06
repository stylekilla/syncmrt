import h5py as h
import numpy as np

f = h.File('../scratch/testXray.hdf5')

f.create_group('Patient')
f.create_group('Image')

for i in range(3):
	_setName = str(len(f['Image'])+1).zfill(2)
	_nims = np.random.randint(1,3)
	# Create the group set.
	newSet = f['Image'].create_group(_setName)
	# Add the images to the set one by one.
	for i in range(_nims):
		image = newSet.create_dataset(str(i+1),data=np.random.rand(1216,616))
		metadata = {
			'Extent': (-50,50,-25,25),
			'Image Isocenter': (608,308),
			'Image Angle': np.random.randint(-90,91),
			'M': np.identity(3),
			'Mi': np.identity(3),
		}
		# Add the image attributes (metadata).
		for key, val in metadata.items():
			image.attrs[key] = val

f.close()