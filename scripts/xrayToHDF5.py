import h5py as hdf
import numpy as np
import tifffile as tif
import glob

name = 'Block1'
detector = 'Hamamatsu'
pixsize = 5/(320.417-289.062)

# Locate the files.
path = '/mnt/datahdd/mrt/xray/set/'
savePath = '/home/imbl/Documents/Micah/Data/xray/'
fn = glob.glob(path+'*.tif')
# Read in TIFF's.
ary0 = tif.imread(fn[0])
ary1 = tif.imread(fn[1])

# Isoc as (image shape) - (coordinate from top left corner in Y X (as per imageJ)). This gives isoc in reference to bottom left position.
imagej_x = 320.417
imagej_y = 234.625
isoc = np.absolute( np.array([0,ary0.shape[0]]) - np.array([-imagej_x,imagej_y]) )

# Open HDF5 file.
import datetime as dt
now = dt.datetime.now()
fileName = str(savePath)+'xray_dataset'+str(now.hour)+'h-'+str(now.minute)+'m.hdf5'
f = hdf.File(fileName,'w')
f.attrs['NumberOfImages'] = 2
f.attrs['Detector'] = detector
f.attrs['PixelSize'] = pixsize
f.attrs['PatientName'] = name

# Create the image datasets in the HDF5 container.
im0 = f.create_dataset('0',data=ary0)
im1 = f.create_dataset('1',data=ary1)

# Calculate extent vars.
x1 = isoc[0]*pixsize
x2 = x1-ary0.shape[1]*pixsize
y1 = -isoc[1]*pixsize
y2 = y1+ary0.shape[0]*pixsize
z1 = -isoc[0]*pixsize
z2 = z1+ary0.shape[1]*pixsize
extent = np.array([x1,x2,y1,y2,z1,z2])

# Assign vars to images.
im0.attrs['extent'] = extent[:4]
im0.attrs['isocenter'] = np.array([0,0,0])
im1.attrs['extent'] = np.concatenate((extent[4:6],extent[2:4]))
im1.attrs['isocenter'] = np.array([0,0,0])

# Close and save file.
f.close()