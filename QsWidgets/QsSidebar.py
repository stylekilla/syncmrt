from PyQt5 import QtWidgets, QtGui, QtCore
from functools import partial
from resources import config
import QsWidgets
import logging

class QAlignment(QtWidgets.QWidget):
	markersChanged = QtCore.pyqtSignal(int)
	calculateAlignment = QtCore.pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Markers
		markerGroup = QtWidgets.QGroupBox()
		markerGroup.setTitle('Marker Options')
		label1 = QtWidgets.QLabel('No. of Markers:')
		self.widget['maxMarkers'] = QtWidgets.QSpinBox()
		self.widget['maxMarkers'].setRange(3,10)
		self.widget['maxMarkers'].valueChanged.connect(self.updateMarkers)
		self.widget['maxMarkers'].setToolTip("Number of markers to use for registration.")
		self.widget['anatomical'] = QtWidgets.QRadioButton('Anatomical')
		self.widget['anatomical'].setToolTip("Align using anatomical features.")
		self.widget['fiducial'] = QtWidgets.QRadioButton('Fiducial')
		self.widget['fiducial'].setToolTip("Align using fiducials, offers optimisation parameters.")
		self.widget['optimise'] = QtWidgets.QCheckBox('Optimise')
		self.widget['optimise'].setToolTip("Optimise the fiducial positions.")
		label2 = QtWidgets.QLabel('Marker Size (mm):')
		self.widget['markerSize'] = QtWidgets.QDoubleSpinBox()
		self.widget['markerSize'].setToolTip("Choose the largest dimension of the fiducial markers used.")
		label3 = QtWidgets.QLabel('Threshold (%):')
		self.widget['threshold'] = QtWidgets.QDoubleSpinBox()
		self.widget['threshold'].setToolTip("Threshold for optimisation. Playing with this will change optimisation results.")
		# Layout
		markerGroupLayout = QtWidgets.QFormLayout()
		markerGroupLayout.addRow(label1,self.widget['maxMarkers'])
		markerGroupLayout.addRow(self.widget['anatomical'])
		markerGroupLayout.addRow(self.widget['fiducial'])
		markerGroupLayout.addRow(self.widget['optimise'])
		markerGroupLayout.addRow(label2,self.widget['markerSize'])
		markerGroupLayout.addRow(label3,self.widget['threshold'])
		markerGroup.setLayout(markerGroupLayout)
		self.layout.addWidget(markerGroup)
		# Default Positions
		self.widget['optimise'].setEnabled(False)
		self.widget['anatomical'].setChecked(True)
		self.widget['markerSize'].setEnabled(False)
		self.widget['markerSize'].setRange(1,5)
		self.widget['markerSize'].setSingleStep(0.25)
		self.widget['markerSize'].setValue(2.00)
		self.widget['maxMarkers'].setMinimum(1)
		self.widget['maxMarkers'].setValue(config.markers.quantity)
		self.widget['threshold'].setEnabled(False)
		self.widget['threshold'].setRange(0,50)
		self.widget['threshold'].setValue(3)
		self.widget['threshold'].setSingleStep(0.5)
		# Signals and Slots
		self.widget['anatomical'].toggled.connect(self.markerMode)
		self.widget['fiducial'].toggled.connect(self.markerMode)
		self.widget['optimise'].toggled.connect(self.markerMode)

		# Group 2: Checklist
		alignGroup = QtWidgets.QGroupBox()
		alignGroup.setTitle('Patient Alignment: CT')
		self.widget['calcAlignment'] = QtWidgets.QPushButton('Calculate')
		self.widget['calcAlignment'].setToolTip("Calculate alignment of XR to CT")
		self.widget['doAlignment'] = QtWidgets.QPushButton('Align')
		self.widget['doAlignment'].setToolTip("Perform the calculated alignment")
		# Layout
		alignGroupLayout = QtWidgets.QFormLayout()
		alignGroupLayout.addRow(self.widget['calcAlignment'],self.widget['doAlignment'])
		alignGroup.setLayout(alignGroupLayout)
		self.layout.addWidget(alignGroup)
		# Defaults
		# self.widget['doAlignment'].setEnabled(False)
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)

	def updateMarkers(self,value):
		# Send signal that the number of markers has changed.
		self.markersChanged.emit(value)

	def markerMode(self):
		'''If fiducial markers are chosen then enable optimisation checkbox and sizing.'''
		# Enabling/toggling optimise.
		if self.widget['fiducial'].isChecked():
			self.widget['optimise'].setEnabled(True)
		else:
			self.widget['optimise'].setEnabled(False)
			self.widget['optimise'].setChecked(False)
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

		# Enabling/toggling markerSize.
		if self.widget['optimise'].isChecked():
			self.widget['markerSize'].setEnabled(True)
			self.widget['threshold'].setEnabled(True)
		else:
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

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
		imagingSequence_layout.addRow(QHLine())

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
		imagingSequence_layout.addRow(QHLine())
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

class QTreatment(QtWidgets.QWidget):
	calculate = QtCore.pyqtSignal(int)
	align = QtCore.pyqtSignal(int)
	deliver = QtCore.pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Treatment Settings
		settingsGroup = QtWidgets.QGroupBox()
		settingsGroup.setTitle('Description')
		label1 = QtWidgets.QLabel('Number of beams: ')
		self.widget['quantity'] = QtWidgets.QLabel()
		# Layout
		settingsGroupLayout = QtWidgets.QFormLayout()
		settingsGroupLayout.addRow(label1,self.widget['quantity'])
		settingsGroup.setLayout(settingsGroupLayout)
		self.layout.addWidget(settingsGroup)
		# Defaults
		self.widget['quantity'].setText(str(0))
		# Signals and Slots

		# Group 2: Deliver Treatment
		# Dict for beam plan group widgets.
		self.widget['beamGroup'] = QtWidgets.QGroupBox()
		self.widget['beamGroup'].setVisible(False)
		self.widget['beamGroup'].setTitle('Beam Sequence')
		# Empty Layout, start by saying no RTPLAN loaded.
		self.widget['beamSequence'] = QtWidgets.QFormLayout()
		self.widget['noTreatment'] = QtWidgets.QLabel('No Treatment Plan loaded.')
		self.widget['beamSequence'].addRow(self.widget['noTreatment'])
		self.widget['beamGroup'].setLayout(self.widget['beamSequence'])
		self.layout.addWidget(self.widget['beamGroup'])
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)

	def populateTreatments(self):
		""" Once treatment plan is loaded, add the treatments to the workflow. """
		# Remove the no treatment widget.
		self.widget['noTreatment'].deleteLater()
		del self.widget['noTreatment']
		# Enable the group widget again.
		self.widget['beamGroup'].setVisible(True)
		self.widget['beam'] = [None]*int(self.widget['quantity'].text())
		# sequenceLayout = QtWidgets.QFormLayout()
		# For each beam specified in the count, add a set of buttons.
		for i in range(int(self.widget['quantity'].text())):
			self.widget['beam'][i] = {}
			label = QtWidgets.QLabel(str('Beam %i'%(i+1)))
			# sequenceGroup = QtWidgets.QGroupBox()

			self.widget['beam'][i]['calculate'] = QtWidgets.QPushButton('Calculate')
			self.widget['beam'][i]['align'] = QtWidgets.QPushButton('Align')
			# self.widget['beam'][i]['hline'] = QHLine()
			self.widget['beam'][i]['interlock'] = QtWidgets.QCheckBox('Interlock')
			self.widget['beam'][i]['deliver'] = QtWidgets.QPushButton('Deliver')
			# Layout
			self.widget['beamSequence'].addRow(label)
			self.widget['beamSequence'].addRow(self.widget['beam'][i]['calculate'],self.widget['beam'][i]['align'])
			self.widget['beamSequence'].addRow(QHLine())
			self.widget['beamSequence'].addRow(self.widget['beam'][i]['interlock'],self.widget['beam'][i]['deliver'])
			# Defaults
			self.widget['beam'][i]['alignmentComplete'] = False
			self.widget['beam'][i]['interlock'].setChecked(True)
			self.widget['beam'][i]['interlock'].setEnabled(False)
			self.widget['beam'][i]['deliver'].setEnabled(False)
			# Signals and Slots
			self.widget['beam'][i]['calculate'].clicked.connect(partial(self._emitCalculate,i))
			self.widget['beam'][i]['align'].clicked.connect(partial(self._emitAlign,i))
			self.widget['beam'][i]['interlock'].stateChanged.connect(partial(self.treatmentInterlock,i))
			self.widget['beam'][i]['deliver'].clicked.connect(partial(self._disableTreatmentDelivery,i))

	def _emitCalculate(self,_id):
		self.calculate.emit(_id)

	def _emitAlign(self,_id):
		self.align.emit(_id)

	def treatmentInterlock(self,index):
		'''Treatment interlock stops treatment from occuring. Requires alignment to be done first.'''
		# Enable interlock button.
		if self.widget['beam'][index]['alignmentComplete'] == True:
			self.widget['beam'][index]['interlock'].setEnabled(True)

		# Enable widget delivery button.
		if self.widget['beam'][index]['interlock'].isChecked():
			self.widget['beam'][index]['deliver'].setEnabled(False)
		else:
			self.widget['beam'][index]['deliver'].setEnabled(True)

	def _disableTreatmentDelivery(self, i):
		self.widget['beam'][i]['interlock'].setEnabled(False)
		self.widget['beam'][i]['deliver'].setEnabled(False)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class QSettings(QtWidgets.QWidget):
	modeChanged = QtCore.pyqtSignal('QString')
	stageChanged = QtCore.pyqtSignal('QString')
	detectorChanged = QtCore.pyqtSignal('QString')
	maskSizeChanged = QtCore.pyqtSignal(float)
	refreshConnections = QtCore.pyqtSignal()

	def __init__(self):
		super().__init__()
		self.controls = {}
		self.hardware = {}
		self.widget = {}
		self.group = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Hardware
		self.group['hardware'] = QtWidgets.QGroupBox()
		self.group['hardware'].setTitle('Hardware Configuration')
		detectorLabel = QtWidgets.QLabel('Stage')
		self.hardware['stage'] = QtWidgets.QComboBox()
		stageLabel = QtWidgets.QLabel('Detector')
		self.hardware['detector'] = QtWidgets.QComboBox()
		self.hardware['refresh'] = QtWidgets.QPushButton("Refresh Connections")
		# Layout
		hardwareGroupLayout = QtWidgets.QVBoxLayout()
		hardwareGroupLayout.addWidget(detectorLabel)
		hardwareGroupLayout.addWidget(self.hardware['stage'])
		hardwareGroupLayout.addWidget(stageLabel)
		hardwareGroupLayout.addWidget(self.hardware['detector'])
		hardwareGroupLayout.addWidget(QHLine())
		hardwareGroupLayout.addWidget(self.hardware['refresh'])
		self.group['hardware'].setLayout(hardwareGroupLayout)
		# Signals and Slots
		self.hardware['stage'].currentIndexChanged.connect(self.stageChange)
		self.hardware['detector'].currentIndexChanged.connect(self.detectorChange)
		self.hardware['refresh'].clicked.connect(self._refreshConnections)

		# Mask Settings.
		self.group['mask'] = QtWidgets.QGroupBox()
		self.group['mask'].setTitle("Mask Settings")
		self.widget['maskSize'] = QsWidgets.QRangeEdit()
		self.widget['maskSize'].setRange([0,30.0],20.0)
		self.widget['maskSize'].editingFinished.connect(self._emitMaskSizeChanged)
		# Layout.
		lyt = QtWidgets.QFormLayout()
		lyt.addRow(QtWidgets.QLabel("Size (mm):"),self.widget['maskSize'])
		self.group['mask'].setLayout(lyt)

		# Add Sections
		self.layout.addWidget(self.group['hardware'])
		self.layout.addWidget(self.group['mask'])
		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def loadStages(self,stageList):
		# stageList should be a list of strings of the stages available to choose from.
		self.hardware['motorsList'] = stageList

		# For each item in the list, add it to the drop down list.
		for item in self.hardware['motorsList']:
			self.hardware['stage'].addItem(item)

		# Sort the model alphanumerically.
		self.hardware['stage'].model().sort(0)

	def stageChange(self):
		self.stageChanged.emit(self.hardware['stage'].currentText())

	def _refreshConnections(self):
		self.refreshConnections.emit()

	def _emitMaskSizeChanged(self):
		# Turn the line edit text into a float.
		if self.widget['maskSize'].isValid(): self.maskSizeChanged.emit(float(self.widget['maskSize'].text()))

	def loadDetectors(self,stageList):
		# stageList should be a list of strings of the stages available to choose from.
		self.hardware['detectorList'] = stageList

		# For each item in the list, add it to the drop down list.
		for item in self.hardware['detectorList']:
			self.hardware['detector'].addItem(item)

		# Sort the model alphanumerically.
		self.hardware['detector'].model().sort(0)

	def detectorChange(self):
		self.detectorChanged.emit(self.hardware['detector'].currentText())

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class QXrayProperties(QtWidgets.QWidget):
	toggleOverlay = QtCore.pyqtSignal(int,bool)
	isocenterUpdated = QtCore.pyqtSignal(float,float,float)
	align = QtCore.pyqtSignal(int)

	def __init__(self,parent=None):
		super().__init__()
		# self.parent = parent
		self.widget = {}
		self.group = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 2: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbBeamIsoc'] = QtWidgets.QCheckBox('Beam Isocenter')
		self.widget['cbBeamIsoc'].setToolTip("Shows the synchrotron beam centre.")
		self.widget['cbBeamOverlay'] = QtWidgets.QCheckBox('Beam Overlay')
		self.widget['cbBeamOverlay'].setToolTip("Shows the area to be irradiated.")
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbPatIsoc'].setToolTip("Shows the tumour centre.")
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		self.widget['cbCentroid'].setToolTip("Shows the centre of mass of all selected points.")
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbBeamIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbBeamOverlay'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['cbBeamIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbBeamIsoc'))
		self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
		self.widget['cbBeamOverlay'].stateChanged.connect(partial(self.emitToggleOverlay,'cbBeamOverlay'))
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 2: Editable Isocenter.
		self.widget['isocenter'] = {}
		self.group['isocenter'] = QtWidgets.QGroupBox()
		self.group['isocenter'].setTitle('Tumour Isocenter')
		lytIsocenter = QtWidgets.QVBoxLayout()
		# Add toggle checkbox.
		self.widget['isocenter']['cbCustomIsoc'] = QtWidgets.QCheckBox('Set Custom Isocenter')
		self.widget['isocenter']['cbCustomIsoc'].setToolTip("If enabled, allows the user to set a custom target position.")
		self.widget['isocenter']['cbCustomIsoc'].stateChanged.connect(self._toggleCustomIsocenter)
		# Create an isocenter widget with XYZ toggles in it.
		self.widget['isocenter']['editIso'] = QtWidgets.QWidget()
		label1 = QtWidgets.QLabel('Isocenter (mm)')
		label2 = QtWidgets.QLabel('H1: ')
		self.widget['isocenter']['editIsoX'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('V: ')
		self.widget['isocenter']['editIsoY'] = QtWidgets.QLineEdit()
		label4 = QtWidgets.QLabel('H2: ')
		self.widget['isocenter']['editIsoZ'] = QtWidgets.QLineEdit()
		self.widget['isocenter']['align'] = QtWidgets.QPushButton("Align")
		# Layout
		lytEditIsocenter = QtWidgets.QFormLayout()
		lytEditIsocenter.setContentsMargins(0,0,0,0)
		lytEditIsocenter.addRow(label1)
		lytEditIsocenter.addRow(label2,self.widget['isocenter']['editIsoX'])
		lytEditIsocenter.addRow(label3,self.widget['isocenter']['editIsoY'])
		lytEditIsocenter.addRow(label4,self.widget['isocenter']['editIsoZ'])
		self.widget['isocenter']['editIso'].setLayout(lytEditIsocenter)
		# Validators.
		doubleValidator = QtGui.QDoubleValidator()
		doubleValidator.setDecimals(3)
		self.widget['isocenter']['editIsoX'].setText('0')
		self.widget['isocenter']['editIsoY'].setText('0')
		self.widget['isocenter']['editIsoZ'].setText('0')
		self.widget['isocenter']['editIsoX'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoY'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoZ'].setValidator(doubleValidator)
		# Defaults
		self.widget['isocenter']['editIso'].setEnabled(False)
		self.widget['isocenter']['editIso'].setVisible(False)
		self.widget['isocenter']['align'].setEnabled(False)
		self.widget['isocenter']['align'].setVisible(False)
		# Signals and Slots
		self.widget['isocenter']['editIsoX'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoY'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoZ'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['align'].clicked.connect(partial(self.align.emit,-1))
		# Set the layout of group.
		lytIsocenter.addWidget(self.widget['isocenter']['cbCustomIsoc'])
		lytIsocenter.addWidget(self.widget['isocenter']['editIso'])
		lytIsocenter.addWidget(self.widget['isocenter']['align'])
		self.group['isocenter'].setLayout(lytIsocenter)
		# Add group to sidebar layout.
		self.layout.addWidget(self.group['isocenter'])

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('X-ray Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		self.window['layout'].setContentsMargins(0,0,0,0)
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def _toggleCustomIsocenter(self,state):
		""" Toggles the manual setting of the isocenter on and off. """
		self.widget['isocenter']['editIso'].setEnabled(bool(state))
		self.widget['isocenter']['editIso'].setVisible(bool(state))
		self.widget['isocenter']['align'].setEnabled(bool(state))
		self.widget['isocenter']['align'].setVisible(bool(state))

	def _updateIsocenter(self):
		""" Send a signal with updated x,y coordinates. """
		_x = float(self.widget['isocenter']['editIsoX'].text())
		_y = float(self.widget['isocenter']['editIsoY'].text())
		_z = float(self.widget['isocenter']['editIsoZ'].text())
		self.isocenterUpdated.emit(_x,_y,_z)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().setParent(None)
		# New widgets.
		for i in range(len(widget)):
			widget[i].setMaximumHeight(200)
			layout.addWidget(widget[i])

	def emitToggleOverlay(self,button,state):
		setState = False
		# Identify true or false.
		if state == 0: setState = False
		elif state == 2: setState = True
		# Send the signal.
		if button == 'cbCentroid': self.toggleOverlay.emit(0,setState)
		elif button == 'cbBeamIsoc': self.toggleOverlay.emit(1,setState)
		elif button == 'cbPatIsoc': self.toggleOverlay.emit(2,setState)
		elif button == 'cbBeamOverlay': self.toggleOverlay.emit(3,setState)

	def refreshOverlays(self):
		for item in ['cbBeamIsoc','cbPatIsoc','cbCentroid','cbBeamOverlay']:
			# Toggle them on and off to refresh them.
			self.widget[item].toggle()
			self.widget[item].toggle()


class QCtProperties(QtWidgets.QWidget):
	# Qt signals.
	isocenterUpdated = QtCore.pyqtSignal(float,float,float)
	toggleOverlay = QtCore.pyqtSignal(int,bool)
	updateCtView = QtCore.pyqtSignal(str,tuple,str)

	"""
	The structure of information held in this class is as follows:
		1.	self.group['groupname']
		2.	self.widget['groupname']['widgetname']
	"""

	def __init__(self):
		super().__init__()
		# Continue with sub-class initialisation.
		self.group = {}
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Overlays.
		self.widget['overlays'] = {}
		self.group['overlays'] = QtWidgets.QGroupBox()
		self.group['overlays'].setTitle('Plot Overlays')
		self.widget['overlays']['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['overlays']['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		lytOverlays = QtWidgets.QVBoxLayout()
		lytOverlays.addWidget(self.widget['overlays']['cbPatIsoc'])
		lytOverlays.addWidget(self.widget['overlays']['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['overlays']['cbPatIsoc'].stateChanged.connect(partial(self._emitToggleOverlay,'cbPatIsoc'))
		self.widget['overlays']['cbCentroid'].stateChanged.connect(partial(self._emitToggleOverlay,'cbCentroid'))
		# Group inclusion to page
		self.group['overlays'].setLayout(lytOverlays)
		self.layout.addWidget(self.group['overlays'])

		# Group 2: Editable Isocenter.
		self.widget['isocenter'] = {}
		self.group['isocenter'] = QtWidgets.QGroupBox()
		self.group['isocenter'].setTitle('Tumour Isocenter')
		lytIsocenter = QtWidgets.QVBoxLayout()
		# Add toggle checkbox.
		self.widget['isocenter']['cbCustomIsoc'] = QtWidgets.QCheckBox('Set Custom Isocenter')
		self.widget['isocenter']['cbCustomIsoc'].setToolTip("If enabled, allows the user to set a custom target position.")
		self.widget['isocenter']['cbCustomIsoc'].stateChanged.connect(self._toggleCustomIsocenter)
		# Create an isocenter widget with XYZ toggles in it.
		self.widget['isocenter']['editIso'] = QtWidgets.QWidget()
		label1 = QtWidgets.QLabel('Isocenter (mm)')
		label2 = QtWidgets.QLabel('x: ')
		self.widget['isocenter']['editIsoX'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('y: ')
		self.widget['isocenter']['editIsoY'] = QtWidgets.QLineEdit()
		label4 = QtWidgets.QLabel('z: ')
		self.widget['isocenter']['editIsoZ'] = QtWidgets.QLineEdit()
		# Layout
		lytEditIsocenter = QtWidgets.QFormLayout()
		lytEditIsocenter.setContentsMargins(0,0,0,0)
		lytEditIsocenter.addRow(label1)
		lytEditIsocenter.addRow(label2,self.widget['isocenter']['editIsoX'])
		lytEditIsocenter.addRow(label3,self.widget['isocenter']['editIsoY'])
		lytEditIsocenter.addRow(label4,self.widget['isocenter']['editIsoZ'])
		self.widget['isocenter']['editIso'].setLayout(lytEditIsocenter)
		# Validators.
		doubleValidator = QtGui.QDoubleValidator()
		doubleValidator.setDecimals(3)
		self.widget['isocenter']['editIsoX'].setText('0')
		self.widget['isocenter']['editIsoY'].setText('0')
		self.widget['isocenter']['editIsoZ'].setText('0')
		self.widget['isocenter']['editIsoX'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoY'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoZ'].setValidator(doubleValidator)
		# Defaults
		self.widget['isocenter']['editIso'].setEnabled(False)
		self.widget['isocenter']['editIso'].setVisible(False)
		# Signals and Slots
		self.widget['isocenter']['editIsoX'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoY'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoZ'].editingFinished.connect(self._updateIsocenter)
		# Set the layout of group.
		lytIsocenter.addWidget(self.widget['isocenter']['cbCustomIsoc'])
		lytIsocenter.addWidget(self.widget['isocenter']['editIso'])
		self.group['isocenter'].setLayout(lytIsocenter)
		# Add group to sidebar layout.
		self.layout.addWidget(self.group['isocenter'])

		# Group: View.
		self.group['view'] = QtWidgets.QGroupBox()
		self.group['view'].setTitle('CT View')
		view = QtWidgets.QLabel('Primary View:')
		# Combo box selection.
		self.widget['view'] = {}
		self.widget['view']['select'] = QtWidgets.QComboBox()
		self.widget['view']['select'].addItem("Coronal (AP)")
		self.widget['view']['select'].addItem("Coronal (PA)")
		# Range slider.
		self.widget['view']['xrange'] = QsWidgets.QRangeList('X:')
		self.widget['view']['yrange'] = QsWidgets.QRangeList('Y:')
		self.widget['view']['zrange'] = QsWidgets.QRangeList('Z:')
		self.widget['view']['xrange'].newRange.connect(self._emitUpdateCtView)
		self.widget['view']['yrange'].newRange.connect(self._emitUpdateCtView)
		self.widget['view']['zrange'].newRange.connect(self._emitUpdateCtView)
		# Flattening options.
		self.widget['view']['sum'] = QtWidgets.QRadioButton('Sum')
		self.widget['view']['max'] = QtWidgets.QRadioButton('Max')
		flatteningOptions = QtWidgets.QWidget()
		flatteningOptionsLayout = QtWidgets.QHBoxLayout()
		flatteningOptionsLayout.addWidget(self.widget['view']['sum'])
		flatteningOptionsLayout.addWidget(self.widget['view']['max'])
		flatteningOptions.setLayout(flatteningOptionsLayout)
		self.widget['view']['sum'].setChecked(True)
		self.widget['view']['sum'].toggled.connect(self._emitUpdateCtView)
		self.widget['view']['max'].toggled.connect(self._emitUpdateCtView)
		# Layout
		viewGroupLayout = QtWidgets.QVBoxLayout()
		viewGroupLayout.addWidget(view)
		viewGroupLayout.addWidget(self.widget['view']['select'])
		viewGroupLayout.addWidget(QtWidgets.QLabel("CT ROI (DICOM):"))
		viewGroupLayout.addWidget(self.widget['view']['xrange'])
		viewGroupLayout.addWidget(self.widget['view']['yrange'])
		viewGroupLayout.addWidget(self.widget['view']['zrange'])
		viewGroupLayout.addWidget(flatteningOptions)
		# Defaults
		self.group['view'].setEnabled(False)
		self.widget['view']['select'].setCurrentIndex(0)
		# Signals and Slots
		self.widget['view']['select'].currentIndexChanged.connect(self._emitUpdateCtView)
		# Group inclusion to page
		self.group['view'].setLayout(viewGroupLayout)
		self.layout.addWidget(self.group['view'])

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		self.window['layout'].setContentsMargins(0,0,0,0)
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def _toggleCustomIsocenter(self,state):
		""" Toggles the manual setting of the isocenter on and off. """
		self.widget['isocenter']['editIso'].setEnabled(bool(state))
		self.widget['isocenter']['editIso'].setVisible(bool(state))

	def _updateIsocenter(self):
		""" Send a signal with updated x,y coordinates. """
		_x = float(self.widget['isocenter']['editIsoX'].text())
		_y = float(self.widget['isocenter']['editIsoY'].text())
		_z = float(self.widget['isocenter']['editIsoZ'].text())
		self.isocenterUpdated.emit(_x,_y,_z)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().setParent(None)
		# New widgets.
		for i in range(len(widget)):
			widget[i].setMaximumHeight(200)
			layout.addWidget(widget[i])

	def _emitUpdateCtView(self):
		# Get the CT ROI values.
		_x = self.widget['view']['xrange'].getRange()
		_y = self.widget['view']['yrange'].getRange()
		_z = self.widget['view']['zrange'].getRange()
		roi = _x+_y+_z
		# If a None value is returned then do not send the signal.
		if None in roi: return
		# Get the view.
		view = self.widget['view']['select'].currentText()[-3:-1]
		# Get the mode.
		if self.widget['view']['sum'].isChecked(): mode = 'sum'
		elif self.widget['view']['max'].isChecked(): mode = 'max'
		# Send the signal.
		self.updateCtView.emit(view,roi,mode)

	def _emitToggleOverlay(self,button,state):
		setState = False
		# Identify true or false.
		if state == 0: setState = False
		elif state == 2: setState = True
		# Send the signal.
		if button == 'cbCentroid': self.toggleOverlay.emit(0,setState)
		elif button == 'cbBeamIsoc': self.toggleOverlay.emit(1,setState)
		elif button == 'cbPatIsoc': self.toggleOverlay.emit(2,setState)
		elif button == 'cbBeamOverlay': self.toggleOverlay.emit(3,setState)

	def refreshOverlays(self):
		for item in ['cbBeamIsoc','cbPatIsoc','cbCentroid','cbBeamOverlay']:
			# Toggle them on and off to refresh them.
			self.widget[item].toggle()
			self.widget[item].toggle()

	def setCtRoi(self,extent):
		""" Use an array shape to set the sliders XYZ. """
		self.widget['view']['xrange'].setRange([extent[0],extent[1]])
		self.widget['view']['yrange'].setRange([extent[2],extent[3]])
		self.widget['view']['zrange'].setRange([extent[4],extent[5]])

class QRtplanProperties(QtWidgets.QWidget):
	# Qt signals.
	toggleOverlay = QtCore.pyqtSignal(int,bool)

	def __init__(self):
		# Init QObject class.
		super().__init__()
		# Continue with sub-class initialisation.
		self.group = {}
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbMask'] = QtWidgets.QCheckBox('Isocenter Mask')
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbMask'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		self.widget['cbMask'].stateChanged.connect(partial(self.emitToggleOverlay,'cbMask'))
		self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		# spacer = QtWidgets.QSpacerItem(0,0)
		# self.layout.addSpacerItem(spacer)
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in range(layout.count()):
			layout.removeItem(i)
		# New widgets.
		for i in range(len(widget)):
			layout.addWidget(widget[i])

	def emitToggleOverlay(self,button,state):
		setState = False
		# Identify true or false.
		if state == 0: setState = False
		elif state == 2: setState = True
		# Send the signal.
		if button == 'cbCentroid': self.toggleOverlay.emit(0,setState)
		elif button == 'cbBeamIsoc': self.toggleOverlay.emit(1,setState)
		elif button == 'cbPatIsoc': self.toggleOverlay.emit(2,setState)
		elif button == 'cbMask': self.toggleOverlay.emit(3,setState)
		else: logging.critical('Cannot set button '+str(button)+' to state '+str(setState)+'.')

class QHUSpinBox(QtWidgets.QSpinBox):
	'''CT HU windowing spinbox'''
	def __init__(self):
		super().__init__()
		self.setRange(-1000,5000)
		self.setSingleStep(100)
		self.setValue(-1000)

class QXraySpinBox(QtWidgets.QSpinBox):
	'''Xray windowing spin box'''
	def __init__(self):
		super().__init__()
		self.setRange(0,65535)
		self.setSingleStep(5000)
		self.setValue(0)

class QHLine(QtWidgets.QFrame):
	'''Horizontal line.'''
	def __init__(self):
		super().__init__()
		self.setFrameShape(QtWidgets.QFrame.HLine)
		self.setFrameShadow(QtWidgets.QFrame.Sunken)