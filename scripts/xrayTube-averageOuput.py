import numpy as np
import re, os, fnmatch 
import platform
import tifffile as tif
# import argparse
import datetime


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

fol = '/mnt/imbl-imaging-data/mrt/xray/cache'+slash

# Read the names of the files in the sequence into a list
for filenames in os.walk(fol):
	pass #print(files)

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

#remove some of the dark pixels
image[:,519] = image[:,518]
image[:,606] = image[:,606]*1.04
image[:,607] = image[:,606]
image[:,610] = image[:,610]*1.03
image[:,609] = image[:,610]
image[:,608] = 0.5*(image[:,609]+image[:,607])
image[178,:] = image[177,:]
image[179,:] = image[180,:]
image[39,:] = image[38,:]

'''THIS SECTION IS TO FIX THE IMAGE CONTRAST PRE-ALIGNMENT PROGRAM.'''
# windowMin = 0 
# windowMax = 800

# image[image>windowMax] = windowMax

outputPretext = "{:%y%m%d-%Hh%Mm%Ss}".format(datetime.datetime.now())
outputFolder = '/mnt/imbl-imaging-data/mrt/xray'+slash
np.save(outputFolder+outputPretext,image.astype('float32'))
tif.imsave(outputFolder+outputPretext+'.tif',image.astype('float32'))

# os.remove(fol)

from matplotlib import pyplot as plt
plt.imshow(image,cmap='bone_r')
plt.show()