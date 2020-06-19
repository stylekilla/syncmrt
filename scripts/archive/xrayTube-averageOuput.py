import numpy as np
import re, os, fnmatch 
import platform
# import tifffile as tif
# import argparse
import datetime
from skimage.external import tifffile as tif


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