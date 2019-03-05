import h5py as hdf
import numpy as np
from skimage.external import tifffile as tif
import glob

name = 'Rats'
detector = 'Hamamatsu'
pixsize = 0.1589

# Locate the files.
# path = '/mnt/datahdd/mrt/xray/set/'
path = '/home/imbl/Documents/Data/XR/set/'
savePath = '/home/imbl/Documents/Data/XR/hdf5/'
# fn = glob.glob(path+'*.npy')
fn = glob.glob(path+'*.tif')
# Read in TIFF's.
ary0 = tif.imread(fn[0])
ary1 = tif.imread(fn[1])
# ary0 = np.load(fn[0])
# ary1 = np.load(fn[1])

# Isoc as (image shape) - (coordinate from top left corner in Y X (as per imageJ)). This gives isoc in reference to bottom left position.
imagej_x = 551.875
imagej_y = 230.375+3.583
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

# # Remove files in folder.
# # os.remove(fol)
# import shutil
# # folder = '/path/to/folder'
# for the_file in os.listdir(path):
#     file_path = os.path.join(path, the_file)
#     try:
#         if os.path.isfile(file_path):
#             os.unlink(file_path)
#         #elif os.path.isdir(file_path): shutil.rmtree(file_path)
#     except Exception as e:
#         print(e)