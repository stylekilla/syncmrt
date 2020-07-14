from PyQt5 import QtWidgets, QtCore
from .. import QsGeneric
from functools import partial
import logging

class QImaging(QtWidgets.QWidget):
	# Acquire image sends: (theta,zTranslation)
	acquire = QtCore.pyqtSignal(list,list,str)
	numberOfImagesChanged = QtCore.pyqtSignal(int)
	imageSetChanged = QtCore.pyqtSignal(str)
	imageModeChanged = QtCore.pyqtSignal(str)
	# Storage.
	widget = {}
	group = {}

	def __init__(self):
		super().__init__()
		# Vars.
		self.theta = [90,0]
		self.translation = [-20,20]
		self.thetaRange = [-90,90]
		self.translationRange = [-100,100]
		# Layout.
		self.layout = QtWidgets.QVBoxLayout()

		'''
		GROUP: Available Images
		'''


		'''
		GROUP: Available Images
		'''
		# Imaging settings.
		self.group['availableImages'] = QtWidgets.QGroupBox("Select Image")
		imagingSequence_layout = QtWidgets.QFormLayout()
		# imagingSequence_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		# Num images.
		lblImages = QtWidgets.QLabel("Select Image:")
		self.widget['imageList'] = QtWidgets.QComboBox()
		self.widget['imageList'].setMinimumSize(65,20)
		self.widget['imageList'].setToolTip("Select an existing image.")
		commentLabel = QtWidgets.QLabel("Comment:")
		self.widget['currentImageComment'] = QtWidgets.QLabel("-")
		imagingSequence_layout.addRow(lblImages,self.widget['imageList'])
		imagingSequence_layout.addRow(commentLabel,self.widget['currentImageComment'])
		# Set the group layout.
		self.group['availableImages'].setLayout(imagingSequence_layout)

		'''
		GROUP: Imaging Angles
		'''
		# Imaging settings.
		self.group['imagingSequence'] = QtWidgets.QGroupBox("Acquire New Image")
		imagingSequence_layout = QtWidgets.QFormLayout()
		# imagingSequence_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		# Num images.
		lblImages = QtWidgets.QLabel("Number of Images")
		self.widget['numImages'] = QtWidgets.QSpinBox()
		self.widget['numImages'].setMinimumSize(55,20)
		self.widget['numImages'].setRange(1,2)
		self.widget['numImages'].setValue(2)
		self.widget['numImages'].valueChanged.connect(self.updateNumImages)
		self.widget['numImages'].setToolTip("The number of images to acquire, this can be 1 (2D alignment) or 2 (3D alignment).")
		imagingSequence_layout.addRow(lblImages,self.widget['numImages'])
		imagingSequence_layout.addRow(QsGeneric.QHLine())

		# Angular range.
		self.widget['theta_range'] = QtWidgets.QLabel("Imaging Angles:")
		imagingSequence_layout.addRow(self.widget['theta_range'])
		# Theta 1
		self.widget['theta1_label'] = QtWidgets.QLabel("\u03B8<sub>1</sub>\u00B0 [0,90]")
		self.widget['theta1'] = QtWidgets.QDoubleSpinBox()
		self.widget['theta1'].setMinimumSize(55,20)
		self.widget['theta1'].setDecimals(1)
		self.widget['theta1'].setMinimum(0)
		self.widget['theta1'].setMaximum(self.thetaRange[1])
		self.widget['theta1'].setValue(90)
		self.widget['theta1'].setToolTip("Choose the first imaging angle, must be between 0 and 90.")
		imagingSequence_layout.addRow(self.widget['theta1_label'],self.widget['theta1'])
		# Theta 2
		self.widget['theta2_label'] = QtWidgets.QLabel("\u03B8<sub>2</sub>\u00B0 [-90,0]")
		self.widget['theta2'] = QtWidgets.QDoubleSpinBox()
		self.widget['theta2'].setMinimumSize(55,20)
		self.widget['theta2'].setDecimals(1)
		self.widget['theta2'].setMinimum(self.thetaRange[0])
		self.widget['theta2'].setMaximum(0)
		self.widget['theta2'].setValue(0)
		self.widget['theta2'].setToolTip("Choose the second imaging angle, must be between -90 and 0.")
		imagingSequence_layout.addRow(self.widget['theta2_label'],self.widget['theta2'])

		# Translation Range.
		lblROI = QtWidgets.QLabel("Vertical Region Of Interest:")
		imagingSequence_layout.addRow(lblROI)
		# translation 1
		self.widget['translation1_label'] = QtWidgets.QLabel("Z<sub>upper</sub> mm")
		self.widget['translation1'] = QtWidgets.QDoubleSpinBox()
		self.widget['translation1'].setMinimumSize(55,20)
		self.widget['translation1'].setDecimals(1)
		self.widget['translation1'].setMinimum(self.translationRange[0])
		self.widget['translation1'].setMaximum(self.translationRange[1])
		self.widget['translation1'].setValue(self.translation[1])
		self.widget['translation1'].setToolTip("Distance to image above the current patient position.")
		imagingSequence_layout.addRow(self.widget['translation1_label'],self.widget['translation1'])
		# translation 2
		self.widget['translation2_label'] = QtWidgets.QLabel("Z<sub>lower</sub> mm")
		self.widget['translation2'] = QtWidgets.QDoubleSpinBox()
		self.widget['translation2'].setMinimumSize(55,20)
		self.widget['translation2'].setDecimals(1)
		self.widget['translation2'].setMinimum(self.translationRange[0])
		self.widget['translation2'].setMaximum(self.translationRange[1])
		self.widget['translation2'].setValue(self.translation[0])
		self.widget['translation2'].setToolTip("Distance to image below the current patient position.")
		imagingSequence_layout.addRow(self.widget['translation2_label'],self.widget['translation2'])

		# Comments.
		self.widget['comment'] = QtWidgets.QLineEdit()
		# self.widget['comment'].setAcceptRichText(False)
		self.widget['comment'].setMaximumHeight(20)
		self.widget['comment'].setToolTip("Write a comment for the image(s).")
		imagingSequence_layout.addRow(QtWidgets.QLabel("Comment:"))
		imagingSequence_layout.addRow(self.widget['comment'])
		imagingSequence_layout.addRow(QsGeneric.QHLine())
		# Acquire button.
		self.widget['step'] = QtWidgets.QRadioButton("Step")
		self.widget['step'].setChecked(True)
		self.widget['scan'] = QtWidgets.QRadioButton("Scan")
		self.widget['step'].toggled.connect(partial(self._imageModeChanged,'step'))
		self.widget['scan'].toggled.connect(partial(self._imageModeChanged,'scan'))
		self.widget['acquire'] = QtWidgets.QPushButton("Acquire X-rays")
		self.widget['acquire'].setEnabled(False)
		self.widget['acquire'].clicked.connect(self.acquireImages)
		self.widget['acquire'].setToolTip("Acquire x-ray image(s).")
		imagingSequence_layout.addRow(self.widget['acquire'])
		# Set the group layout.
		self.group['imagingSequence'].setLayout(imagingSequence_layout)

		# Add the widgets to the layout.
		self.layout.addWidget(self.group['availableImages'])
		self.layout.addWidget(self.group['imagingSequence'])
		self.layout.addStretch(1)
		# Add the layout to the QImaging widget.
		self.setLayout(self.layout)

		# Signals.
		self.widget['imageList'].currentTextChanged.connect(self.imageSetChanged)

	def _imageModeChanged(self,mode,state):
		if state is True:
			self.imageModeChanged.emit(mode)

	def updateSeparationRange(self,newRange):
		# Get new range.
		self.thetaRange = newRange
		a, b = self.thetaRange
		# Update text label.
		self.widget['theta_range'].setText("Range: ({}, {})\xB0".format(a,b))
		# Update double spin boxes.
		# Theta 1
		self.widget['theta1'].setMinimum(self.thetaRange[1])
		self.widget['theta1'].setMaximum(0)
		# Theta 2
		self.widget['theta2'].setMinimum(0)
		self.widget['theta2'].setMaximum(self.thetaRange[0])

	def updateNumImages(self):
		# Get current value.
		i = int(self.widget['numImages'].value())
		layout = self.group['imagingSequence'].layout()
		if i == 1:
			# If only 1 image, remove theta 2.
			layout.takeRow(self.widget['theta2'])
			self.widget['theta2_label'].setVisible(False)
			self.widget['theta2'].setVisible(False)
		else:
			# If 2 images, add theta 2.
			row, col = layout.getWidgetPosition(self.widget['theta1'])
			layout.insertRow(row+1,self.widget['theta2_label'],self.widget['theta2'])
			self.widget['theta2_label'].setVisible(True)
			self.widget['theta2'].setVisible(True)
		self.numberOfImagesChanged.emit(i)

	def acquireImages(self):
		# Gather theta values.
		i = int(self.widget['numImages'].value())
		if i == 1:
			theta = [self.widget['theta1'].value()]
		else:
			theta = [self.widget['theta1'].value(),self.widget['theta2'].value()]
		# zTranslation is [lower,upper]
		zTranslation = [self.widget['translation2'].value(),self.widget['translation1'].value()]
		# Comment.
		comment = self.widget['comment'].text()
		# Emit signal.
		self.acquire.emit(theta, zTranslation, comment)

	def enableAcquisition(self):
		self.widget['acquire'].setEnabled(True)

	def disableAcquisition(self):
		self.widget['acquire'].setEnabled(False)

	def resetImageSetList(self):
		logging.info("Image set list cleared.")
		self.widget['imageList'].clear()

	def addImageSet(self,_setName):
		logging.debug("Adding {} to image set list.".format(_setName))
		if type(_setName) is list:
			for _set in _setName:
				self.widget['imageList'].addItem(_set)
		else:
			self.widget['imageList'].addItem(_setName)
		# Set to the latest image set.
		self.widget['imageList'].setCurrentIndex(self.widget['imageList'].count()-1)

	def updateCurrentImageDetails(self,comment):
		""" Update the current image comment. """
		text = str(comment)
		self.widget['currentImageComment'].setText(text)
