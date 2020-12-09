import matplotlib as mpl
# mpl.use('Qt5Agg')
mpl.use('MacOSX')
mpl.rcParams['toolbar'] = 'toolmanager'
mpl.rcParams['datapath'] = './QsWidgets/QsMpl/mpl-data'

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, FigureManagerQT
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial
import logging

__all__ = ['QPlot']


class QPlot(QtWidgets.QWidget):
	def __init__(self):
		"""
		QPlot is designed to interface with syncmrt.file.image.Image2D objects.

		Parameters
		----------
		tableModel : QsWorkspace.QPlotTableModel object
			A table model must be provided for the storage of marker locations.
		"""
		super().__init__()
		# Create the figure/canvas.
		self.fig = plt.figure(constrained_layout=True)
		self.fig.patch.set_facecolor('#000000')
		# Create the canvas.
		self.canvas = FigureCanvasQTAgg(self.fig)
		# Create the figure manager.
		self.figureManager = FigureManagerQT(self.canvas,1)
		# Create the toolbar manager.
		self.toolbarManager = self.figureManager.toolbar.toolmanager
		# Create the toolbar
		self.toolbar = self.figureManager.toolbar
		# Reference to ax.imshows().
		self.images = {}
		# All overlay plots.
		self.overlays = [[],[]]

		# Create 2 axes.
		self.ax = self.fig.subplots(1,2,gridspec_kw={'hspace':0,'wspace':0,'left':0,'right':1,'bottom':0,'top':1},sharey=False)
		for idx, ax in enumerate(self.ax):
			# Set up the axes.
			ax.set_facecolor('#000000')
			ax.title.set_color('#FFFFFF')
			ax.xaxis.label.set_color('#FFFFFF')
			ax.yaxis.label.set_color('#FFFFFF')
			# ax.xaxis.set_label_coords(0.5,0.12)
			# ax.yaxis.set_label_coords(0.12,0.5)
			# ax.xaxis.label.set_size(20)
			# ax.yaxis.label.set_size(20)
			# ax.yaxis.label.set_rotation(90)
			# ax.spines['left'].set_visible(False)
			# ax.spines['top'].set_visible(False)
			# ax.spines['right'].set_visible(False)
			# ax.spines['bottom'].set_visible(False)
			# ax.tick_params('both',which='both',length=7,width=1,pad=-35,direction='in',colors='#FFFFFF')
			ax.xaxis.set_visible(False)
			ax.yaxis.set_visible(False)

		# Get the layout.
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		self.setLayout(layout)

		# Refresh the canvas.
		self.canvas.draw()

	def loadImage(self,index,image):
		# Clear the axes.
		self.ax[index].cla()
		# Write new image.
		self.images[self.ax[index]] = self.ax[index].imshow(image, cmap='cividis')
		# self.images[self.ax[index]] = self.ax[index].imshow(image, cmap='binary')
		# Update the canvas.
		self.canvas.draw()

	def getImage(self,index):
		if self.ax[index] in self.images:
			x1,x2 = self.ax[index].get_xlim()
			y2,y1 = self.ax[index].get_ylim()
			x1,x2,y1,y2 = int(x1),int(x2),int(y1),int(y2)
			return self.images[self.ax[index]].get_array()[y1:y2,x1:x2],[y1,x1]
		else:
			return None,None

	def plotDescriptors(self,index,descriptors,maxDescriptors=0):
		self.clearOverlays(index)
		if len(descriptors) == 0: return
		if (maxDescriptors > len(descriptors)) or (maxDescriptors == 0):
			maxDescriptors=len(descriptors)
		# Plot positions.
		self.ax[index].set_title("Showing {}/{} Keypoints".format(maxDescriptors,len(descriptors)),fontdict={'color':'#FFFFFF'})
		for i in range(0,len(descriptors),int(len(descriptors)/maxDescriptors)):
			# Points.
			self.overlays[index].append(
				self.ax[index].scatter(
					descriptors[i,1]*descriptors[i,2],
					descriptors[i,0]*descriptors[i,2],
					ec='k',fc='none',marker='o'
				)
			)
			# Arrows.
			x = descriptors[i,1]*descriptors[i,2]
			y = descriptors[i,0]*descriptors[i,2]
			dx = 10*np.cos(descriptors[i,3])
			dy = 10*np.sin(descriptors[i,3])
			self.overlays[index].append( self.ax[index].arrow(x,y,dx,dy) )
		self.canvas.draw()

	def clearOverlays(self,index=-1):
		if index == -1:
			# Clear everything in list.
			for overlays in self.overlays:
				for overlay in overlays:
					overlay.remove()
			# Reset list.
			self.overlays = [[],[]]
		else:
			for overlay in self.overlays[index]:
				overlay.remove()
			# Reset list.
			self.overlays[index] = []
		# Refresh canvas.
		self.canvas.draw()

	def clearAll(self):
		""" Clears all images in the plot. """
		for ax in self.ax:
			# Clear the plot.
			ax.cla()
		# Remove all references to ax.imshows.
		self.images.clear()
		self.overlays = [[],[]]
		# Refresh the canvas.
		self.canvas.draw()