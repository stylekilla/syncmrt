# Internal imports.
from resources import config, ui
import systems
import QsWidgets
# Core imports.
import os
import sys
from functools import partial
# Sitepackages imports.
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtGui, QtWidgets, uic

import threading

# Forcing a fix for MPL?
import matplotlib as mpl
mpl.use('Qt5Agg')
mpl.rcParams['toolbar'] = 'toolmanager'

# Some icons are used under the licence: https://fontawesome.com/license

# For PyInstaller:
if getattr(sys, 'frozen', False):
	# If the application is run as a bundle, the pyInstaller bootloader extends the sys module by a flag frozen=True and sets the app path into variable _MEIPASS'.
	application_path = sys._MEIPASS
else:
	application_path = os.path.dirname(os.path.abspath(__file__))
resourceFilepath = application_path+'/resources/'

# Select Qt5 user interface.
qtCreatorFile = resourceFilepath+"/ui/main.ui"
qtStyleSheet = open(resourceFilepath+"/ui/stylesheet.css")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

import logging

"""
MAIN CLASS: Application starts here.
"""

class main(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		# Inititate UI.
		QtWidgets.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setStyleSheet(qtStyleSheet.read())
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setWindowTitle('syncMRT')
		self.setWindowIcon(QtGui.QIcon(resourceFilepath+'images/icon.png'))

		"""
		Epics.
		"""
		# Run in parallel.
		# self.backendControlThread = None
		# Put epics on it's own thread.
		self.backendControlThread = QtCore.QThread()
		self.backendControlThread.start()
		logging.critical("Main Thread: {}".format(QtCore.QThread().currentThread()))
		logging.critical("Backend Thread: {}".format(self.backendControlThread.currentThread()))
		logging.critical('%-25s: %s, %s,' % (self, threading.current_thread().name, threading.current_thread().ident))
		# Create the monitor and move it to the epics thread.
		# self.epicsMonitor = systems.control.backend.epics.EpicsMonitor()
		# self.epicsMonitor.moveToThread(self.backendControlThread)

		"""
		Qt5 Setup
		"""
		# Menu bar.
		self._menuBar = ui.menubar.populate(self.menuBar())
		# Layout margins.
		self.layoutCentralWidget.setContentsMargins(0,0,0,0)
		self.statusBar.setContentsMargins(0,0,0,0)
		self.layoutSidebar.setContentsMargins(0,0,0,0)
		self.layoutWorkspace.setContentsMargins(0,0,0,0)
		self.centralWidgetTop.setContentsMargins(0,0,0,0)

		# Logging window
		self.logger = QsWidgets.QLog(self.frameLogger)
		logger = logging.getLogger()
		logger.addHandler(self.logger.handler)
		logger.setLevel(logging.INFO)

		# ===============================
		# Left Sidebar: General Commands.
		# ===============================
		self.sidebar = ui.sidebar.Sidebar(self.frameSidebarStack,self.frameSidebarList)
		# Sidebar: Imaging
		self.sidebar.addPage('Imaging',QsWidgets.QsSidebar.QImaging(),before='all')
		self.sbImaging = self.sidebar.getPage('Imaging')
		# Sidebar: Alignment.
		self.sbAlignment = self.sidebar.addPage('Alignment',QsWidgets.QsSidebar.QAlignment(),after='Imaging')
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		self.sbAlignment.widget['optimise'].toggled.connect(partial(self.toggleOptimise))
		self.sbAlignment.calculateAlignment.connect(self.patientCalculateAlignment)
		self.sbAlignment.doAlignment.connect(self.patientApplyAlignment)
		# Add treatment section to sidebar.
		self.sidebar.addPage('Treatment',QsWidgets.QsSidebar.QTreatment(),after='Alignment')
		self.sbTreatment = self.sidebar.getPage('Treatment')
		# Add image properties section to sidebar.
		self.sidebar.addPage('ImageProperties',None,after='Treatment')
		# Add settings section to sidebar.
		self.sidebar.addPage('Settings',QsWidgets.QsSidebar.QSettings(),after='all')
		self.sbSettings = self.sidebar.getPage('Settings')

		# Create work environment
		self.environment = ui.workspace.environment(self.toolbarPane,self.workStack)
		self.environment.workspaceChanged.connect(partial(self.sidebar.linkPages,'ImageProperties'))

		# =======================
		# Right Sidebar: ToolBox.
		# =======================
		self.rightSidebar = QsWidgets.QsSidebar.QSidebarList(self.frameRightSidebar)
		# Status Monitor.
		self.statusMonitor = QsWidgets.QsSidebar.QStatusMonitor()
		self.rightSidebar.addSection("Status Monitor",self.statusMonitor)
		self.statusMonitor.addMonitor('Positioning Support')
		self.statusMonitor.addMonitor('Imaging Detector')
		# Property manager.
		self.properties = QsWidgets.QsSidebar.QPropertyManager()
		self.rightSidebar.addSection("Poperties",self.properties)
		# Stage Position Monitor.
		self.ppsMonitor = QsWidgets.QsSidebar.QMotorMonitor()
		self.rightSidebar.addSection("Positioning Stage",self.ppsMonitor)
		# Create alignment table.
		self.properties.addSection('Alignment')
		self.properties.addVariable('Alignment',['Rotation','X','Y','Z'],[0,0,0])
		self.properties.addVariable('Alignment',['Translation','X','Y','Z'],[0,0,0])
		self.properties.addVariable('Alignment','Scale',0)

		# ==================
		# Bottom Status Bar.
		# ==================
		# Collapsing button for Logger.
		icon = QtGui.QIcon(resourceFilepath+'/images/CollapseBottom.png')
		icon.pixmap(20,20)
		self.pbCollapseLogger = QtWidgets.QPushButton(icon,'')
		self.pbCollapseLogger.setToolTip("Toggle Log Viewer")
		self.pbCollapseLogger.setFlat(True)
		self.pbCollapseLogger.setFixedWidth(22)
		self.statusBar.addPermanentWidget(self.pbCollapseLogger)
		self.pbCollapseLogger.clicked.connect(self.logger.toggleVisibility)

		# Collapsing button for Sidebar (Right).
		icon = QtGui.QIcon(resourceFilepath+'/images/CollapseRight.png')
		icon.pixmap(20,20)
		self.pbCollapseSidebar = QtWidgets.QPushButton(icon,'')
		self.pbCollapseSidebar.setToolTip("Toggle Properties Panel")
		self.pbCollapseSidebar.setFlat(True)
		self.pbCollapseSidebar.setFixedWidth(22)
		self.pbCollapseSidebar.clicked.connect(self.rightSidebar.toggleVisibility)
		self.statusBar.addPermanentWidget(self.pbCollapseSidebar)

		# =============
		# Top Menu Bar.
		# =============
		# Connect menubar items.
		self._menuBar['new_xray'].triggered.connect(partial(self.newFile,'xray'))
		self._menuBar['load_xray'].triggered.connect(partial(self.openFiles,'xray'))
		self._menuBar['load_syncplan'].triggered.connect(partial(self.openFiles,'syncplan'))
		self._menuBar['load_ct'].triggered.connect(partial(self.openFiles,'ct'))
		self._menuBar['load_rtplan'].triggered.connect(partial(self.openFiles,'rtp'))
		# self._menuBar['load_folder'].triggered.connect(partial(self.openFiles,'folder'))
		self._menuBar['load_folder'].triggered.connect(self.test)

		# Switches.
		self._isXrayOpen = False
		self._isCTOpen = False
		self._isMRIOpen = False
		self._isRTPOpen = False

		"""
		The Brain Setup.
		"""
		# Create a new system, this has a solver, detector and stage.
		self.system = systems.theBrain.Brain(
			resourceFilepath+config.files.patientSupports,
			resourceFilepath+config.files.detectors,
			config,
			deviceMonitor=self.statusMonitor,
			backendThread=self.backendControlThread
		)

		# Put the brain on it's own thread.
		self.systemThread = QtCore.QThread()
		self.systemThread.start()
		self.system.moveToThread(self.systemThread)
		# Create a patient.
		self.patient = systems.patient.Patient()
		# Link the system with the patient data.
		self.system.loadPatient(self.patient)
		# Add a monitor to the pps.
		self.system.setPatientSupportMonitor(self.ppsMonitor)
		# Get signal for a new patient support move.
		self.system.newMove.connect(self.showMovement)

		"""
		More GUI linking from System and Patient.
		"""
		# Create controls work environment.
		self.sbSettings.stageChanged.connect(self.system.setStage)
		self.sbSettings.refreshConnections.connect(self.system.patientSupport.reconnect)
		self.sbSettings.refreshConnections.connect(self.system.imager.reconnect)
		self.sbSettings.detectorChanged.connect(self.system.setDetector)
		self.sbSettings.loadStages(self.system.patientSupport.deviceList)
		self.sbSettings.loadDetectors(self.system.imager.deviceList)
		# When an image set is added to the HDF5 file, add it to the sidebar:QImaging:QComboBox.
		self.system.newImageSet.connect(self.sbImaging.addImageSet)
		# When the current xray image setlist set is changed, plot it.
		self.sbImaging.imageSetChanged.connect(self.loadXrayImage)
		# Tell the system to acquire an x-ray.
		self.sbImaging.acquire.connect(self.system.acquireXray)
		# When the image mode changes tell the system.
		self.sbImaging.imageModeChanged.connect(self.system.setImagingMode)

	def test(self):
		logging.critical("Running test function.")
		self.system.movePatient([10,5,1,0,0,2.5],'absolute')

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
			if self._isXrayOpen:
				# We have one. Reset it.
				self.envXray.reset()
			else:
				# We need an x-ray environment. Create it.
				self.createWorkEnvironmentXray()
			# Get list of existing x-rays in file.
			_list = self.patient.dx.getImageList()
			# Add them to the combo box.
			self.sbImaging.resetImageSetList()
			self.sbImaging.addImageSet(_list)
			# Get the plot histogram widgets and give them to the sidebar widget.
			histogram = self.envXray.getPlotHistogram()
			self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)
			# Force marker update for table.
			self.envXray.set('maxMarkers',config.markers.quantity)
			# Finalise import. Set open status to true and open the workspace.
			self._isXrayOpen = True
			self.environment.button['X-RAY'].clicked.emit()
			self.sidebar.linkPages('ImageProperties','xrayImageProperties')

	def openFiles(self,modality):
		# We don't do any importing of pixel data in here; that is left up to the plotter by sending the filepath.
		if modality == 'ct':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
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
			if len(file) > 0: self.openXray(file[0])

		elif modality == 'syncplan':
			fileFormat = 'CSV (*.csv)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			file, dtype = fileDialogue.getOpenFileNames(self, "Open Synchrotron Treatment Plan", "", fileFormat)
			if len(file) > 0: self.openSyncPlan(file[0])

		elif modality == 'rtp':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			file, dtype = fileDialogue.getOpenFileNames(self, "Open RP dataset", "", fileFormat)
			if len(file) > 0: self.openRTP(file)

		elif modality == 'folder':
			# Try all file types...
			fileFormat = None
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.Directory)
			folder = fileDialogue.getExistingDirectory(self, "Open dataset folder", "")
			if folder != '':
				dataset = []
				modality = 'xray'
				for root, subdir, fp in os.walk(folder):
					for fn in fp:
						if (fn.endswith(tuple('.hdf5'))) & (fn[:len(modality)] == modality):
							dataset.append(os.path.join(root,fn))
				if len(dataset) > 0:
					self.patient.load(dataset,'DX')
					self.openXray(dataset[0])

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
			# Connect the settings mask size to the plot.
			self.sbSettings.maskSizeChanged.connect(self.envXray.setMaskSize)
			# Force marker update for table.
			self.envXray.set('maxMarkers',config.markers.quantity)
		else:
			self.createWorkEnvironmentXray()
		# Open the x-ray file.
		self.patient.load(files,'DX')
		# Get list of existing x-rays in file.
		_list = self.patient.dx.getImageList()
		# Add them to the combo box.
		self.sbImaging.resetImageSetList()
		self.sbImaging.addImageSet(_list)
		# Connect the settings mask size to the plot.
		self.sbSettings.maskSizeChanged.connect(self.envXray.setMaskSize)
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
		# Connect signal for number of markers.
		self.sbAlignment.markersChanged.connect(partial(self.envXray.set,'maxMarkers'))
		# Connect image properties page.
		self.envXray.toggleSettings.connect(partial(self.sidebar.showStack,'ImageProperties'))
		# Sidebar page for x-ray image properties.
		widget = self.sidebar.addPage('xrayImageProperties',QsWidgets.QsSidebar.QXrayProperties(),addList=False)
		widget.toggleOverlay.connect(partial(self.envXray.toggleOverlay))
		widget.isocenterUpdated.connect(self.envXray.updateIsocenter)
		widget.pickIsocenter.connect(self.envXray.pickIsocenter)
		widget.align.connect(self.patientApplyAlignment)
		self.envXray.newIsocenter.connect(widget.setIsocenter)
		# What is this?
		self.sbImaging.enableAcquisition()
		self.sbImaging.resetImageSetList()
		# Add histograms widgets.
		histogram = self.envXray.getPlotHistogram()
		self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)

	def loadXrayImage(self,_set):
		"""
		Load an x-ray image from the HDF5 dataset into the plot environment.
		"""
		if _set == "":
			# No valid image is selected, assume the file is empty, so reset the plot environment and return.
			self.envXray.reset()
			# Connect the settings mask size to the plot.
			self.sbSettings.maskSizeChanged.connect(self.envXray.setMaskSize)
			# Force marker update for table.
			self.envXray.set('maxMarkers',config.markers.quantity)
			return
		# When the current image set is changed, get images and plot them.
		images = self.patient.dx.getImageSet(_set)
		# Update the sidebar comment label.
		self.sbImaging.updateCurrentImageDetails(images[0].comment)
		# Set the amount of images required.
		self.envXray.loadImages(images)
		# Toggle the ovelrays on and off to refresh them.
		self.sidebar.widget['xrayImageProperties'].refreshOverlays()

	def openSyncPlan(self,file):
		""" Open Synchrotron Treatment Plan. """
		self.patient.load(file,'SYNCPLAN')
		# Now populate the treatment delivery pane... lol.

	def openCT(self,files):
		"""Open CT modality files."""
		logging.info('Loading CT')
		# Load CT Dataset.
		self.patient.load(files,'CT')
		# Create new CT workspace if required.
		if self._isCTOpen == False:
			self.createWorkEnvironmentCT()
			logging.debug('Created CT Work Environment')
		# Enable the CT view selection.
		self.sidebar.widget['ctImageProperties'].group['view'].setEnabled(True)
		# Update the CT view.
		self.sidebar.widget['ctImageProperties'].updateCtView.connect(self.patient.ct.calculateView)
		self.patient.ct.newCtView.connect(self.updateCTEnv)
		# Load the CT images and get the histograms.
		self.updateCTEnv()
		# Force marker update for table.
		self.envCt.set('maxMarkers',config.markers.quantity)
		# Finalise import. Set open status to true and open the workspace.
		self._isCTOpen = True
		self.environment.button['CT'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','ctImageProperties')

	def updateCTEnv(self):
		# Send ct dataset to plot.
		self.envCt.loadImages(self.patient.ct.image)
		# Update the extent.
		logging.critical(self.patient.ct.viewExtent)
		self.sidebar.widget['ctImageProperties'].setCtRoi(self.patient.ct.viewExtent)
		# Get the plot histogram widgets and give them to the sidebar widget.
		histogram = self.envCt.getPlotHistogram()
		self.sidebar.widget['ctImageProperties'].addPlotHistogramWindow(histogram)

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
		widget.align.connect(self.patientCalculateAlignment)
		widget.isocenterUpdated.connect(self.envCt.updateIsocenter)
		widget.pickIsocenter.connect(self.envCt.pickIsocenter)
		self.envCt.newIsocenter.connect(widget.setIsocenter)
		widget.toggleOverlay.connect(partial(self.envCt.toggleOverlay))
		# Add histograms widgets.
		histogram = self.envCt.getPlotHistogram()
		self.sidebar.widget['ctImageProperties'].addPlotHistogramWindow(histogram)

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
			self.envRtplan[i].set('maxMarkers',config.markers.quantity)
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
			self.envRtplan[i].set('patIso',self.patient.rtplan.getIsocenter(i))
			# Get the plot histogram widgets and give them to the sidebar widget.
			histogram = self.envRtplan[i].getPlotHistogram()
			self.sidebar.widget['bev%iImageProperties'%(i+1)].addPlotHistogramWindow(histogram)
			# Force marker update for table.
			self.sbAlignment.markersChanged.connect(partial(self.envRtplan[i].set,'maxMarkers'))
		# Populate the sidebar with all the treatments.
		self.sbTreatment.populateTreatments()
		for i in range(len(self.patient.rtplan.beam)):
			self.sbTreatment.widget['beam'][i]['calculate'].clicked.connect(partial(self.patientCalculateAlignment,index=i))
		# Finalise import. Set open status to true and open the first BEV workspace.
		self._isRTPOpen = True
		self.environment.button['BEV1'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','bev1ImageProperties')

	def showMovement(self,uid):
		logging.info("Show Movement UID: {}".format(uid))
		# Get all the appropriate data. We assume since there is a move that there must be a patient support system connected.
		device = self.system.patientSupport.currentDevice
		motors = self.system.patientSupport.currentMotors

		# Show a pop up with the current movements.
		self._movementWindow = QsWidgets.QMovementWindow(device,motors,uid)

		# Setup.
		# origin = self.system.get(uid)
		# movements = self.system.get(uid)
		destination = self.system.getPatientMove(uid)
		self._movementWindow.setDestination(destination)

		self._movementWindow.show()

	def updateSettings(self,mode,origin,idx=0):
		"""Update variable based of changed data in property model (in some cases, external sources)."""
		if (mode == 'xr') & (self._isXrayOpen):
			"""Update x-ray specific properties."""
			if origin == self.sbXrayProperties.widget['alignIsocY']:
				pass
			elif origin == self.sbXrayProperties.widget['alignIsocX']:
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

	def toggleOptimise(self,state):
		"""State(bool) tells you whether you should clear the optimisation plots or not."""
		logging.critical("This does not work anymore. Must be re-implemented.")
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

	def patientCalculateAlignment(self,index):
		""" 
		Send coordinates to algorithm and align.
		Index 	0: CT with a preset 0,0,0 DICOM iso or a defined one.
				1+: Beam's Eye View Number (BEV#)
				-1: Local x-ray isocenter, no other paired imaging/data
		Left points : DICOM coordinate system
		Right points : Local coordinate system
		"""
		# Treatment index will tell the method where the call was made from.
		logging.info('Calulating patient alignment with condition '+str(index))

		if index == -1:
			# First check we have an x-ray environment.
			if self._isXrayOpen:
				# Now get the isocenter (defaults to 0,0,0).
				isocenter = self.envXray.getIsocenter()
				r = np.zeros((3,3))
				l = np.zeros((3,3))
		elif index == 0:
			# Align to a CT.
			if (self._isXrayOpen|self._isCTOpen) is False:
				error = QtWidgets.QMessageBox()
				error.setText('Must have both a local x-ray dataset and CT dataset open.')
				error.exec()
				return
			# Do stuff.
		elif index > 0:
			# Align to a BEV.
			if (self._isXrayOpen|self._isCTOpen|self._isRTPOpen) is False:
				error = QtWidgets.QMessageBox()
				error.setText('Must have a local x-ray, CT and Treatment Plan dataset open.')
				error.exec()
				return
			# Do stuff.

		# Get the number of points that each plot environment should have.
		numberOfPoints = self.sbAlignment.widget['maxMarkers'].value()

		# error = QtWidgets.QErrorMessage()
		# error.showMessage("Please ensure {} markers are selected in the CT images.".format(numberOfPoints))
		# return
		if index == 0:
			# Align to a CT.
			# Get the x-ray (right) points. These are always in terms of the fixed synchrotron axes.
			r = self.envXray.getMarkers()
			l = self.envCt.getMarkers(raw=True)
			# Get the CT isocenter.
			isocenter = self.envCt.getIsocenter(raw=True)
		elif index > 0:
			# Align to a BEV.
			# Get the x-ray (right) points. These are always in terms of the fixed synchrotron axes.
			r = self.envXray.getMarkers()
			l = self.envRtplan[index-1].getMarkers(raw=True)
			# Get the RTPLAN isocenter.
			# isocenter = self.patient.rtplan.beam[index-1].isocenter
			isocenter = self.envRtplan[index-1].getIsocenter(raw=True)

		# Finally, we can send the points off for calculation to `theBrain`!
		self.system.solver.setInputs(
			left=l,
			right=r,
			patientIsoc=isocenter
		)

		# We have some points. Calculate the global result.
		alignment6d = self.system.solver.solve()

		# If table already exists, update information...
		self.properties.updateVariable('Alignment',['Rotation','X','Y','Z'],[float(alignment6d[3]),float(alignment6d[4]),float(alignment6d[5])])
		self.properties.updateVariable('Alignment',['Translation','X','Y','Z'],[float(alignment6d[0]),float(alignment6d[1]),float(alignment6d[2])])
		self.properties.updateVariable('Alignment','Scale',float(self.system.solver.scale))

		# Calculate alignment for stage.
		self.system.calculateAlignment()

	def patientApplyAlignment(self,index):
		"""Calculate alignment first."""
		self.patientCalculateAlignment(index=index)
		# Calculate alignment for stage.
		self.system.calculateAlignment()
		# Do the alignment.
		self.system.applyAlignment()

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())