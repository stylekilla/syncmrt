# Program imports
import config
import workspace
import menubar
from sidebar import Sidebar
from synctools import QsWidgets

# Sitepackages
import os
import sys
from functools import partial
import numpy as np
# Pyqt5
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtGui, QtWidgets, uic
# SyncMRT Tools.
import synctools as mrt

# For PyInstaller:
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Select Qt5 user interface.
qtCreatorFile = application_path+"/resources/main.ui"
qtStyleSheet = open(application_path+"/resources/stylesheet.css")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

import logging, coloredlogs
coloredlogs.install(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',datefmt='%H:%M:%S',level=logging.DEBUG)

# Debug levels: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
# logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    # datefmt='%H:%M:%S',
    # datefmt='%Y-%m-%d:%H:%M:%S',
    # )

"""
MAIN CLASS
- def openFiles(self, modality): Imports files, gathers variables and plots. 
"""

class main(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		# Inititate UI.
		QtWidgets.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setStyleSheet(qtStyleSheet.read())
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		"""
		Qt5 Setup
		"""
		# Menu bar.
		self._menuBar = menubar.populate(self.menuBar())
		# Layout margins.
		self.layoutCentralWidget.setContentsMargins(0,0,0,0)
		self.statusBar.setContentsMargins(0,0,0,0)
		self.layoutSidebar.setContentsMargins(0,0,0,0)
		self.layoutWorkspace.setContentsMargins(0,0,0,0)

		# Sidebar panel.
		self.sidebar = Sidebar(self.frameSidebarStack,self.frameSidebarList)
		# Sidebar: Alignment.
		self.sbAlignment = self.sidebar.addPage('Alignment',QsWidgets.QAlignment(),before='all')
		self.sbAlignment.widget['maxMarkers'].setValue(3)
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		# self.sbAlignment.widget['calcAlignment'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=-1))
		# self.sbAlignment.widget['doAlignment'].clicked.connect(partial(self.patientApplyAlignment,treatmentIndex=-1))
		# self.sbAlignment.widget['optimise'].toggled.connect(partial(self.toggleOptimise))
		# Sidebar: Imaging
		self.sidebar.addPage('Imaging',QsWidgets.QImaging(),after='Alignment')
		self.sbImaging = self.sidebar.getPage('Imaging')
		# Add image properties section to sidebar.
		self.sidebar.addPage('ImageProperties',None,after='Imaging')
		# Add treatment section to sidebar.
		self.sidebar.addPage('Treatment',QsWidgets.QTreatment(),after='ImageProperties')
		self.sbTreatment = self.sidebar.getPage('Treatment')
		# Add settings section to sidebar.
		self.sidebar.addPage('Settings',QsWidgets.QSettings(),after='all')
		self.sbSettings = self.sidebar.getPage('Settings')

		# Create work environment
		self.environment = workspace.environment(self.toolbarPane,self.workStack)
		self.environment.workspaceChanged.connect(partial(self.sidebar.linkPages,'ImageProperties'))

		# PropertyManager
		self.property = workspace.propertyModel()
		self.propertyTree = workspace.propertyManager(self.frameVariablePane,self.property)

		# Collapsing button for Property Manager.
		icon = QtGui.QIcon(application_path+'/resources/CollapseRight.png')
		icon.pixmap(20,20)
		self.pbCollapseProperties = QtWidgets.QPushButton(icon,'')
		self.pbCollapseProperties.setFlat(True)
		self.statusBar.addPermanentWidget(self.pbCollapseProperties)
		self.pbCollapseProperties.clicked.connect(partial(self.propertyTree.toggleFrame,self.frameVariablePane))

		# Create alignment table.
		self.property.addSection('Alignment')
		self.property.addVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment',['Translation','H1','H2','V'],[0,0,0])
		self.property.addVariable('Alignment','Scale',0)
		self.propertyTree.expandAll()

		# Connect menubar items.
		self._menuBar['new_xray'].triggered.connect(partial(self.newFile,'xray'))
		self._menuBar['load_xray'].triggered.connect(partial(self.openFiles,'xray'))
		self._menuBar['load_ct'].triggered.connect(partial(self.openFiles,'ct'))
		self._menuBar['load_rtplan'].triggered.connect(partial(self.openFiles,'rtp'))
		self._menuBar['load_folder'].triggered.connect(partial(self.openFiles,'folder'))

		# Switches.
		self._isXrayOpen = False
		self._isCTOpen = False
		self._isMRIOpen = False
		self._isRTPOpen = False

		# TESTING MENU
		self.menuTESTING.triggered.connect(self.testing)

		"""
		SyncMRT Setup
		"""
		# Create a new system, this has a solver, detector and stage.
		self.system = mrt.system(application_path+config.files.patientSupports,application_path+config.files.detectors,config)		# Create a new patient, this has room for medical scans and synchrotron scans + other data.
		self.patient = mrt.patient()
		# Link the system with the patient data.
		self.system.loadPatient(self.patient)

		"""
		More GUI linking from System and Patient.
		"""
		# Create controls work environment.
		# self.environment.addPage('Controls',alignment='Right')
		# self.controls = mrt.widgets.controls.controlsPage(parent=self.environment.stackPage['Controls'])
		self.sbSettings.modeChanged.connect(self.setControlsComplexity)
		self.sbSettings.stageChanged.connect(self.system.setStage)
		self.sbSettings.refreshConnections.connect(self.system.patientSupport.reconnect)
		self.sbSettings.refreshConnections.connect(self.system.imager.reconnect)
		self.sbSettings.detectorChanged.connect(self.system.setDetector)
		# self.sbSettings.controls['cbReadOnly'].stateChanged.connect(partial(self.setControlsReadOnly))
		# self.setControlsReadOnly(True)
		self.sbSettings.loadStages(self.system.patientSupport.deviceList)
		self.sbSettings.loadDetectors(self.system.imager.deviceList)
		# When an image set is added to the HDF5 file, add it to the sidebar:QImaging:QComboBox.
		self.system.newImageSet.connect(self.sbImaging.addImageSet)
		# When the current xray image setlist set is changed, plot it.
		self.sbImaging.imageSetChanged.connect(self.loadXraySet)
		# Tell the system to acquire an x-ray.
		self.sbImaging.acquire.connect(self.system.acquireXray)
		# When the image mode changes tell the system.
		self.sbImaging.imageModeChanged.connect(self.system.setImagingMode)
		# Connect the calculate alignment button to the solver.
		self.sbTreatment.calculate.connect(partial(self.solve))
		# Connect the apply alignment button to the patient movement.
		self.sbTreatment.align.connect(partial(self.align))
		# Connect the treatment button to the patient treatment delivery.
		self.sbTreatment.deliver.connect(partial(self.treat))


		self.testing()

	def testing(self):
		# self.openFiles('folder')
		# self.envXray.plot.plot0.markerAdd(-27.036,45.995)
		# self.envXray.plot.plot0.markerAdd(32.8665,45.001)
		# self.envXray.plot.plot0.markerAdd(34.6091,-15.0564)
		# self.envXray.plot.plot90.markerAdd(-23.2147,46.0205)
		# self.envXray.plot.plot90.markerAdd(-57.9952,43.4355)
		# self.envXray.plot.plot90.markerAdd(43.1843,-15.4921)
		# self.patient.rtplan.plot[0].plot0.markerAdd(25.527,-27.8264)
		# self.patient.rtplan.plot[0].plot0.markerAdd(-29.334,-25.1335)
		# self.patient.rtplan.plot[0].plot0.markerAdd(-34.1097,32.0152)
		# self.patient.rtplan.plot[0].plot90.markerAdd(-0.3594,-27.2985)
		# self.patient.rtplan.plot[0].plot90.markerAdd(-35.9191,-25.8618)
		# self.patient.rtplan.plot[0].plot90.markerAdd(63.9358,31.6087)
		# Xray
		# self.openXray(['/Users/micahbarnes/Documents/scratch/testXray.hdf5'])
		self.openXray(['/home/imbl/Documents/Software/testdata/test.hdf5'])
		# CT
		# folder = '/Users/micahbarnes/Documents/scratch/ct-lamb/'
		# folder = '/Users/micahbarnes/Documents/scratch/head-phant/'
		# ds_ct = []
		# ds_rtplan = []
		# for root, subdir, fp in os.walk(folder):
		# 	for fn in fp:
		# 		if (fn.endswith(tuple('.dcm'))) & (fn[:len('ct')] == 'CT'):
		# 			ds_ct.append(os.path.join(root,fn))
		# 		elif (fn.endswith(tuple('.dcm'))) & (fn[:len('rp')] == 'RP'):
		# 			ds_rtplan.append(os.path.join(root,fn))
		# if len(ds_ct) > 0: self.openCT(ds_ct)
		# if len(ds_rtplan) > 0: self.openRTP(ds_rtplan)

		# self.envXray.plot[0].markerAdd(20,0)
		# self.envXray.plot[0].markerAdd(0,0)
		# self.envXray.plot[0].markerAdd(0,40)
		# self.envXray.plot[1].markerAdd(0,0)
		# self.envXray.plot[1].markerAdd(0,0)
		# self.envXray.plot[1].markerAdd(0,40)
		# self.envRtplan[0].plot[0].markerAdd(20,0)
		# self.envRtplan[0].plot[0].markerAdd(0,0)
		# self.envRtplan[0].plot[0].markerAdd(0,40)
		# self.envRtplan[0].plot[1].markerAdd(0,0)
		# self.envRtplan[0].plot[1].markerAdd(0,0)
		# self.envRtplan[0].plot[1].markerAdd(0,40)

	# def takestupidxray(self,theta):
	# 	# Grab frame from hamamastu.
	# 	try:
	# 		import pyepics as epics
	# 	except:
	# 		pass
	# 	arrayData = epics.caget('SR08ID01DET04:IMAGE:ArrayData')
	# 	arrayData = arrayData.reshape(1216,616)
	# 	self.envXray.plot[0].image.imshow(arrayData)
	# 	self.envXray.plot[0].canvas.draw()

	# def acquireXrays(self,theta,zTranslation,comment):
	# 	# Send command to system.
	# 	self.system.acquireXray(theta,zTranslation,comment)
		# Once done, load images.
		# for i in range(len(theta)):
			# self.envXray.plot[i].imageLoad(self.system.detector.imageBuffer[0])

	# def updateXraySetList(self,newItem):
		# Get the updated items list.
		# self.sbImaging.addImageSet(newItem)

	def loadXraySet(self,_set):
		# When the current image set is changed, get images and plot them.
		images = self.patient.dx.getImageSet(_set)
		# Set the amount of images required.
		self.envXray.loadImages(images)
		# Populate new editable isocenters.
		isocenter = self.envXray.getPlotIsocenter()
		self.sidebar.widget['xrayImageProperties'].addEditableIsocenter(isocenter)
		# Populate new histograms.
		histogram = self.envXray.getPlotHistogram()
		self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)
		# Populate the treatment delivery sidebar.
		_angles = []
		for i in range(len(images)):
			_angles.append(images[i].view['title'])
		self.sbTreatment.populateTreatments(_angles)

	@QtCore.pyqtSlot(int)
	def calculateAlignment(self,treatmentIndex):
		print('TADA MAIN.py L:188')

	@QtCore.pyqtSlot(float,float,float)
	def ctUpdateIsocenter(self,x,y,z):
		# Update the ct isocenter.
		try:
			self.patient.ct.isocenter = np.array([x,y,z])
			self.patient.ct.plot.updatePatientIsocenter(self.patient.ct.isocenter)
			logging.debug('Updated patient CT isocenter with vals: {} {} {}'.format(x,y,z))
		except:
			logging.warning('Unable to update CT isocenter.')

	@QtCore.pyqtSlot(str)
	def setControlsComplexity(self,level):
		self.controls.setLevel(level)

	@QtCore.pyqtSlot(bool)
	def enableDoAlignment(self,state=False):
		# self.pps._isStageConnected
		self.sbAlignment.widget['doAlignment'].setEnabled(state)

	def setControlsReadOnly(self,state):
		self.controls.setReadOnly(bool(not state))

	def newFile(self,modality):
		if modality == 'xray':
			fileFormat = 'HDF5 (*.hdf5)'
			fileDialogue = QtWidgets.QFileDialog()
			file, dtype = fileDialogue.getSaveFileName(self, "Create new x-ray dataset", "", fileFormat)
			# Create the new xray file.
			if file.endswith('.hdf5') is False:
				file += '.hdf5'
			self.patient.new(file,'DX')
			# Create an xray workspace.
			self.createWorkEnvironmentXray()

	def openFiles(self,modality):
		# We don't do any importing of pixel data in here; that is left up to the plotter by sending the filepath.
		if modality == 'ct':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			# fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			# files, dtype = fileDialogue.getOpenFileNames(self, "Open CT dataset", "", fileFormat)
			# self.openCT(folder)
			fileDialogue.setFileMode(QtWidgets.QFileDialog.Directory)
			folder = fileDialogue.getExistingDirectory(self, "Open CT dataset", "")
			dataset = []
			for root, subdir, fp in os.walk(folder):
				for fn in fp:
					if (fn.endswith(tuple('.dcm'))) & (fn[:len(modality)] == 'CT'):
						dataset.append(os.path.join(root,fn))
			if len(dataset) > 0:
				self.openCT(dataset)

		elif modality == 'xray':
			fileFormat = 'HDF5 (*.hdf5)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			file, dtype = fileDialogue.getOpenFileNames(self, "Open Xray dataset", "", fileFormat)
			self.patient.load(file,'DX')
			self.openXray(file)

		elif modality == 'rtp':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			file, dtype = fileDialogue.getOpenFileNames(self, "Open RP dataset", "", fileFormat)
			self.openRTP(file)

		elif modality == 'folder':
			# Try all file types...
			fileFormat = None
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.Directory)
			folder = fileDialogue.getExistingDirectory(self, "Open dataset folder", "")

			dataset = []
			modality = 'xray'
			for root, subdir, fp in os.walk(folder):
				for fn in fp:
					if (fn.endswith(tuple('.hdf5'))) & (fn[:len(modality)] == modality):
						dataset.append(os.path.join(root,fn))
			if len(dataset) > 0:
				self.patient.load(dataset,'DX')
				self.openXray(dataset)

			dataset = []
			modality = 'CT'
			for root, subdir, fp in os.walk(folder):
				for fn in fp:
					if (fn.endswith(tuple('.dcm'))) & (fn[:len(modality)] == modality):
						dataset.append(os.path.join(root,fn))
			if len(dataset) > 0:
				self.openCT(dataset)	
			
			dataset = []
			modality = 'RP'
			for root, subdir, fp in os.walk(folder):
				for fn in fp:
					if (fn.endswith(tuple('.dcm'))) & (fn[:len(modality)] == modality):
						dataset.append(os.path.join(root,fn))
			if len(dataset) > 0:
				self.openRTP(dataset)

			self.environment.button['CT'].clicked.emit()

	def openXray(self,files):
		"""Open XR (x-ray) modality files."""
		logging.info('Loading x-ray data into worksapce.')
		# Create new x-ray workspace if required.
		if self._isXrayOpen:
			# Re-initialise the environment.
			self.envXray.reset()
		else:
			self.createWorkEnvironmentXray()
		# Send x-ray dataset to plot.
		# self.envXray.loadImages(self.patient.dx.image)
		self.system.setLocalXrayFile(files)
		# Get list of existing x-rays in file.
		_list = self.patient.dx.getImageList()
		# Add them to the combo box.
		self.sbImaging.resetImageSetList()
		self.sbImaging.addImageSet(_list)
		# Get the plot histogram widgets and give them to the sidebar widget.
		histogram = self.envXray.getPlotHistogram()
		self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)
		# Get the plot isocenter widgets and give them to the sidebar widget.
		isocenter = self.envXray.getPlotIsocenter()
		self.sidebar.widget['xrayImageProperties'].addEditableIsocenter(isocenter)
		# Force marker update for table.
		self.envXray.set('maxMarkers',config.markers.quantity)
		# Finalise import. Set open status to true and open the workspace.
		self._isXrayOpen = True
		# self.sbImaging.enableAcquisition()
		self.environment.button['X-RAY'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','xrayImageProperties')

	def createWorkEnvironmentXray(self):
		# Create the base widgets for x-rays.
		logging.debug('Creating X-RAY Work Environment')
		# Make a widget for plot stuff.
		self.envXray = self.environment.addPage('X-RAY',QsWidgets.QPlotEnvironment())
		self.envXray.toggleSettings.connect(partial(self.sidebar.showStack,'ImageProperties'))
		# Connect max markers spin box.
		self.sbAlignment.markersChanged.connect(partial(self.envXray.set,'maxMarkers'))
		# Sidebar page for x-ray image properties.
		widget = self.sidebar.addPage('xrayImageProperties',QsWidgets.QXrayProperties(),addList=False)
		# Signals and slots.
		widget.toggleOverlay.connect(partial(self.envXray.toggleOverlay))
		self.sbImaging.enableAcquisition()
		self.sbImaging.resetImageSetList()

	def openCT(self,files):
		"""Open CT modality files."""
		logging.info('Loading CT')
		# Load CT Dataset.
		self.patient.load(files,'CT')
		# Create new CT workspace if required.
		if self._isCTOpen == False:
			self.createWorkEnvironmentCT()
			logging.debug('Created CT Work Environment')
		# Send ct dataset to plot.
		self.envCt.loadImages(self.patient.ct.image)
		# Get the plot histogram widgets and give them to the sidebar widget.
		histogram = self.envCt.getPlotHistogram()
		self.sidebar.widget['ctImageProperties'].addPlotHistogramWindow(histogram)
		# Force marker update for table.
		self.envCt.set('maxMarkers',config.markers.quantity)
		# Finalise import. Set open status to true and open the workspace.
		self._isCtOpen = True
		self.environment.button['CT'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','ctImageProperties')

	def createWorkEnvironmentCT(self):
		# Make a widget for plot stuff.
		self.envCt = self.environment.addPage('CT',QsWidgets.QPlotEnvironment())
		self.envCt.set('maxMarkers',config.markers.quantity)
		self.envCt.toggleSettings.connect(partial(self.sidebar.showStack,'ImageProperties'))
		# Connect max markers spin box.
		self.sbAlignment.markersChanged.connect(partial(self.envCt.set,'maxMarkers'))
		# Sidebar page for ct image properties.
		widget = self.sidebar.addPage('ctImageProperties',QsWidgets.QCtProperties(),addList=False)
		# Signals and slots.
		widget.toggleOverlay.connect(partial(self.envCt.toggleOverlay))

	def openRTP(self,files):
		"""Open CT modality files."""
		logging.info('Loading RTPLAN')
		# Load CT Dataset.
		self.patient.load(files,'RTPLAN')
		# Create new CT workspace if required.
		if self._isRTPOpen == False:
			logging.debug('Creating BEV Work Environments')
			pass
		else: 
			logging.error('BEV Work Environments already exist.')
			return
		# Create an RTPLAN environment for every beam.
		self.envRtplan = np.empty(len(self.patient.rtplan.beam),dtype=object)
		# Iterate through each planned beam.
		for i in range(len(self.patient.rtplan.beam)):
			""" CREATE WORK ENV """
			self.sbTreatment.widget['quantity'].setText(str(i+1))
			# Make a widget for plot stuff.
			self.envRtplan[i] = self.environment.addPage('BEV%i'%(i+1),QsWidgets.QPlotEnvironment())
			self.envRtplan[i].set('maxMarkers',config.markerQuantity)
			self.envRtplan[i].toggleSettings.connect(partial(self.sidebar.showStack,'ImageProperties'))
			# Connect max markers spin box.
			self.sbAlignment.markersChanged.connect(partial(self.envRtplan[i].set,'maxMarkers'))
			# Sidebar page for rtplan image properties.
			widget = self.sidebar.addPage('bev%iImageProperties'%(i+1),QsWidgets.QRtplanProperties(),addList=False)
			# Signals and slots.
			widget.toggleOverlay.connect(partial(self.envRtplan[i].toggleOverlay))
			""" POPULATE WORK ENV """
			self.envRtplan[i].loadImages(self.patient.rtplan.beam[i].image)
			# Set the mask data and isocenter data in the plots.
			self.envRtplan[i].set('patMask',self.patient.rtplan.beam[i].mask)
			self.envRtplan[i].set('patIso',self.patient.rtplan.beam[i].isocenter)
			# Get the plot histogram widgets and give them to the sidebar widget.
			histogram = self.envRtplan[i].getPlotHistogram()
			self.sidebar.widget['bev%iImageProperties'%(i+1)].addPlotHistogramWindow(histogram)
			# Force marker update for table.
			self.envRtplan[i].set('maxMarkers',config.markers.quantity)
		# Populate the sidebar with all the treatments.
		self.sbTreatment.populateTreatments()
		for i in range(len(self.patient.rtplan.beam)):
			self.sbTreatment.widget['beam'][i]['calculate'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=i))
		# Finalise import. Set open status to true and open the first BEV workspace.
		self._isRTPOpen = True
		self.environment.button['BEV1'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','bev1ImageProperties')

	def updateSettings(self,mode,origin,idx=0):
		"""Update variable based of changed data in property model (in some cases, external sources)."""
		if (mode == 'xr') & (self._isXrayOpen):
			"""Update x-ray specific properties."""
			if origin == self.sbXrayProperties.widget['alignIsocY']:
				# Overwrite the alignment isoc in settings.
				# config.hamamatsuAlignmentIsoc[:2] = origin.text()
				# config.hamamatsuAlignmentIsoc[0] = origin.text()
				# config.hamamatsuAlignmentIsoc[2] = origin.text()
				# Update the property variables.
				# item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['y'])
				# item.setData(origin.text(),QtCore.Qt.DisplayRole)
				# Re-calculate the extent.
				# self.xrayCalculateExtent()
				pass
			elif origin == self.sbXrayProperties.widget['alignIsocX']:
				# Overwrite the alignment isoc in settings.
				# config.hamamatsuAlignmentIsoc[2] = origin.text()
				# config.hamamatsuAlignmentIsoc[1] = origin.text()
				# Update the property variables.
				# item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['x'])
				# item.setData(origin.text(),QtCore.Qt.DisplayRole)
				# Re-calculate the extent.
				# self.xrayCalculateExtent()
				pass
			elif origin == self.sbXrayProperties.window['pbApply']:
				# Must be in radiograph mode.
				mode = 'radiograph'
				# Get the windows and apply them.
				windows = self.sbXrayProperties.getWindows()
				self.envXray.setRadiographMode(mode)
				self.envXray.plot.setWindows(windows)

		elif (mode == 'ct') & (self._isCTOpen):
			"""Update ct specific properties."""
			if origin == self.sbCTProperties.window['pbApply']:
				# Check mode type.
				if self.sbCTProperties.window['rbMax'].isChecked():
					mode = 'max'
				else:
					mode = 'sum'
				# Get windows and apply them.
				windows = self.sbCTProperties.getWindows()
				self.patient.ct.plot.setRadiographMode(mode)
				self.patient.ct.plot.setWindows(windows)

		elif (mode == 'rtplan') & (self._isRTPOpen):
			"""Update rtplan specific properties."""
			if origin == self.patient.rtplan.guiInterface[idx].window['pbApply']:
				# Check mode type.
				if self.patient.rtplan.guiInterface[idx].window['rbMax'].isChecked():
					mode = 'max'
				else:
					mode = 'sum'
				# Get windows and apply them.
				windows = self.patient.rtplan.guiInterface[idx].getWindows()
				self.patient.rtplan.plot[idx].setRadiographMode(mode)
				self.patient.rtplan.plot[idx].setWindows(windows)

		# elif mode == 'global':
		# 	"""Update global variables, applicable to all modes."""
		# 	if origin == self.sbAlignment.widget['maxMarkers']:
		# 		value = self.sbAlignment.widget['maxMarkers'].value()
		# 		# Update settings.
		# 		config.markerQuantity = value
		# 		# Update plot tables.
		# 		if self._isXrayOpen: self.envXray.settings('maxMarkers',value)
		# 		if self._isCTOpen: self.patient.ct.plot.settings('maxMarkers',value)
		# 		if self._isRTPOpen: 
		# 			for i in range(len(self.patient.rtplan.plot)):
		# 				self.patient.rtplan.plot[i].settings('maxMarkers',value)

	def toggleOptimise(self,state):
		"""State(bool) tells you whether you should clear the optimisation plots or not."""
		if state == True:
			pass
		elif state == False:
			try:
				"""Remove X-ray optimised points."""
				self.xray.plotEnvironment.plot0.markerRemove(marker=-2)
				self.xray.plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass
			try:
				"""Remove X-ray optimised points."""
				self.patient.ct.plotEnvironment.plot0.markerRemove(marker=-2)
				self.patient.ct.plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass
			try:
				"""Remove X-ray optimised points."""
				for i in range(len(self.rtp.beam)):
					self.rtp.beam[i].plotEnvironment.plot0.markerRemove(marker=-2)
					self.rtp.beam[i].plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass

	def solve(self,_index):
		logging.info("Solving alignment for dataset {}".format(_index))
		# Get the corresponding images.
		images = self.patient.dx.getImageSet(self.sbImaging.widget['imageList'].currentText())
		# Get the angle.
		theta = float(images[_index].view['title'][:-1])
		# Get the ptv point.
		_ptv = self.envXray.plot[_index].patientIsocenter
		# Calculate Txy.
		txy = -_ptv[0]
		# Calculate the output values.
		h1 = txy*np.sin(np.deg2rad(theta))
		h2 = txy*np.cos(np.deg2rad(theta))
		tz = -_ptv[1]

		# Store relative movements.
		self.system.solver[_index] = [h1,h2,tz,0,0,0]

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.updateVariable('Alignment',['Translation','H1','H2','V'],[h1,h2,tz])

	def align(self,_index):
		logging.info("Applying alignment for dataset {}".format(_index))
		# Get the corresponding images.
		images = self.patient.dx.getImageSet(self.sbImaging.widget['imageList'].currentText())
		# Get positions.
		_imagePos = images[_index].patientPosition
		_solution = self.system.solver[_index]
		moveTo = np.array(_imagePos) + np.array(_solution)
		self.system.patientSupport.setPosition(moveTo)
		self.sbTreatment.widget['beam'][_index]['alignmentComplete'] = True
		self.sbTreatment.treatmentInterlock(_index)

	def treat(self):
		_preTreatmentPos = self.system.patientSupport.position()

		"""
			PUT DUNCANS CODE HERE.
		"""

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())