from PyQt5 import QtWidgets, QtGui, QtCore, uic
from functools import partial

# class plotEnvironment():
from syncmrt import widgets
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

resourceFilepath = "resources/"


'''
TOOL PANEL
- class: toolSelector
- class: toolListWidget
'''

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

class sbAlignment:
	def __init__(self,parent):
		self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Markers
		markerGroup = QtWidgets.QGroupBox()
		markerGroup.setTitle('Marker Options')
		self.widget['anatomical'] = QtWidgets.QRadioButton('Anatomical')
		self.widget['fiducial'] = QtWidgets.QRadioButton('Fiducial')
		self.widget['optimise'] = QtWidgets.QCheckBox('Optimise')
		label1 = QtWidgets.QLabel('Number of Points:')
		self.widget['maxMarkers'] = QtWidgets.QSpinBox()
		label2 = QtWidgets.QLabel('Marker Size (mm):')
		self.widget['markerSize'] = QtWidgets.QDoubleSpinBox()
		# Layout
		markerGroupLayout = QtWidgets.QFormLayout()
		markerGroupLayout.addRow(self.widget['anatomical'])
		markerGroupLayout.addRow(self.widget['fiducial'])
		markerGroupLayout.addRow(self.widget['optimise'])
		markerGroupLayout.addRow(label1,self.widget['maxMarkers'])
		markerGroupLayout.addRow(label2,self.widget['markerSize'])
		markerGroup.setLayout(markerGroupLayout)
		self.layout.addWidget(markerGroup)
		# Default Positions
		self.widget['optimise'].setEnabled(False)
		self.widget['anatomical'].setChecked(True)
		self.widget['markerSize'].setEnabled(False)
		self.widget['markerSize'].setRange(0,5)
		self.widget['markerSize'].setSingleStep(0.25)
		self.widget['markerSize'].setValue(2.00)
		self.widget['maxMarkers'].setMinimum(1)
		# Signals and Slots
		self.widget['anatomical'].toggled.connect(self.markerMode)
		self.widget['fiducial'].toggled.connect(self.markerMode)
		self.widget['optimise'].toggled.connect(self.markerMode)

		# Group 2: Checklist
		checklistGroup = QtWidgets.QGroupBox()
		checklistGroup.setTitle('Checklist')
		self.widget['checkSetup'] = QtWidgets.QLabel('Alignment Setup')
		self.widget['checkXray'] = QtWidgets.QLabel('X-ray')
		self.widget['checkDicom'] = QtWidgets.QLabel('Dicom Image')
		self.widget['checkRTP'] = QtWidgets.QLabel('Treatment Plan')
		self.widget['check'] = QtWidgets.QPushButton('Check')
		self.widget['align'] = QtWidgets.QPushButton('Align')
		# Layout
		checklistGroupLayout = QtWidgets.QFormLayout()
		checklistGroupLayout.addRow(self.widget['checkSetup'])
		checklistGroupLayout.addRow(self.widget['checkXray'])
		checklistGroupLayout.addRow(self.widget['checkDicom'])
		checklistGroupLayout.addRow(self.widget['checkRTP'])
		checklistGroupLayout.addRow(self.widget['check'],self.widget['align'])
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

		# Enabling/toggling markerSize.
		if self.widget['optimise'].isChecked():
			self.widget['markerSize'].setEnabled(True)
		else:
			self.widget['markerSize'].setEnabled(False)

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

class sbSettings:
	def __init__(self,parent):
		self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 2: Alignment
		alignmentGroup = QtWidgets.QGroupBox()
		alignmentGroup.setTitle('Alignment')
		self.widget['findXrIsoc'] = QtWidgets.QPushButton('Find Xray Isocentre')
		label2 = QtWidgets.QLabel('Correct Patient')
		label3 = QtWidgets.QLabel('Alignment')
		label4 = QtWidgets.QLabel('Dosimetry')

		# Group 3: Dosimetry
		dosimetryGroup = QtWidgets.QGroupBox()
		dosimetryGroup.setTitle('Dosimetry')
		self.widget['check'] = QtWidgets.QPushButton('Check Treatment')
		self.widget['deliver'] = QtWidgets.QPushButton('Deliver Treatment')
		# Defaults
		# Signals and Slots

		# Add Sections

		# Finish page.
		self.layout.addStretch(1)
		self.parent.setLayout(self.layout)

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

		# Group 1: Windowing
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

		# Add Sections 
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

'''
PLOTTING
- class: workEnvironment
- class: plotEnvironment
- class: customNavigationToolbar
- class: plotTableModel
'''

class workEnvironment:
	'''Select the work environment out of the stacked widget via the toolbar buttons.'''
	def __init__(self,toolbar,stack):
		self.stack = stack
		self.stackPage = {}
		self.button = {}

		layout = QtWidgets.QHBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignLeft)
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)

		self.toolbarLayout = layout
		toolbar.setLayout(self.toolbarLayout)

	def addWorkspace(self,name):
		'''Add environments to work environment. Can be in form of list.'''
		if name in self.stackPage:
			# Do nothing if it already exists.
			return

		size = QtCore.QSize()
		size.setHeight(30)
		size.setWidth(75)

		if type(name) == list:
			# Enumerate list and add workspaces.
			for index, name in enumerate(name):
				button = QtWidgets.QToolButton()
				button.setText(name)
				button.setFixedSize(size)
				self.toolbarLayout.addWidget(button)
				self.button[name] = button

				page = QtWidgets.QWidget()
				self.stack.addWidget(page)
				self.stackPage[name] = page

				index = self.stack.indexOf(page)
				self.button[name].clicked.connect(partial(self.showWorkspace,index))
		else:
			# Assume singular workspace addition.
			button = QtWidgets.QToolButton()
			button.setText(name)
			button.setFixedSize(size)
			self.toolbarLayout.addWidget(button)
			self.button[name] = button

			page = QtWidgets.QWidget()
			self.stack.addWidget(page)
			self.stackPage[name] = page

			index = self.stack.indexOf(page)
			button.clicked.connect(partial(self.showWorkspace,index))

	def showWorkspace(self,index):
		self.stack.setCurrentIndex(index)

class plotEnvironment:
	'''
	All things plot. Navbars, plot canvas, table view/model (x2)
	'''
	def __init__(self,widget):
		self.layout = QtWidgets.QGridLayout(widget)
		self.model0 = plotTableModel()
		self.model90 = plotTableModel()
		self.plot0 = widgets.mpl2DFigure(self.model0)
		self.plot90 = widgets.mpl2DFigure(self.model90)
		self.nav0 = customNavigationToolbar(self.plot0.canvas,widget)
		self.nav90 = customNavigationToolbar(self.plot90.canvas,widget)

		self.table0 = QtWidgets.QTableView()
		self.table0.setAlternatingRowColors(True)
		self.table0.setModel(self.model0)
		self.table0.setColumnWidth(0,200)
		self.table0.verticalHeader().setDefaultSectionSize(20)
		self.table0.verticalHeader().hide()
		self.table0.horizontalHeader().setStretchLastSection(True)

		self.table90 = QtWidgets.QTableView()
		self.table90.setAlternatingRowColors(True)
		self.table90.setModel(self.model90)
		self.table90.setColumnWidth(0,200)
		self.table90.verticalHeader().setDefaultSectionSize(20)
		self.table90.verticalHeader().hide()
		self.table90.horizontalHeader().setStretchLastSection(True)

		self.layout.addWidget(self.nav0,0,0)
		self.layout.addWidget(self.plot0.canvas,1,0)
		self.layout.addWidget(self.table0,2,0)
		self.layout.addWidget(self.nav90,0,1)
		self.layout.addWidget(self.plot90.canvas,1,1)
		self.layout.addWidget(self.table90,2,1)

		self.nav0.actionClearMarkers.triggered.connect(partial(self.plot0.markerRemove,-1))
		self.nav0.actionPickMarkers.triggered.connect(self.nav0.pick)
		self.nav90.actionClearMarkers.triggered.connect(partial(self.plot90.markerRemove,-1))
		self.nav90.actionPickMarkers.triggered.connect(self.nav90.pick)

		# Enable point updating through editing table values.
		self.model0.itemChanged.connect(self.plot0.markerUpdate)
		self.model90.itemChanged.connect(self.plot90.markerUpdate)

		# Blank Qt cursor in figures.
		self.plot0.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
		self.plot90.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

	def setWindows(self,windows):
		'''Set windows for all plots. Take windows as list of lists with upper and lower limits per window [[upper,lower],].'''
		self.plot0.imageWindow(windows)
		self.plot90.imageWindow(windows)

	def setRadiographMode(self,mode):
		'''Set radiograph mode to 'sum' or 'max.''' 
		self.plot0._radiographMode = mode
		self.plot90._radiographMode = mode

	def settings(self,setting,value):
		if setting == 'maxMarkers':
			self.plot0.markerModel.setMarkerRows(value)
			self.plot90.markerModel.setMarkerRows(value)
			self.plot0.markersMaximum = value
			self.plot90.markersMaximum = value
		else:
			pass

class plotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they 
	are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(3)
		self.setMarkerRows(0)
		# self.markers = {}
		self.items = {}
		self._locked = False

		self.setHorizontalHeaderLabels(['#','x','y'])
		# Set column 0 editable(false)

	def addPoint(self,row,x,y):
		'''Write a point to the model. This is specified by the point number (identifier), and it's x and y coord.'''
		self._locked = True
		column0 = QtGui.QStandardItem()
		column0.setData('Marker '+str(row),QtCore.Qt.DisplayRole)
		column0.setEditable(False)

		column1 = QtGui.QStandardItem()
		column1.setData(float(x),QtCore.Qt.DisplayRole)

		column2 = QtGui.QStandardItem()
		column2.setData(float(y),QtCore.Qt.DisplayRole)

		self.items[row-1] = [column1, column2]
		# self.markers[row-1] = [x,y]

		data = [column0, column1, column2]

		for index, element in enumerate(data):
			self.setItem(row-1,index,element)

		self.layoutChanged.emit()
		self._locked = False

	def removePoint(self,index):
		'''Remove a specific point in the list.'''
		pass

	def setMarkerRows(self,rows):
		'''Defines the maximum number of rows according to the maximum number of markers.'''
		current = self.rowCount()
		difference = abs(current-rows)

		if rows < current:
			self.removeRows(current-1-difference, difference)
		elif rows > current:
			self.insertRows(current,difference)
		else:
			pass

		self.layoutChanged.emit()

	def clearMarkers(self,newRows):
		'''Clear the model of all it's rows and re-add empty rows in their place.'''
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(newRows)

class customNavigationToolbar(NavigationToolbar2QT):
	def __init__(self,canvas,parent):
		NavigationToolbar2QT.__init__(self,canvas,parent)
		self.canvas = canvas

		actions = self.findChildren(QtWidgets.QAction)
		toolsBlacklist = ['Customize','Forward','Back','Subplots','Save']
		for a in actions:
			if a.text() in toolsBlacklist:
				self.removeAction(a)

		# Remove the labels (x,y,val).
		self.locLabel.deleteLater()

		self.actionPickMarkers = self.addAction('Pick')
		self.actionClearMarkers = self.addAction('Clear')
		self.actionImageSettings = self.addAction('Image Settings')
		self.insertSeparator(self.actionImageSettings)
		self.actionPickMarkers.setCheckable(True)

		# Pick should disable when ZOOM or PAN is enabled.

	def set_message(self, s):
		# Set empty message method to stop it from trying to use self.locLabel
		pass 

	def pick(self):
		if self._active == 'PICK':
			self._active = None
		else:
			self._active = 'PICK'

		if self._idPress is not None:
			self._idPress = self.canvas.mpl_disconnect(self._idPress)
			self.mode = ''

		if self._active:
			self.canvas._pickerActive = True
			self._idPress = self.canvas.mpl_connect(
				'button_press_event', self.press_pick)
			self.canvas.widgetlock(self)
		else:
			self.canvas.widgetlock.release(self)
			self.canvas._pickerActive = False

	def press_pick(self, event):
		"""the press mouse button in pick mode callback"""

		if event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return

		self.press(event)
		self.release(event)

'''
PROPERTY MANAGER
- class: propertyManager (QTreeView)
- class: propertyModel (QStandardItemModel)
'''

class propertyManager(QtWidgets.QTreeView):
	'''
	Property manager that stores variable/name for all variables. 
	This is a tree view, the model comes from propertyModel.
	'''
	def __init__(self,frame,model):
		'''Send the frame location to sit the tree in along with the model to populate the tree with.'''
		super().__init__()
		# self.setHeaderLabel('Property Editor')
		self.setMinimumSize(250,800)
		self.setMaximumWidth(500)
		# self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setRootIsDecorated(True)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setModel(model)

		# Set layout and add propertyManager as widget to frame layout.
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		frame.setLayout(layout)

class propertyModel(QtGui.QStandardItemModel):
	'''
	Categories (such as Xray/CT/RtPlan) will be parents of their variables.
	Children will be attached with sub children for broken down variables.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(2)
		self.setRowCount(0)
		self.setHorizontalHeaderLabels(['Property','Value'])
		# Section holds Root (top level) items. Index holds index of all sub-items.
		self.section = {}
		# index[name][variable][sub-variable] returns QModelIndex.
		self.index = {}

	def addSection(self,name):
		'''Add new section to model. Model section introduces list of all items inside.'''
		item = QtGui.QStandardItem()
		item.setData(name,QtCore.Qt.DisplayRole)
		self.appendRow(item)
		self.section[name] = item

		# have a custom delegate for styling...
		self.index[name] = {}
		self.index[name]['root'] = self.indexFromItem(item)

	def addVariable(self,name,variable,value):
		'''Takes single and multiple variables, adds to parent item (name).'''
		if type(variable) is list:
			# Multiple Entry
			prop = QtGui.QStandardItem()
			prop.setData(variable[0],QtCore.Qt.DisplayRole)
			prop.setEditable(False)

			descr = QtGui.QStandardItem()
			descr.setEditable(False)

			self.section[name].appendRow([prop,descr])
			self.index[name][variable[0]] = {}
			self.index[name][variable[0]][0] = self.indexFromItem(descr)

			string = ''

			for i in range(len(value)):
				var = QtGui.QStandardItem()
				var.setData(variable[i+1],QtCore.Qt.DisplayRole)
				var.setEditable(False)

				val = QtGui.QStandardItem()
				val.setData(value[i],QtCore.Qt.DisplayRole)
				val.setEditable(True)

				prop.appendRow([var,val])

				string += str(value[i])+','

				self.index[name][variable[0]][variable[i+1]] = self.indexFromItem(val)

			string = string[:-1]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemVariable = QtGui.QStandardItem()
			itemVariable.setData(variable,QtCore.Qt.DisplayRole)
			itemVariable.setEditable(False)

			itemValue = QtGui.QStandardItem()
			itemValue.setData(value,QtCore.Qt.DisplayRole)
			itemValue.setEditable(True)

			self.section[name].appendRow([itemVariable,itemValue])
			self.index[name][variable] = self.indexFromItem(itemValue)

	def updateVariable(self,name,variable,value):
		'''Find variable and update value.'''

		if type(variable) is list:
			# Multiple Entry
			descr = self.itemFromIndex(self.index[name][variable[0]][0])

			# item description
			string = ''

			for i in range(len(value)):
				val = self.itemFromIndex(self.index[name][variable[0]][variable[i+1]])
				val.setData(value[i],QtCore.Qt.DisplayRole)

				string += str(value[i])+','

			string = string[:-1]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemValue = self.itemFromIndex(self.index[name][variable])
			itemValue.setData(value,QtCore.Qt.DisplayRole)

class variablePane:
	'''
	Create variable viewing pane based of a tree widget. You will have collapsible tables to view your information in.
	'''
	def __init__(self,tree):
		'''Main tree Widget settings (sits within frame).'''
		tree.setHeaderLabel('Property Editor')
		tree.setMinimumSize(250,800)
		tree.setMaximumWidth(500)
		tree.setIndentation(0)
		tree.setRootIsDecorated(True)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		tree.setSizePolicy(sizePolicy)

	def addTable(self,tree,name,model):
		'''Add a table of data based of variableModel() class.'''
		category = QtWidgets.QTreeWidgetItem()
		category.setFirstColumnSpanned(True)
		category.setText(0,name)

		child = QtWidgets.QTreeWidgetItem()

		view = QtWidgets.QTreeView()
		view.setModel(model)
		view.setAlternatingRowColors(True)
		view.setMinimumSize(250,0)
		view.setMaximumWidth(500)
		tree.setRootIsDecorated(True)
		view.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		# verticalHeader = QtWidgets.QHeaderView(QtCore.Qt.Vertical)
		# verticalHeader.setDefaultSectionSize(20)
		# view.setVerticalHeader(verticalHeader)
		# view.verticalHeader().hide()

		category.addChild(child)
		tree.addTopLevelItem(category)
		tree.setItemWidget(child,0,view)
		tree.expandItem(category)

class variableModel(QtGui.QStandardItemModel):
	'''
	A model class based of a standard item model that enables you to add single and multiple data points.
	This is used in conjunction with a viewer in the GUI to display the model data.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(2)
		self.setRowCount(0)
		self.setHorizontalHeaderLabels(['Property','Value'])

	def addTableRow(self,variable,value):
		'''Add a table row of data with a label (static) and the value (editable).'''
		# Rows are appended to the end of the table.
		column1 = QtGui.QStandardItem()
		column1.setData(variable,QtCore.Qt.DisplayRole)
		column1.setEditable(False)

		column2 = QtGui.QStandardItem()
		column2.setData(value,QtCore.Qt.DisplayRole)
		column2.setEditable(True)

		self.appendRow([column1, column2])

	def addMultiVariable(self,variable,value):
		'''Add multiple variables to the model, the Variable/Value should be a list of vars.'''
		# Variable should have 1 more entry than value.
		prop = QtGui.QStandardItem()
		prop.setData(variable[0],QtCore.Qt.DisplayRole)
		prop.setEditable(False)

		descr = QtGui.QStandardItem()
		descr.setEditable(False)

		self.appendRow([prop,descr])

		string =''

		for i in range(len(value)):
			var = QtGui.QStandardItem()
			var.setData(variable[i+1],QtCore.Qt.DisplayRole)
			var.setEditable(False)

			val = QtGui.QStandardItem()
			val.setData(value[i],QtCore.Qt.DisplayRole)
			val.setEditable(True)

			prop.appendRow([var,val])

			string += str(value[i])+','

		string = string[:-1]
		descr.setData(string,QtCore.Qt.DisplayRole)

'''
LOGFILES
- class logFile(): Keep a logfile in a class. Execute as self.logFile = logFile().
- method log(logwindow, message, rank): Print logs in the application. Called from the application window.
- class: logFile
- meth: log
'''

class logFile:
	def __init__(self):
		self.message = ()
		self.rank = ()

	def addLog(self,message,rank):
		self.message.append(message)
		self.rank.append(rank)

	def resetLog():
		self.message = ()
		self.rank = ()

def log(window,message,rank):
	if rank == 'error':
		window.setTextColor(QtCore.Qt.red)
		window.setFontWeight(QtGui.QFont.Medium)
		window.append(message)
	elif rank == 'warning':
		window.setTextColor(QtCore.Qt.red)
		window.append(message)
	elif rank == 'event':
		window.setTextColor(QtCore.Qt.black)
		window.append(message)
	else:
		window.setTextColor(QtCore.Qt.gray)
		window.append(message)

'''
WIDGET TOGGLES
- meth: widgetToggle
'''
def widgetToggle(widget):
	'''Set state to opposite of current visibility state.'''
	state = widget.isVisible()
	widget.setVisible(not state)