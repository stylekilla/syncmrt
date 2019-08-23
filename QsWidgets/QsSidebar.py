from PyQt5 import QtWidgets, QtGui, QtCore
from functools import partial
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
		self.widget['anatomical'] = QtWidgets.QRadioButton('Anatomical')
		self.widget['fiducial'] = QtWidgets.QRadioButton('Fiducial')
		self.widget['optimise'] = QtWidgets.QCheckBox('Optimise')
		label2 = QtWidgets.QLabel('Marker Size (mm):')
		self.widget['markerSize'] = QtWidgets.QDoubleSpinBox()
		label3 = QtWidgets.QLabel('Threshold (%):')
		self.widget['threshold'] = QtWidgets.QDoubleSpinBox()
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
		alignGroup.setTitle('Patient Alignment')
		self.widget['calcAlignment'] = QtWidgets.QPushButton('Calculate')
		self.widget['doAlignment'] = QtWidgets.QPushButton('Align')
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
		self.theta = [-2,2]
		self.translation = [-10,15]
		self.thetaRange = [-90,90]
		self.translationRange = [-100,100]
		# Layout.
		self.layout = QtWidgets.QVBoxLayout()

		'''
		GROUP: Available Images
		'''
		# Imaging settings.
		self.group['availableImages'] = QtWidgets.QGroupBox("Imaging Sequence")
		imagingSequence_layout = QtWidgets.QFormLayout()
		# imagingSequence_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		# Num images.
		lblImages = QtWidgets.QLabel("Select Image:")
		self.widget['imageList'] = QtWidgets.QComboBox()
		self.widget['imageList'].setMinimumSize(65,20)
		# self.widget['imageList'].addItem("<new>")
		# self.widget['imageList'].valueChanged.connect()
		imagingSequence_layout.addRow(lblImages,self.widget['imageList'])
		# Acquire button.
		# self.widget['load'] = QtWidgets.QPushButton("load")
		# self.widget['load'].setEnabled(False)
		# self.widget['load'].clicked.connect(self.loadImages)
		# imagingSequence_layout.addRow(self.widget['load'])
		# Set the group layout.
		self.group['availableImages'].setLayout(imagingSequence_layout)


		'''
		GROUP: Imaging Angles
		'''
		# Imaging settings.
		self.group['imagingSequence'] = QtWidgets.QGroupBox("Imaging Sequence")
		imagingSequence_layout = QtWidgets.QFormLayout()
		# imagingSequence_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		# Num images.
		lblImages = QtWidgets.QLabel("Number of Images")
		self.widget['numImages'] = QtWidgets.QSpinBox()
		self.widget['numImages'].setMinimumSize(55,20)
		# self.widget['numImages'].setMaximumSize(55,20)
		self.widget['numImages'].setRange(1,2)
		self.widget['numImages'].setValue(2)
		self.widget['numImages'].valueChanged.connect(self.updateNumImages)
		imagingSequence_layout.addRow(lblImages,self.widget['numImages'])
		imagingSequence_layout.addRow(QHLine())
		# Translation Range.
		self.widget['translation_range'] = QtWidgets.QLabel("Region Of Interest:")
		imagingSequence_layout.addRow(self.widget['translation_range'])
		# translation 1
		self.widget['translation1_label'] = QtWidgets.QLabel("Z<sub>upper</sub> mm")
		self.widget['translation1'] = QtWidgets.QDoubleSpinBox()
		self.widget['translation1'].setMinimumSize(55,20)
		self.widget['translation1'].setDecimals(1)
		self.widget['translation1'].setMinimum(self.translationRange[0])
		self.widget['translation1'].setMaximum(self.translationRange[1])
		self.widget['translation1'].setValue(self.translation[1])
		imagingSequence_layout.addRow(self.widget['translation1_label'],self.widget['translation1'])
		# translation 2
		self.widget['translation2_label'] = QtWidgets.QLabel("Z<sub>lower</sub> mm")
		self.widget['translation2'] = QtWidgets.QDoubleSpinBox()
		self.widget['translation2'].setMinimumSize(55,20)
		self.widget['translation2'].setDecimals(1)
		self.widget['translation2'].setMinimum(self.translationRange[0])
		self.widget['translation2'].setMaximum(self.translationRange[1])
		self.widget['translation2'].setValue(self.translation[0])
		imagingSequence_layout.addRow(self.widget['translation2_label'],self.widget['translation2'])
		# Range.
		# imagingSequence_layout.addRow(QtWidgets.QLabel("Image Angles"))
		self.widget['theta_range'] = QtWidgets.QLabel("Angles Range ({}, {})\xB0:".format(self.thetaRange[0],self.thetaRange[1]))
		imagingSequence_layout.addRow(self.widget['theta_range'])
		# Theta 1
		self.widget['theta1_label'] = QtWidgets.QLabel("\u03B8<sub>1</sub>\u00B0")
		self.widget['theta1'] = QtWidgets.QDoubleSpinBox()
		self.widget['theta1'].setMinimumSize(55,20)
		self.widget['theta1'].setDecimals(1)
		self.widget['theta1'].setMinimum(self.thetaRange[0])
		self.widget['theta1'].setMaximum(self.thetaRange[1])
		self.widget['theta1'].setValue(self.theta[0])
		imagingSequence_layout.addRow(self.widget['theta1_label'],self.widget['theta1'])
		# Theta 2
		self.widget['theta2_label'] = QtWidgets.QLabel("\u03B8<sub>2</sub>\u00B0")
		self.widget['theta2'] = QtWidgets.QDoubleSpinBox()
		self.widget['theta2'].setMinimumSize(55,20)
		self.widget['theta2'].setDecimals(1)
		self.widget['theta2'].setMinimum(self.thetaRange[0])
		self.widget['theta2'].setMaximum(self.thetaRange[1])
		self.widget['theta2'].setValue(self.theta[1])
		imagingSequence_layout.addRow(self.widget['theta2_label'],self.widget['theta2'])
		# Comments.
		self.widget['comment'] = QtWidgets.QLineEdit()
		# self.widget['comment'].setAcceptRichText(False)
		self.widget['comment'].setMaximumHeight(20)
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
		# imagingSequence_layout.addRow(self.widget['step'],self.widget['scan'])
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
		self.widget['theta1'].setMinimum(self.thetaRange[0])
		self.widget['theta1'].setMaximum(self.thetaRange[1])
		# Theta 2
		self.widget['theta2'].setMinimum(self.thetaRange[0])
		self.widget['theta2'].setMaximum(self.thetaRange[1])

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
		'''Once treatment plan is loaded, add the treatments to the workflow.'''
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
	refreshConnections = QtCore.pyqtSignal()

	def __init__(self):
		super().__init__()
		self.controls = {}
		self.hardware = {}
		self.layout = QtWidgets.QVBoxLayout()

		# # Group 1: Controls Level
		# controlsGroup = QtWidgets.QGroupBox()
		# controlsGroup.setTitle('Control Complexity')
		# self.controls['rbSimple'] = QtWidgets.QRadioButton('Simple')
		# self.controls['rbNormal'] = QtWidgets.QRadioButton('Normal')
		# self.controls['rbComplex'] = QtWidgets.QRadioButton('Complex')
		# self.controls['cbReadOnly'] = QtWidgets.QCheckBox('Read Only')
		# self.controls['complexity'] = 'simple'
		# # Layout
		# controlsGroupLayout = QtWidgets.QVBoxLayout()
		# controlsGroupLayout.addWidget(self.controls['rbSimple'])
		# controlsGroupLayout.addWidget(self.controls['rbNormal'])
		# controlsGroupLayout.addWidget(self.controls['rbComplex'])
		# controlsGroupLayout.addWidget(self.controls['cbReadOnly'])
		# controlsGroup.setLayout(controlsGroupLayout)

		# Group 2: Hardware
		hardwareGroup = QtWidgets.QGroupBox()
		hardwareGroup.setTitle('Hardware Configuration')
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
		hardwareGroup.setLayout(hardwareGroupLayout)

		# Defaults
		# self.controls['rbSimple'].setChecked(True)
		# self.controls['cbReadOnly'].setChecked(True)
		# Signals and Slots
		# self.controls['rbSimple'].clicked.connect(self.controlsMode)
		# self.controls['rbNormal'].clicked.connect(self.controlsMode)
		# self.controls['rbComplex'].clicked.connect(self.controlsMode)
		self.hardware['stage'].currentIndexChanged.connect(self.stageChange)
		self.hardware['detector'].currentIndexChanged.connect(self.detectorChange)
		self.hardware['refresh'].clicked.connect(self._refreshConnections)
		# Add Sections
		# self.layout.addWidget(controlsGroup)
		self.layout.addWidget(hardwareGroup)
		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	# def controlsMode(self):
	# 	''' Set complexity of controls. '''
	# 	if self.controls['rbSimple'].isChecked():
	# 		self.controls['complexity'] = 'simple'
	# 	elif self.controls['rbNormal'].isChecked():
	# 		self.controls['complexity'] = 'normal'
	# 	elif self.controls['rbComplex'].isChecked():
	# 		self.controls['complexity'] = 'complex'

	# 	# Emit signal to say state has changed.
	# 	self.modeChanged.emit(self.controls['complexity'])

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

	def __init__(self,parent=None):
		super().__init__()
		# self.parent = parent
		self.widget = {}
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

		# Group 1: Editable Isocenter
		# editIsocenter = QtWidgets.QGroupBox()
		# editIsocenter.setTitle('Edit Treatment Isocenter')
		# label1 = QtWidgets.QLabel('Isocenter (mm)')
		# label2 = QtWidgets.QLabel('x: ')
		# self.widget['alignIsocX'] = QtWidgets.QLineEdit()
		# label3 = QtWidgets.QLabel('y: ')
		# self.widget['alignIsocY'] = QtWidgets.QLineEdit()
		# Layout
		# editIsocenterLayout = QtWidgets.QFormLayout()
		# editIsocenterLayout.addRow(label1)
		# editIsocenterLayout.addRow(label2,self.widget['alignIsocX'])
		# editIsocenterLayout.addRow(label3,self.widget['alignIsocY'])
		# # Defaults
		# validator = QtGui.QDoubleValidator()
		# validator.setBottom(0)
		# validator.setDecimals(4)
		# self.widget['alignIsocX'].setValidator(validator)
		# self.widget['alignIsocY'].setValidator(validator)
		# # Signals and Slots
		# # Group inclusion to page
		# editIsocenter.setLayout(editIsocenterLayout)
		# self.layout.addWidget(editIsocenter)

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
	isocenterChanged = QtCore.pyqtSignal(float,float,float)
	toggleOverlay = QtCore.pyqtSignal(int,bool)
	updateCtView = QtCore.pyqtSignal(str)

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
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group: Editable Isocenter
		# self.group['editIsocenter'] = editIsocenter = QtWidgets.QGroupBox()
		# self.group['editIsocenter'] = QtWidgets.QGroupBox()
		# self.group['editIsocenter'].setTitle('Edit Treatment Isocenter')
		# label1 = QtWidgets.QLabel('Isocenter (mm)')
		# label2 = QtWidgets.QLabel('x: ')
		# self.widget['isocX'] = QtWidgets.QLineEdit()
		# label3 = QtWidgets.QLabel('y: ')
		# self.widget['isocY'] = QtWidgets.QLineEdit()
		# label4 = QtWidgets.QLabel('z: ')
		# self.widget['isocZ'] = QtWidgets.QLineEdit()
		# # Layout
		# editIsocenterLayout = QtWidgets.QFormLayout()
		# editIsocenterLayout.addRow(label1)
		# editIsocenterLayout.addRow(label2,self.widget['isocX'])
		# editIsocenterLayout.addRow(label3,self.widget['isocY'])
		# editIsocenterLayout.addRow(label4,self.widget['isocZ'])
		# # Defaults
		# self.group['editIsocenter'].setEnabled(False)
		# doubleValidator = QtGui.QDoubleValidator()
		# # doubleValidator.setBottom(0)
		# doubleValidator.setDecimals(3)
		# self.widget['isocX'].setText('0')
		# self.widget['isocY'].setText('0')
		# self.widget['isocZ'].setText('0')
		# self.widget['isocX'].setValidator(doubleValidator)
		# self.widget['isocY'].setValidator(doubleValidator)
		# self.widget['isocZ'].setValidator(doubleValidator)
		# # Signals and Slots
		# self.widget['isocX'].returnPressed.connect(self.updateIsocenter)
		# self.widget['isocY'].returnPressed.connect(self.updateIsocenter)
		# self.widget['isocZ'].returnPressed.connect(self.updateIsocenter)
		# # Group inclusion to page
		# self.group['editIsocenter'].setLayout(editIsocenterLayout)
		# self.layout.addWidget(self.group['editIsocenter'])

		# Group: View.
		self.group['view'] = QtWidgets.QGroupBox()
		self.group['view'].setTitle('CT View')
		view = QtWidgets.QLabel('Primary View:')
		self.widget['view'] = QtWidgets.QComboBox()
		self.widget['view'].addItem("Coronal (AP)")
		self.widget['view'].addItem("Coronal (PA)")
		# Layout
		viewGroupLayout = QtWidgets.QVBoxLayout()
		viewGroupLayout.addWidget(view)
		viewGroupLayout.addWidget(self.widget['view'])
		# Defaults
		self.group['view'].setEnabled(False)
		self.widget['view'].setCurrentIndex(0)

		# Signals and Slots
		# self.widget['view'].currentIndexChanged.connect(partial(self.updateCtView.emit,self.widget['view'].currentText()[-3:-1]))
		self.widget['view'].currentIndexChanged.connect(self.emitUpdateCtView)
		# self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		# self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
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

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().setParent(None)
		# New widgets.
		for i in range(len(widget)):
			widget[i].setMaximumHeight(200)
			layout.addWidget(widget[i])

	def emitUpdateCtView(self):
		view = self.widget['view'].currentText()[-3:-1]
		self.updateCtView.emit(view)

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