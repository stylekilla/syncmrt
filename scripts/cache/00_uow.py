import numpy as np
import re, os, fnmatch 
import platform
import datetime
from skimage.external import tifffile as tif
import h5py as hdf
import glob

numbers = re.compile(r'(\d+)')

def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

# parser = argparse.ArgumentParser()
# parser.add_argument("--filename", type=str)
# args = parser.parse_args()


#find the right type of slash to use
if platform.system() == "Windows":
   slash = '\\'
else:
   slash = '/'

# fol = '/mnt/datahdd/mrt/xray/cache'+slash
fol = '/home/imbl/Documents/Data/XR/cache'+slash

# Read the names of the files in the sequence into a list
for filenames in os.walk(fol):
	pass 
  # print(files)

#Sort the files. Assumes all files in the folder are to be sorted
fn = sorted(fnmatch.filter(filenames[2], '*'), key=numericalSort)

try:
	im = tif.imread(fol+slash+fn[0])
except:
	print('Make sure there are files in the cache folder.')
	exit()

stack = np.zeros((im.shape[0], im.shape[1], len(fn)))
intens = np.zeros(len(fn))

for i in range(len(fn)):
  stack[:,:,i] = tif.imread(fol+slash+fn[i])
  intens[i] = np.sum(stack[:200,:200,i])

binary_intens = intens > (intens[1] * 1.5)
        
x_peaks = np.where(np.diff(binary_intens))[0]
x1, x2 = x_peaks[0], x_peaks[-1]

# image = np.sum(stack[:,:,x1:x2+1], axis=2)
image = np.mean(stack[:,:,x1:x2+1], axis=2)

image = np.fliplr(np.flipud(image))

#remove some of the dark pixels
# image[:,519] = image[:,518]
# image[:,606] = image[:,606]*1.04
# image[:,607] = image[:,606]
# image[:,610] = image[:,610]*1.03
# image[:,609] = image[:,610]
# image[:,608] = 0.5*(image[:,609]+image[:,607])
# image[178,:] = image[177,:]
# image[179,:] = image[180,:]
# image[39,:] = image[38,:]

'''THIS SECTION IS TO FIX THE IMAGE CONTRAST PRE-ALIGNMENT PROGRAM.'''
# windowMin = 0 
# windowMax = 800

# image[image>windowMax] = windowMax


outputPretext = "{:%y%m%d-%Hh%Mm%Ss}".format(datetime.datetime.now())
# outputFolder = '/mnt/datahdd/mrt/xray'+slash
outputFolder = '/home/imbl/Documents/Data/XR/set'+slash
outputFolder_tif = '/home/imbl/Documents/Data/XR/UOW'+slash
np.save(outputFolder+outputPretext+'_0',image.astype('float32'))
np.save(outputFolder+outputPretext+'_1',image.astype('float32'))
tif.imsave(outputFolder_tif+outputPretext+'.tif',image.astype('float32'))

# # Remove files in folder.
# # os.remove(fol)
# import shutil
# # folder = '/path/to/folder'
# for the_file in os.listdir(fol):
#     file_path = os.path.join(fol, the_file)
#     try:
#         if os.path.isfile(file_path):
#             os.unlink(file_path)
#         #elif os.path.isdir(file_path): shutil.rmtree(file_path)
#     except Exception as e:
#         print(e)

# import matplotlib
# matplotlib.use('Agg')
# from matplotlib import pyplot as plt
# plt.imshow(image,cmap='bone_r')
# plt.show()



name = 'Rats'
detector = 'Hamamatsu'
pixsize = 0.0809

# Locate the files.
# path = '/mnt/datahdd/mrt/xray/set/'
path = '/home/imbl/Documents/Data/XR/set/'
savePath = '/home/imbl/Documents/Data/XR/hdf5/'
# fn = glob.glob(path+'*.tif')
fn = glob.glob(path+'*.npy')
# Read in TIFF's.
# ary0 = tif.imread(fn[0])
# ary1 = tif.imread(fn[1])
ary0 = np.load(fn[0])
ary1 = np.load(fn[1])

# Isoc as (image shape) - (coordinate from top left corner in Y X (as per imageJ)). This gives isoc in reference to bottom left position.
imagej_x = 536+7.41
imagej_y = 666.5
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