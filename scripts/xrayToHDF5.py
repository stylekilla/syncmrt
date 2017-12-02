import h5py as hdf
import numpy as np
import tifffile as tif
import glob

name = 'Block1'
detector = 'Hamamatsu'
pixsize = 0.155

# Locate the files.
path = '/mnt/datahdd/mrt/xray/set/'
fn = glob.glob(path+'*.tif')
# Read in TIFF's.
ary0 = tif.imread(fn[0])
ary1 = tif.imread(fn[1])

# Isoc as (image shape) - (coordinate from top left corner). This gives isoc in reference to bottom left position.
isoc = np.absolute( np.array([ary0.shape[0],0]) - np.array([234.729,325.167]) )
isoc = np.around(isoc).astype(int)

# Open HDF5 file.
f = hdf.File('xray_dataset.hdf5','w')
f.attrs['NumberOfImages'] = 2
f.attrs['Detector'] = detector
f.attrs['PixelSize'] = pixsize
f.attrs['PatientName'] = name

# Create the image datasets in the HDF5 container.
im0 = f.create_dataset('0',data=ary0)
im1 = f.create_dataset('1',data=ary1)

# Calculate extent vars.
b = (0-isoc[0])*pixsize
l = (0-isoc[1])*pixsize
t = (ary0.shape[0]-isoc[0])*pixsize
r = (ary0.shape[1]-isoc[1])*pixsize
extent = np.array([l,r,b,t])

# Assign vars to images.
im0.attrs['extent'] = extent
im0.attrs['isocenter'] = np.array([0,0,0])
im1.attrs['extent'] = extent
im1.attrs['isocenter'] = np.array([0,0,0])

# Close and save file.
f.close()