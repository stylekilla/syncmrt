import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys
import imageio
from testguiPlot import QPlot
# from matplotlib import pyplot as plt
# from matplotlib.patches import ConnectionPatch
# import pydicom as dicom
import logging
# import os
import testGpu

# Select Qt5 user interface.
qtCreatorFile = "siftgui.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class main(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		# Inititate UI.
		QtWidgets.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		# Window Attributes.
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setWindowTitle('SIFT GUI')
		# Add plot widget.
		self.plot = QPlot()
		self.wgtPlot.addWidget(self.plot)
		self.wgtPlot.setCurrentWidget(self.plot)
		# Connections.
		self.pbLoad.clicked.connect(self.loadImages)
		self.pbCalculateSIFT.clicked.connect(self.calculateSIFT)
		self.pbClear.clicked.connect(self.clearAxes)
		# Start the gpu.
		self._gpu = testGpu.gpu()

	def loadImages(self):
		# Get image filenames.
		fn1 = self.inpImage1.text()
		fn2 = self.inpImage2.text()
		# Image 1.
		try:
			image1 = imageio.imread(fn1,as_gray=True)
			self.plot.loadImage(0,image1)
		except:
			logging.warning("Could not load Image 1")
		# Image 2.
		try:	
			image2 = imageio.imread(fn2,as_gray=True)
			self.plot.loadImage(1,image2)
		except:
			logging.warning("Could not load Image 2")

	def calculateSIFT(self):
		try:
			# Params.
			sigma = float(self.inpSigma.text())
			contrast = float(self.inpContrast.text())
			curvature = float(self.inpCurvature.text())
			upsample = bool(self.inpUpsample.isChecked())
		except:
			logging.warning("Could not get all parameters.")
			return
		# Run SIFT.
		if type(self.plot.getImage(0)[0]) != type(None):
			image,offset = self.plot.getImage(0)
			_, descriptors = self._gpu.findFeaturesSIFT(image,sigma=sigma,contrast=contrast,curvature=curvature,upsample=upsample,plot=False)
			logging.warning("Found {} features.".format(len(descriptors)))
			if len(descriptors) > 0:
				descriptors[:,:2] += offset
				self.plot.plotDescriptors(0,descriptors,int(self.inpNKeypoints.text()))

		if type(self.plot.getImage(1)[0]) != type(None):
			image,offset = self.plot.getImage(1)
			_, descriptors = self._gpu.findFeaturesSIFT(image,sigma=sigma,contrast=contrast,curvature=curvature,upsample=upsample,plot=False)
			logging.warning("Found {} features.".format(len(descriptors)))
			if len(descriptors) > 0: 
				descriptors[:,:2] += offset
				self.plot.plotDescriptors(1,descriptors,int(self.inpNKeypoints.text()))

	def clearAxes(self):
		# Clear the plots.
		self.plot.clearOverlays()

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())