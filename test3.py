from matplotlib import pyplot as plt
import numpy as np
import imageio
from scipy.signal import convolve2d

fn = '/Users/barnesmicah/Documents/dumpingGround/SIFTtestImages/test1.jpg'
image = imageio.imread(fn,as_gray=True)

# Filter width should be 5 times the standard deviation and rounded up to the next odd integer..
# filterWidth = 50
filterWidth = 9
# Calculate an offset for the filter so that it is centred about zero (i.e. so it goes from -1,0,+1 instead of 0,1,2...).
filterOffset = (filterWidth-1)/2
# Calculate xy values for filter (centred on zero, as described above).
x,y = np.indices((filterWidth,filterWidth))-filterOffset

# Generate gaussian kernel.
sigma = [1.6,1.795939277294997,2.015873679831797,2.2627416997969525,2.5398416831491195,2.8508758980490865]
g = []
for s in sigma:
	# g.append( np.exp( -(x**2 + y**2)/(2*(s)**2) )/( 2*np.pi * (s)**2 ) )
	gauss = np.exp( -(x**2 + y**2)/(2*(s)**2) )/( 2*np.pi * (s)**2 )
	g.append( convolve2d(image,gauss) )

fig,ax = plt.subplots(2,len(sigma),sharex=True,sharey=True)

for i in range(len(g)):
	ax[0,i].imshow(g[i],cmap='Greys')

for j in range(len(g)-1):
	ax[1,j].imshow(g[j+1]-g[j],cmap='Greys')
	# ax[1,j].imshow(imageio.imread('/Users/barnesmicah/Documents/dumpingGround/SIFTcomparison/scale{}.jpg'.format(j+1),as_gray=True),cmap='Greys')

plt.show()