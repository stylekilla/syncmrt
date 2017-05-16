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
class toolSelector:
	'''
	Combo of list and stackedwidget for having a toggle-able tool frame.
	'''
	def __init__(self,listFrame,stack):
		self.toolList = toolListWidget(listFrame)
		self.stack = stack
		self.stackPage = {}
		self.index = 0
		self.stack.setVisible(False)
		self._previousItem = False

		# Connects selection to stacked widget page.
		self.toolList.currentItemChanged.connect(self.previousTool)
		self.toolList.itemPressed.connect(self.showTool)

	# def insertTool(self,name,index-after-before?)

	def addTool(self,name):
		'''Add tool and increase index by 1.'''
		self.toolList.addCategory(name,self.index)
		page = QtWidgets.QWidget()
		self.stackPage[name] = page
		self.populateCategory(name)
		self.stack.addWidget(page)

		self.index += 1
		self._previousItem = self.toolList.item(self.index)

	def previousTool(self,current,previous):
		self._previousItem = previous

	def showTool(self,item):
		'''Change workspace based on item clicked. If the same one is clicked then toggle the view on/off.'''
		# if not self._previousItem:
		# 	self._previousItem = item

		if self.toolList.currentItem() == self._previousItem:
			self.stack.setVisible(not self.stack.isVisible())
		else:
			self.stack.setVisible(True)
			index = self.toolList.row(item)
			self.stack.setCurrentIndex(index)
			self._previousItem = item

	def showToolExternalTrigger(self,item):
		'''Allow for external triggering for displaying tool panes.'''
		self.toolList.setCurrentItem(item)
		self.showTool(item)

	def hideTool(self,name):
		pass

	def removeTool(self,name):
		pass

	def populateCategory(self,name):
		'''Populate each category with a dictionary of tools.'''
		if name == 'Alignment':
			self.alignment = {}
			page = self.stackPage[name]
			layout = QtWidgets.QVBoxLayout()

			# Group 1: Markers
			markerGroup = QtWidgets.QGroupBox()
			markerGroup.setTitle('Marker Options')
			self.alignment['anatomical'] = QtWidgets.QRadioButton('Anatomical')
			self.alignment['fiducial'] = QtWidgets.QRadioButton('Fiducial')
			self.alignment['optimise'] = QtWidgets.QCheckBox('Optimise')
			label1 = QtWidgets.QLabel('Number of Points:')
			self.alignment['maxMarkers'] = QtWidgets.QSpinBox()
			label2 = QtWidgets.QLabel('Marker Size (mm):')
			self.alignment['markerSize'] = QtWidgets.QDoubleSpinBox()
			# Layout
			markerGroupLayout = QtWidgets.QFormLayout()
			markerGroupLayout.addRow(self.alignment['anatomical'])
			markerGroupLayout.addRow(self.alignment['fiducial'])
			markerGroupLayout.addRow(self.alignment['optimise'])
			markerGroupLayout.addRow(label1,self.alignment['maxMarkers'])
			markerGroupLayout.addRow(label2,self.alignment['markerSize'])
			markerGroup.setLayout(markerGroupLayout)
			layout.addWidget(markerGroup)
			# Default Positions
			self.alignment['optimise'].setEnabled(False)
			self.alignment['anatomical'].setChecked(True)
			self.alignment['markerSize'].setEnabled(False)
			self.alignment['markerSize'].setRange(0,5)
			self.alignment['markerSize'].setSingleStep(0.25)
			self.alignment['markerSize'].setValue(2.00)
			self.alignment['maxMarkers'].setMinimum(1)
			# Signals and Slots
			self.alignment['anatomical'].toggled.connect(self.markerMode)
			self.alignment['fiducial'].toggled.connect(self.markerMode)
			self.alignment['optimise'].toggled.connect(self.markerMode)

			# Group 2: Checklist
			checklistGroup = QtWidgets.QGroupBox()
			checklistGroup.setTitle('Checklist')
			self.alignment['checkSetup'] = QtWidgets.QLabel('Alignment Setup')
			self.alignment['checkXray'] = QtWidgets.QLabel('X-ray')
			self.alignment['checkDicom'] = QtWidgets.QLabel('Dicom Image')
			self.alignment['checkRTP'] = QtWidgets.QLabel('Treatment Plan')
			self.alignment['check'] = QtWidgets.QPushButton('Check')
			self.alignment['align'] = QtWidgets.QPushButton('Align')
			# Layout
			checklistGroupLayout = QtWidgets.QFormLayout()
			checklistGroupLayout.addRow(self.alignment['checkSetup'])
			checklistGroupLayout.addRow(self.alignment['checkXray'])
			checklistGroupLayout.addRow(self.alignment['checkDicom'])
			checklistGroupLayout.addRow(self.alignment['checkRTP'])
			checklistGroupLayout.addRow(self.alignment['check'],self.alignment['align'])
			checklistGroup.setLayout(checklistGroupLayout)
			layout.addWidget(checklistGroup)
			# Defaults
			# Signals and Slots

			# Finish page.
			layout.addStretch(1)
			page.setLayout(layout)

		elif name == 'Treatment':
			self.treatment = {}
			page = self.stackPage[name]
			layout = QtWidgets.QVBoxLayout()

			# Group 1: Treatment Settings
			settingsGroup = QtWidgets.QGroupBox()
			settingsGroup.setTitle('Description')
			label1 = QtWidgets.QLabel('Number of beams: ')
			self.treatment['quantity'] = QtWidgets.QLabel()
			# Layout
			settingsGroupLayout = QtWidgets.QFormLayout()
			settingsGroupLayout.addRow(label1,self.treatment['quantity'])
			settingsGroup.setLayout(settingsGroupLayout)
			layout.addWidget(settingsGroup)
			# Defaults
			self.treatment['quantity'].setText(str(0))
			# Signals and Slots

			# Group 2: Deliver Treatment
			# Dict for beam plan group widgets.
			self.treatment['beam'] = {}
			group = QtWidgets.QGroupBox()
			group.setTitle('Deliver Treatment')
			# Empty Layout
			self.treatment['deliveryGroup'] = QtWidgets.QFormLayout()
			self.treatment['noTreatment'] = QtWidgets.QLabel('No Treatment Plan loaded.')
			self.treatment['deliveryGroup'].addRow(self.treatment['noTreatment'])
			group.setLayout(self.treatment['deliveryGroup'])
			layout.addWidget(group)
			# Defaults
			# Signals and Slots

			# Finish page.
			layout.addStretch(1)
			page.setLayout(layout)

		elif name == 'Setup':
			self.setup = {}
			page = self.stackPage[name]
			layout = QtWidgets.QVBoxLayout()

			# Group 1: Alignment callibration.
			callibrationGroup = QtWidgets.QGroupBox()
			callibrationGroup.setTitle('Alignment Callibration')
			label1 = QtWidgets.QLabel('Alignment Isocenter (pixels)')
			label2 = QtWidgets.QLabel('x: ')
			self.setup['alignIsocX'] = QtWidgets.QLineEdit()
			label3 = QtWidgets.QLabel('y: ')
			self.setup['alignIsocY'] = QtWidgets.QLineEdit()
			# Layout
			callibrationGroupLayout = QtWidgets.QFormLayout()
			callibrationGroupLayout.addRow(label1)
			callibrationGroupLayout.addRow(label2,self.setup['alignIsocX'])
			callibrationGroupLayout.addRow(label3,self.setup['alignIsocY'])
			# Defaults
			validator = QtGui.QDoubleValidator()
			validator.setBottom(0)
			validator.setDecimals(4)
			self.setup['alignIsocX'].setValidator(validator)
			self.setup['alignIsocY'].setValidator(validator)
			# Signals and Slots

			# Group 2: Alignment
			alignmentGroup = QtWidgets.QGroupBox()
			alignmentGroup.setTitle('Alignment')
			self.setup['findXrIsoc'] = QtWidgets.QPushButton('Find Xray Isocentre')
			label2 = QtWidgets.QLabel('Correct Patient')
			label3 = QtWidgets.QLabel('Alignment')
			label4 = QtWidgets.QLabel('Dosimetry')

			# Group 3: Dosimetry
			dosimetryGroup = QtWidgets.QGroupBox()
			dosimetryGroup.setTitle('Dosimetry')
			self.treatment['check'] = QtWidgets.QPushButton('Check Treatment')
			self.treatment['deliver'] = QtWidgets.QPushButton('Deliver Treatment')
			# Defaults
			# Signals and Slots

			# Add Sections
			callibrationGroup.setLayout(callibrationGroupLayout)
			layout.addWidget(callibrationGroup)
			# Finish page.
			layout.addStretch(1)
			page.setLayout(layout)

		elif name == 'ImageProperties':
			self.ctWindow = {}
			self.xrayWindow = {}
			page = self.stackPage[name]
			layout = QtWidgets.QVBoxLayout()

			# Group 1: HU Window
			ctWindowGroup = QtWidgets.QGroupBox()
			ctWindowGroup.setTitle('Hounsfield Unit Windowing')
			header = QtWidgets.QLabel('No. Windows:')
			self.ctWindow['numWindows'] = QtWidgets.QSpinBox()
			self.ctWindow['rbMax'] = QtWidgets.QRadioButton('Max')
			self.ctWindow['rbSum'] = QtWidgets.QRadioButton('Sum')
			self.ctWindow['pbApply'] = QtWidgets.QPushButton('Apply')
			self.ctWindow['pbReset'] = QtWidgets.QPushButton('Reset')
			self.ctWindow['window'] = {}
			lower = QtWidgets.QLabel('Lower HU') 
			upper = QtWidgets.QLabel('Upper HU')
			self.ctWindow['window'][0] = HUSpinBox()
			self.ctWindow['window'][1] = HUSpinBox()
			# Layout
			self.ctWindow['layout'] = QtWidgets.QFormLayout()
			self.ctWindow['layout'].addRow(header,self.ctWindow['numWindows'])
			self.ctWindow['layout'].addRow(lower,upper)
			self.ctWindow['layout'].addRow(self.ctWindow['window'][0],self.ctWindow['window'][1])
			self.ctWindow['layout'].addRow(self.ctWindow['rbMax'],self.ctWindow['rbSum'])
			self.ctWindow['layout'].addRow(self.ctWindow['pbApply'],self.ctWindow['pbReset'])
			# Defaults
			self.ctWindow['numWindows'].setMinimum(1)
			self.ctWindow['numWindows'].setMaximum(10)
			self.ctWindow['numWindows'].setValue(1)
			self.ctWindow['numWindows'].setSingleStep(1)
			self.ctWindow['window'][1].setValue(5000)
			self.ctWindow['rbSum'].setChecked(True)
			# Signals and Slots
			self.ctWindow['numWindows'].valueChanged.connect(self.addCTWindows)

			# Group 2: X-ray Window
			xrayWindowGroup = QtWidgets.QGroupBox()
			xrayWindowGroup.setTitle('X-ray Windowing')
			header = QtWidgets.QLabel('No. Windows:')
			self.xrayWindow['numWindows'] = QtWidgets.QSpinBox()
			self.xrayWindow['pbApply'] = QtWidgets.QPushButton('Apply')
			self.xrayWindow['pbReset'] = QtWidgets.QPushButton('Reset')
			self.xrayWindow['window'] = {}
			lower = QtWidgets.QLabel('Lower Limit') 
			upper = QtWidgets.QLabel('Upper Limit')
			self.xrayWindow['window'][1] = XraySpinBox()
			self.xrayWindow['window'][0] = XraySpinBox()
			# Layout
			self.xrayWindow['layout'] = QtWidgets.QFormLayout()
			self.xrayWindow['layout'].addRow(header,self.xrayWindow['numWindows'])
			self.xrayWindow['layout'].addRow(lower,upper)
			self.xrayWindow['layout'].addRow(self.xrayWindow['window'][0],self.xrayWindow['window'][1])
			self.xrayWindow['layout'].addRow(self.xrayWindow['pbApply'],self.xrayWindow['pbReset'])
			# Defaults
			self.xrayWindow['numWindows'].setMinimum(1)
			self.xrayWindow['numWindows'].setMaximum(10)
			self.xrayWindow['numWindows'].setValue(1)
			self.xrayWindow['numWindows'].setSingleStep(1)
			self.xrayWindow['window'][1].setValue(10000)
			# Signals and Slots
			self.xrayWindow['numWindows'].valueChanged.connect(self.addXrayWindows)

			# Add Sections
			ctWindowGroup.setLayout(self.ctWindow['layout'])
			layout.addWidget(ctWindowGroup)
			xrayWindowGroup.setLayout(self.xrayWindow['layout'])
			layout.addWidget(xrayWindowGroup)
			# Finish page.
			layout.addStretch(1)
			page.setLayout(layout)

	def markerMode(self):
		'''If fiducial markers are chosen then enable optimisation checkbox and sizing.'''
		# Enabling/toggling optimise.
		if self.alignment['fiducial'].isChecked():
			self.alignment['optimise'].setEnabled(True)
		else:
			self.alignment['optimise'].setEnabled(False)
			self.alignment['optimise'].setChecked(False)
			self.alignment['markerSize'].setEnabled(False)
		# Enabling/toggling markerSize.
		if self.alignment['optimise'].isChecked():
			self.alignment['markerSize'].setEnabled(True)
		else:
			self.alignment['markerSize'].setEnabled(False)

	def treatmentInterlock(self,index):
		'''Treatment interlock stops treatment from occuring. Requires alignment to be done first.'''
		# Enable interlock button.
		if self.treatment['beam'][index]['alignmentComplete'] == True:
			self.treatment['beam'][index]['interlock'].setEnabled(True)

		# Enable treatment delivery button.
		if self.treatment['beam'][index]['interlock'].isChecked():
			self.treatment['beam'][index]['deliver'].setEnabled(False)
		else:
			self.treatment['beam'][index]['deliver'].setEnabled(True)

	def populateTreatments(self):
		'''Once treatment plan is loaded, add the treatments to the workflow.'''
		self.treatment['noTreatment'].deleteLater()
		del self.treatment['noTreatment']

		for i in range(int(self.treatment['quantity'].text())):	
			self.treatment['beam'][i] = {}
			label = QtWidgets.QLabel(str('Beam %i'%(i+1)))
			self.treatment['beam'][i]['calculate'] = QtWidgets.QPushButton('Calculate')
			self.treatment['beam'][i]['align'] = QtWidgets.QPushButton('Align')
			# self.treatment['beam'][i]['hline'] = HLine()
			self.treatment['beam'][i]['interlock'] = QtWidgets.QCheckBox('Interlock')
			self.treatment['beam'][i]['deliver'] = QtWidgets.QPushButton('Deliver')
			# Layout
			self.treatment['deliveryGroup'].addRow(label)
			self.treatment['deliveryGroup'].addRow(self.treatment['beam'][i]['calculate'],self.treatment['beam'][i]['align'])
			self.treatment['deliveryGroup'].addRow(HLine())
			self.treatment['deliveryGroup'].addRow(self.treatment['beam'][i]['interlock'],self.treatment['beam'][i]['deliver'])
			# Defaults
			self.treatment['beam'][i]['alignmentComplete'] = False
			self.treatment['beam'][i]['interlock'].setChecked(True)
			self.treatment['beam'][i]['interlock'].setEnabled(False)
			self.treatment['beam'][i]['deliver'].setEnabled(False)
			# Signals and Slots
			self.treatment['beam'][i]['interlock'].stateChanged.connect(partial(self.treatmentInterlock,i))

	def addCTWindows(self):
		'''Add or remove windowing fields as required.'''
		difference = int(self.ctWindow['numWindows'].value() - len(self.ctWindow['window'])/2)

		# If number greater than, then add windows.
		if difference > 0:
			length = len(self.ctWindow['window'])
			for i in range(difference):
				# Add to dict, add to layout.
				self.ctWindow['window'][length+i*2] = HUSpinBox()
				self.ctWindow['window'][length+i*2+1] = HUSpinBox()
				self.ctWindow['window'][length+i*2+1].setValue(5000)
				self.ctWindow['layout'].insertRow(self.ctWindow['layout'].rowCount()-2,
					self.ctWindow['window'][length+i],self.ctWindow['window'][length+i*2+1])

		# If number less than, remove windows.
		if difference < 0:
			length = len(self.ctWindow['window'])
			for i in range(abs(difference)):
				# Remove from layout, remove from dict.
				self.ctWindow['window'][length-i*2-1].deleteLater()
				self.ctWindow['window'][length-i*2-2].deleteLater()
				del self.ctWindow['window'][length-i*2-1]
				del self.ctWindow['window'][length-i*2-2]

	def addXrayWindows(self):
		'''Add or remove windowing fields as required.'''
		difference = int(self.xrayWindow['numWindows'].value() - len(self.xrayWindow['window'])/2)

		# If number greater than, then add windows.
		if difference > 0:
			length = len(self.xrayWindow['window'])
			for i in range(difference):
				# Add to dict, add to layout.
				self.xrayWindow['window'][length+i*2] = XraySpinBox()
				self.xrayWindow['window'][length+i*2+1] = XraySpinBox()
				self.xrayWindow['window'][length+i*2+1].setValue(10000)
				self.xrayWindow['layout'].insertRow(self.xrayWindow['layout'].rowCount()-1,
					self.xrayWindow['window'][length+i],self.xrayWindow['window'][length+i*2+1])

		# If number less than, remove windows.
		if difference < 0:
			length = len(self.xrayWindow['window'])
			for i in range(abs(difference)):
				# Remove from layout, remove from dict.
				self.xrayWindow['window'][length-i*2-1].deleteLater()
				self.xrayWindow['window'][length-i*2-2].deleteLater()
				del self.xrayWindow['window'][length-i*2-1]
				del self.xrayWindow['window'][length-i*2-2]

	def getCTWindows(self,slope,intercept):
		'''Get window values as list of lists. Need scale slope and intercept.'''
		windows = []

		for i in range(int(len(self.ctWindow['window'])/2)):
			window = [self.ctWindow['window'][i*2].value()*slope-intercept,self.ctWindow['window'][i*2+1].value()*slope-intercept]
			windows.append(window)

		return windows

	def getXrayWindows(self):
		'''Get window values as list of lists. Need scale slope and intercept.'''
		windows = []

		for i in range(int(len(self.xrayWindow['window'])/2)):
			window = [self.xrayWindow['window'][i*2].value(),self.xrayWindow['window'][i*2+1].value()]
			windows.append(window)

		return windows

class toolListWidget(QtWidgets.QListWidget):
	'''
	Tool list widget for selecting pages in stacked widget. Add items as necessary.
	'''
	def __init__(self,parent):
		super().__init__(parent)
		self.setMinimumHeight(800)
		self.setFixedWidth(60)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setIconSize(QtCore.QSize(50,50))

	def addCategory(self,name,index):
		item = QtWidgets.QListWidgetItem()
		item.setText(name)
		icon = QtGui.QIcon(resourceFilepath+name+'.png')
		icon.pixmap(50,50)
		item.setIcon(icon)
		item.setSizeHint(QtCore.QSize(60,60))

		self.insertItem(index,item)


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
		self.setRange(0,10000)
		self.setSingleStep(100)
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
				button.clicked.connect(partial(self.showWorkspace,index))
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
		super().__init__(frame)
		# self.setHeaderLabel('Property Editor')
		self.setMinimumSize(250,800)
		self.setMaximumWidth(500)
		# self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setRootIsDecorated(True)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setModel(model)

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