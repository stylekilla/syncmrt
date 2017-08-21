from PyQt5 import QtWidgets, QtGui, QtCore, uic
from functools import partial
import numpy as np

resourceFilepath = "resources/"

class sidebarStack(QtWidgets.QStackedWidget):
	def __init__(self,parent):
		super().__init__()
		self.parent = parent
		self.setMinimumHeight(500)
		self.setFixedWidth(225)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.parent.setVisible(False)
		self.stackDict = {}

		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,pageName,before=None,after=None):
		'''Before and after must be names of other pages.'''
		self.stackDict[pageName] = QtWidgets.QWidget()

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.indexOf(self.stackDict[before])

		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.indexOf(self.stackDict[after]) + 1
		else:
			index = self.count()

		self.insertWidget(index,self.stackDict[pageName])

	def removePage(self,pageName,delete=False):
		'''Remove page from stack, delete from memory if required.'''
		self.removeWidget(self.stackDict[pageName])
		if delete: del self.stackDict[pageName]

class sidebarList(QtWidgets.QListWidget):
	def __init__(self,parent):
		# List initialisation.
		super().__init__()
		self.setMinimumHeight(500)
		self.setFixedWidth(60)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setIconSize(QtCore.QSize(50,50))
		# A list of pageNames in the stacked widget (of pages to show and hide).
		self.listDict = {}

		# Add self to parent layout.
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,pageName,before=None,after=None):
		'''Before and after must be names of other pages.'''
		self.listDict[pageName] = QtWidgets.QListWidgetItem()
		self.listDict[pageName].setText(pageName)
		# Add Icon.
		icon = QtGui.QIcon(resourceFilepath+pageName+'.png')
		icon.pixmap(50,50)
		self.listDict[pageName].setIcon(icon)
		self.listDict[pageName].setSizeHint(QtCore.QSize(60,60))

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.row(self.listDict[before]) - 1
		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.row(self.listDict[after]) + 1
		else:
			index = self.count()

		self.insertItem(index,self.listDict[pageName])

	def removePage(self,pageName,delete=False):
		'''Remove page from list, delete from memory if required.'''
		self.removeItemWidget(self.listDict[pageName])

		if delete:
			del self.listDict[pageName]

class sidebarSelector:
	def __init__(self,listWidget,stackWidget):
		self.list = sidebarList(listWidget)
		self.stack = stackWidget
		self._previousListItem = None

		# Signal and slots connections for selecting items in list widget.
		self.list.currentItemChanged.connect(self.previousStack)
		self.list.itemPressed.connect(self.showStack)

	def addPage(self,pageName,addStack=True,addList=True,before=None,after=None):
		'''Before and after must be names of other pages.'''
		if addStack: self.stack.addPage(pageName,before=before,after=after)
		if addList: self.list.addPage(pageName,before=before,after=after)

	def previousStack(self,current,previous):
		'''Keep track of the last item pressed when an item is clicked.'''
		self._previousListItem = previous
		# self.showStack(current)

	def showStack(self,listWidgetItem):
		'''Show workspace based on item clicked/called item. If the active one is re-called, toggle the view on/off.'''
		pageName = None

		if type(listWidgetItem) == str:
			# We have a pageName.
			pass
		else:
			# Find pageName in dictionary that matches listWidgetItem.
			for key, value in self.list.listDict.items():
				if value == listWidgetItem:
					pageName = key

		if pageName is None: return

		if self.list.currentItem() == self._previousListItem:
			self.stack.parent.setVisible(not self.stack.parent.isVisible())
		else:
			self.stack.setCurrentWidget(self.stack.stackDict[pageName])
			self.stack.parent.setVisible(True)
			self._previousListItem = listWidgetItem

	def getListItem(self,key):
		# return self.list.listDict['ImageProperties']
		return self.list.listDict[key]

class sbAlignment:
	def __init__(self,parent):
		self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Markers
		markerGroup = QtWidgets.QGroupBox()
		markerGroup.setTitle('Marker Options')
		label1 = QtWidgets.QLabel('No. of Markers:')
		self.widget['maxMarkers'] = QtWidgets.QSpinBox()
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
		self.widget['doAlignment'].setEnabled(False)
		# Signals and Slots

		# Group 3: Checklist
		checklistGroup = QtWidgets.QGroupBox()
		checklistGroup.setTitle('Checklist')
		self.widget['checkSetup'] = QtWidgets.QLabel('Alignment Setup')
		self.widget['checkXray'] = QtWidgets.QLabel('X-ray')
		self.widget['checkDicom'] = QtWidgets.QLabel('Dicom Image')
		self.widget['checkRTP'] = QtWidgets.QLabel('Treatment Plan')
		# self.widget['check'] = QtWidgets.QPushButton('Check')
		# self.widget['align'] = QtWidgets.QPushButton('Align')
		# Layout
		checklistGroupLayout = QtWidgets.QFormLayout()
		checklistGroupLayout.addRow(self.widget['checkSetup'])
		checklistGroupLayout.addRow(self.widget['checkXray'])
		checklistGroupLayout.addRow(self.widget['checkDicom'])
		checklistGroupLayout.addRow(self.widget['checkRTP'])
		# checklistGroupLayout.addRow(self.widget['check'],self.widget['align'])
		checklistGroup.setLayout(checklistGroupLayout)
		self.layout.addWidget(checklistGroup)
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

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

class sbTreatment:
	def __init__(self,parent):
		self.parent = parent
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
		self.widget['beam'] = {}
		group = QtWidgets.QGroupBox()
		group.setTitle('Deliver Treatment')
		# Empty Layout
		self.widget['deliveryGroup'] = QtWidgets.QFormLayout()
		self.widget['noTreatment'] = QtWidgets.QLabel('No Treatment Plan loaded.')
		self.widget['deliveryGroup'].addRow(self.widget['noTreatment'])
		group.setLayout(self.widget['deliveryGroup'])
		self.layout.addWidget(group)
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

	def populateTreatments(self):
		'''Once treatment plan is loaded, add the treatments to the workflow.'''
		self.widget['noTreatment'].deleteLater()
		del self.widget['noTreatment']

		for i in range(int(self.widget['quantity'].text())):	
			self.widget['beam'][i] = {}
			label = QtWidgets.QLabel(str('Beam %i'%(i+1)))
			self.widget['beam'][i]['calculate'] = QtWidgets.QPushButton('Calculate')
			self.widget['beam'][i]['align'] = QtWidgets.QPushButton('Align')
			# self.widget['beam'][i]['hline'] = HLine()
			self.widget['beam'][i]['interlock'] = QtWidgets.QCheckBox('Interlock')
			self.widget['beam'][i]['deliver'] = QtWidgets.QPushButton('Deliver')
			# Layout
			self.widget['deliveryGroup'].addRow(label)
			self.widget['deliveryGroup'].addRow(self.widget['beam'][i]['calculate'],self.widget['beam'][i]['align'])
			self.widget['deliveryGroup'].addRow(HLine())
			self.widget['deliveryGroup'].addRow(self.widget['beam'][i]['interlock'],self.widget['beam'][i]['deliver'])
			# Defaults
			self.widget['beam'][i]['alignmentComplete'] = False
			self.widget['beam'][i]['interlock'].setChecked(True)
			self.widget['beam'][i]['interlock'].setEnabled(False)
			self.widget['beam'][i]['deliver'].setEnabled(False)
			# Signals and Slots
			self.widget['beam'][i]['interlock'].stateChanged.connect(partial(self.treatmentInterlock,i))

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

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class sbSettings(QtCore.QObject):
	modeChanged = QtCore.pyqtSignal('QString')
	stageChanged = QtCore.pyqtSignal('QString')
	detectorChanged = QtCore.pyqtSignal('QString')

	def __init__(self,parent):
		super().__init__()
		self.parent = parent
		self.controls = {}
		self.hardware = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Controls Level
		controlsGroup = QtWidgets.QGroupBox()
		controlsGroup.setTitle('Control Complexity')
		self.controls['rbSimple'] = QtWidgets.QRadioButton('Simple')
		self.controls['rbNormal'] = QtWidgets.QRadioButton('Normal')
		self.controls['rbComplex'] = QtWidgets.QRadioButton('Complex')
		self.controls['cbReadOnly'] = QtWidgets.QCheckBox('Read Only')
		self.controls['complexity'] = 'simple'
		# Layout
		controlsGroupLayout = QtWidgets.QVBoxLayout()
		controlsGroupLayout.addWidget(self.controls['rbSimple'])
		controlsGroupLayout.addWidget(self.controls['rbNormal'])
		controlsGroupLayout.addWidget(self.controls['rbComplex'])
		controlsGroupLayout.addWidget(self.controls['cbReadOnly'])
		controlsGroup.setLayout(controlsGroupLayout)

		# Group 2: Hardware
		hardwareGroup = QtWidgets.QGroupBox()
		hardwareGroup.setTitle('Hardware Configuration')
		detectorLabel = QtWidgets.QLabel('Stage')
		self.hardware['stage'] = QtWidgets.QComboBox()
		stageLabel = QtWidgets.QLabel('Detector')
		self.hardware['detector'] = QtWidgets.QComboBox()
		# Layout
		hardwareGroupLayout = QtWidgets.QVBoxLayout()
		hardwareGroupLayout.addWidget(detectorLabel)
		hardwareGroupLayout.addWidget(self.hardware['stage'])
		hardwareGroupLayout.addWidget(stageLabel)
		hardwareGroupLayout.addWidget(self.hardware['detector'])
		hardwareGroup.setLayout(hardwareGroupLayout)

		# Defaults
		self.controls['rbSimple'].setChecked(True)
		self.controls['cbReadOnly'].setChecked(True)
		# Signals and Slots
		self.controls['rbSimple'].clicked.connect(self.controlsMode)
		self.controls['rbNormal'].clicked.connect(self.controlsMode)
		self.controls['rbComplex'].clicked.connect(self.controlsMode)
		self.hardware['stage'].currentIndexChanged.connect(self.stageChange)
		self.hardware['detector'].currentIndexChanged.connect(self.detectorChange)
		# Add Sections
		self.layout.addWidget(controlsGroup)
		self.layout.addWidget(hardwareGroup)
		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

	def controlsMode(self):
		''' Set complexity of controls. '''
		if self.controls['rbSimple'].isChecked():
			self.controls['complexity'] = 'simple'
		elif self.controls['rbNormal'].isChecked():
			self.controls['complexity'] = 'normal'
		elif self.controls['rbComplex'].isChecked():
			self.controls['complexity'] = 'complex'

		# Emit signal to say state has changed.
		self.modeChanged.emit(self.controls['complexity'])

	def loadStages(self,importList):
		'''Expects a dict of csv values.'''
		self.hardware['motorsList'] = set()
		for motor in importList:
			self.hardware['motorsList'].add(motor['Group'])

		for item in self.hardware['motorsList']:
			self.hardware['stage'].addItem(item)

		self.hardware['stage'].model().sort(0)

	def stageChange(self):
		self.stageChanged.emit(self.hardware['stage'].currentText())

	def loadDetectors(self,importList):
		'''Expects a dict of csv values.'''
		self.hardware['detectorList'] = set()
		for detector in importList:
			self.hardware['detectorList'].add(detector['Name'])

		for item in self.hardware['detectorList']:
			self.hardware['detector'].addItem(item)

		self.hardware['detector'].model().sort(0)

	def detectorChange(self):
		self.detectorChanged.emit(self.hardware['detector'].currentText())

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class sbXrayProperties:
	def __init__(self,parent):
		self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Alignment callibration.
		callibrationGroup = QtWidgets.QGroupBox()
		callibrationGroup.setTitle('Hardware Callibration')
		label1 = QtWidgets.QLabel('Beam Isocenter (pixels)')
		label2 = QtWidgets.QLabel('x: ')
		self.widget['alignIsocX'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('y: ')
		self.widget['alignIsocY'] = QtWidgets.QLineEdit()
		# Layout
		callibrationGroupLayout = QtWidgets.QFormLayout()
		callibrationGroupLayout.addRow(label1)
		callibrationGroupLayout.addRow(label2,self.widget['alignIsocX'])
		callibrationGroupLayout.addRow(label3,self.widget['alignIsocY'])
		# Defaults
		validator = QtGui.QDoubleValidator()
		validator.setBottom(0)
		validator.setDecimals(4)
		self.widget['alignIsocX'].setValidator(validator)
		self.widget['alignIsocY'].setValidator(validator)
		# Signals and Slots
		# Group inclusion to page
		callibrationGroup.setLayout(callibrationGroupLayout)
		self.layout.addWidget(callibrationGroup)

		# Group 2: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbBeamIsoc'] = QtWidgets.QCheckBox('Beam Isocenter')
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbBeamIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('X-ray Windowing')
		header = QtWidgets.QLabel('No. Windows:')
		self.window['numWindows'] = QtWidgets.QSpinBox()
		self.window['pbApply'] = QtWidgets.QPushButton('Apply')
		self.window['pbReset'] = QtWidgets.QPushButton('Reset')
		self.window['window'] = {}
		lower = QtWidgets.QLabel('Lower Limit') 
		upper = QtWidgets.QLabel('Upper Limit')
		self.window['window'][1] = XraySpinBox()
		self.window['window'][0] = XraySpinBox()
		# Layout
		self.window['layout'] = QtWidgets.QFormLayout()
		self.window['layout'].addRow(header,self.window['numWindows'])
		self.window['layout'].addRow(lower,upper)
		self.window['layout'].addRow(self.window['window'][0],self.window['window'][1])
		self.window['layout'].addRow(self.window['pbApply'],self.window['pbReset'])
		# Defaults
		self.window['numWindows'].setMinimum(1)
		self.window['numWindows'].setMaximum(10)
		self.window['numWindows'].setValue(1)
		self.window['numWindows'].setSingleStep(1)
		self.window['window'][1].setValue(65535)
		# Signals and Slots
		self.window['numWindows'].valueChanged.connect(self.addWindows)
		# Group inclusion to page
		windowGroup.setLayout(self.window['layout'])
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

	def addWindows(self):
		'''Add or remove windowing fields as required.'''
		difference = int(self.window['numWindows'].value() - len(self.window['window'])/2)

		# If number greater than, then add windows.
		if difference > 0:
			length = len(self.window['window'])
			for i in range(difference):
				# Add to dict, add to layout.
				self.window['window'][length+i*2] = XraySpinBox()
				self.window['window'][length+i*2+1] = XraySpinBox()
				self.window['window'][length+i*2+1].setValue(10000)
				self.window['layout'].insertRow(self.window['layout'].rowCount()-1,
					self.window['window'][length+i],self.window['window'][length+i*2+1])

		# If number less than, remove windows.
		if difference < 0:
			length = len(self.window['window'])
			for i in range(abs(difference)):
				# Remove from layout, remove from dict.
				self.window['window'][length-i*2-1].deleteLater()
				self.window['window'][length-i*2-2].deleteLater()
				del self.window['window'][length-i*2-1]
				del self.window['window'][length-i*2-2]

	def getWindows(self):
		'''Get window values as list of lists. Need scale slope and intercept.'''
		windows = []

		for i in range(int(len(self.window['window'])/2)):
			window = [self.window['window'][i*2].value(),self.window['window'][i*2+1].value()]
			windows.append(window)

		return windows

class sbCTProperties:
	def __init__(self,parent):
		self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Overlays.
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
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 2: Windowing
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
		header = QtWidgets.QLabel('No. Windows:')
		self.window['numWindows'] = QtWidgets.QSpinBox()
		self.window['rbMax'] = QtWidgets.QRadioButton('Max')
		self.window['rbSum'] = QtWidgets.QRadioButton('Sum')
		self.window['pbApply'] = QtWidgets.QPushButton('Apply')
		self.window['pbReset'] = QtWidgets.QPushButton('Reset')
		self.window['window'] = {}
		lower = QtWidgets.QLabel('Lower Limit') 
		upper = QtWidgets.QLabel('Upper Limit')
		self.window['window'][1] = HUSpinBox()
		self.window['window'][0] = HUSpinBox()
		# Layout
		self.window['layout'] = QtWidgets.QFormLayout()
		self.window['layout'].addRow(header,self.window['numWindows'])
		self.window['layout'].addRow(lower,upper)
		self.window['layout'].addRow(self.window['window'][0],self.window['window'][1])
		self.window['layout'].addRow(self.window['rbMax'],self.window['rbSum'])
		self.window['layout'].addRow(self.window['pbApply'],self.window['pbReset'])
		# Defaults
		self.window['numWindows'].setMinimum(1)
		self.window['numWindows'].setMaximum(10)
		self.window['numWindows'].setValue(1)
		self.window['numWindows'].setSingleStep(1)
		self.window['window'][1].setValue(5000)
		self.window['rbSum'].setChecked(True)
		# Signals and Slots
		self.window['numWindows'].valueChanged.connect(self.addWindows)
		# Group inclusion to page
		windowGroup.setLayout(self.window['layout'])
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

	def addWindows(self):
		'''Add or remove windowing fields as required.'''
		difference = int(self.window['numWindows'].value() - len(self.window['window'])/2)

		# If number greater than, then add windows.
		if difference > 0:
			length = len(self.window['window'])
			for i in range(difference):
				# Add to dict, add to layout.
				self.window['window'][length+i*2] = HUSpinBox()
				self.window['window'][length+i*2+1] = HUSpinBox()
				self.window['window'][length+i*2+1].setValue(5000)
				self.window['layout'].insertRow(self.window['layout'].rowCount()-2,
					self.window['window'][length+i],self.window['window'][length+i*2+1])

		# If number less than, remove windows.
		if difference < 0:
			length = len(self.window['window'])
			for i in range(abs(difference)):
				# Remove from layout, remove from dict.
				self.window['window'][length-i*2-1].deleteLater()
				self.window['window'][length-i*2-2].deleteLater()
				del self.window['window'][length-i*2-1]
				del self.window['window'][length-i*2-2]

	def getWindows(self,slope,intercept):
		'''Get window values as list of lists. Need scale slope and intercept.'''
		windows = []

		for i in range(int(len(self.window['window'])/2)):
			window = [self.window['window'][i*2].value()*slope-intercept,self.window['window'][i*2+1].value()*slope-intercept]
			windows.append(window)

		return windows

class HUSpinBox(QtWidgets.QSpinBox):
	'''CT HU windowing spinbox'''
	def __init__(self):
		super().__init__()
		self.setRange(-1000,5000)
		self.setSingleStep(100)
		self.setValue(-1000)

class XraySpinBox(QtWidgets.QSpinBox):
	'''Xray windowing spin box'''
	def __init__(self):
		super().__init__()
		self.setRange(0,65535)
		self.setSingleStep(5000)
		self.setValue(0)

class HLine(QtWidgets.QFrame):
	'''Horizontal line.'''
	def __init__(self):
		super().__init__()
		self.setFrameShape(QtWidgets.QFrame.HLine)
		self.setFrameShadow(QtWidgets.QFrame.Sunken)