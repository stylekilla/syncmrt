# Internal imports.
from resources import config, ui
import systems
import QsWidgets
from systems.imageGuidance import nonOrthogonalImaging
# Core imports.
import os
import sys
from functools import partial
# Sitepackages imports.
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtGui, QtWidgets, uic

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

# Colored logs.
import logging, coloredlogs
coloredlogs.install(
	fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
	datefmt='%H:%M:%S',
	level=logging.INFO
	)

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
		Qt5 Setup
		"""
		# Menu bar.
		self._menuBar = ui.menubar.populate(self.menuBar())
		# Layout margins.
		self.layoutCentralWidget.setContentsMargins(0,0,0,0)
		self.statusBar.setContentsMargins(0,0,0,0)
		self.layoutSidebar.setContentsMargins(0,0,0,0)
		self.layoutWorkspace.setContentsMargins(0,0,0,0)

		# Sidebar panel.
		self.sidebar = ui.sidebar.Sidebar(self.frameSidebarStack,self.frameSidebarList)
		# Sidebar: Alignment.
		self.sbAlignment = self.sidebar.addPage('Alignment',QsWidgets.QAlignment(),before='all')
		self.sbAlignment.widget['maxMarkers'].setValue(3)
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		self.sbAlignment.widget['calcAlignment'].clicked.connect(partial(self.patientCalculateAlignment,index=-1))
		self.sbAlignment.widget['doAlignment'].clicked.connect(partial(self.patientApplyAlignment,index=-1))
		self.sbAlignment.widget['optimise'].toggled.connect(partial(self.toggleOptimise))
		# Sidebar: Imaging
		self.sidebar.addPage('Imaging',QsWidgets.QImaging(),after='Alignment')
		self.sbImaging = self.sidebar.getPage('Imaging')
		# self.sbImaging.acquire.connect(self.acquireXrays)
		# Add treatment section to sidebar.
		self.sidebar.addPage('Treatment',QsWidgets.QTreatment(),after='Imaging')
		self.sbTreatment = self.sidebar.getPage('Treatment')
		# Add image properties section to sidebar.
		self.sidebar.addPage('ImageProperties',None,after='Treatment')
		# Add settings section to sidebar.
		self.sidebar.addPage('Settings',QsWidgets.QSettings(),after='all')
		self.sbSettings = self.sidebar.getPage('Settings')

		# Create work environment
		self.environment = ui.workspace.environment(self.toolbarPane,self.workStack)
		self.environment.workspaceChanged.connect(partial(self.sidebar.linkPages,'ImageProperties'))

		# PropertyManager
		self.property = ui.workspace.propertyModel()
		self.propertyTree = ui.workspace.propertyManager(self.frameVariablePane,self.property)

		# Collapsing button for Property Manager.
		icon = QtGui.QIcon(resourceFilepath+'/images/CollapseRight.png')
		icon.pixmap(20,20)
		self.pbCollapseProperties = QtWidgets.QPushButton(icon,'')
		self.pbCollapseProperties.setFlat(True)
		self.statusBar.addPermanentWidget(self.pbCollapseProperties)
		self.pbCollapseProperties.clicked.connect(partial(self.propertyTree.toggleFrame,self.frameVariablePane))

		# Create alignment table.
		self.property.addSection('Alignment')
		self.property.addVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment',['Translation','x','y','z'],[0,0,0])
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

		"""
		SyncMRT Setup
		"""
		# Create a new system, this has a solver, detector and stage.
		self.system = systems.theBrain.Brain(resourceFilepath+config.files.patientSupports,resourceFilepath+config.files.detectors,config)
		self.patient = systems.patient.Patient()
		# Link the system with the patient data.
		self.system.loadPatient(self.patient)

		"""
		More GUI linking from System and Patient.
		"""
		# Create controls work environment.
		self.sbSettings.modeChanged.connect(self.setControlsComplexity)
		self.sbSettings.stageChanged.connect(self.system.setStage)
		self.sbSettings.refreshConnections.connect(self.system.patientSupport.reconnect)
		self.sbSettings.refreshConnections.connect(self.system.imager.reconnect)
		self.sbSettings.detectorChanged.connect(self.system.setDetector)
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

		# self.testing()

	def testing(self):
		self.openXray('../scratch/test.hdf5')
		dataset = []
		modality = 'CT'
		# for root, subdir, fp in os.walk('../scratch/head-phant/'):
		for root, subdir, fp in os.walk('../scratch/HeadneckCT/'):
			for fn in fp:
				# if (fn.endswith('.dcm')) & (fn[:len(modality)] == modality):
				if fn.endswith('.dcm'):
					dataset.append(os.path.join(root,fn))
		if len(dataset) > 0:
			self.openCT(dataset)

		# 2D test case.
		# self.envXray.plot[0].markerAdd(10.61,30)
		# self.envXray.plot[0].markerAdd(-10.61,30)
		# self.envXray.plot[0].markerAdd(-5.3,-10)
		# self.envCt.plot[0].markerAdd(15,30)
		# self.envCt.plot[0].markerAdd(-15,30)
		# self.envCt.plot[0].markerAdd(-7.5,-10)

		# self.envXray.plot[0].markerAdd(0.0,-25)
		# self.envXray.plot[0].markerAdd(0.0,25)
		# self.envXray.plot[0].markerAdd(-53.03,25)
		# self.envXray.plot[1].markerAdd(-35.35,-25)
		# self.envXray.plot[1].markerAdd(-35.35,25)
		# self.envXray.plot[1].markerAdd(-17.67,25)
		# self.envCt.plot[0].markerAdd(-25,25)
		# self.envCt.plot[0].markerAdd(-25,-25)
		# self.envCt.plot[0].markerAdd(25,-25)
		# self.envCt.plot[1].markerAdd(25,25)
		# self.envCt.plot[1].markerAdd(25,-25)
		# self.envCt.plot[1].markerAdd(50,-25)

		# self.patientCalculateAlignment()

	@QtCore.pyqtSlot(int)
	def calculateAlignment(self,index):
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
			# self.system.setLocalXrayFile(file)
			# Create an xray workspace.
			if not self._isXrayOpen:
				self.createWorkEnvironmentXray()
			# Get list of existing x-rays in file.
			_list = self.patient.dx.getImageList()
			# Add them to the combo box.
			self.sbImaging.resetImageSetList()
			self.sbImaging.addImageSet(_list)
			# Get the plot histogram widgets and give them to the sidebar widget.
			histogram = self.envXray.getPlotHistogram()
			self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)
			# Get the plot isocenter widgets and give them to the sidebar widget.
			# isocenter = self.envXray.getPlotIsocenter()
			# self.sidebar.widget['xrayImageProperties'].addEditableIsocenter(isocenter)
			# Force marker update for table.
			self.envXray.set('maxMarkers',config.markers.quantity)
			# Finalise import. Set open status to true and open the workspace.
			self._isXrayOpen = True
			# self.sbImaging.enableAcquisition()
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
		else:
			self.createWorkEnvironmentXray()
		# Open the x-ray file.
		self.patient.load(files,'DX')
		# Get list of existing x-rays in file.
		_list = self.patient.dx.getImageList()
		# Add them to the combo box.
		self.sbImaging.resetImageSetList()
		self.sbImaging.addImageSet(_list)
		# Get the plot histogram widgets and give them to the sidebar widget.
		histogram = self.envXray.getPlotHistogram()
		self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)
		# Get the plot isocenter widgets and give them to the sidebar widget.
		# isocenter = self.envXray.getPlotIsocenter()
		# self.sidebar.widget['xrayImageProperties'].addEditableIsocenter(isocenter)
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
		# Sidebar page for x-ray image properties.
		widget = self.sidebar.addPage('xrayImageProperties',QsWidgets.QXrayProperties(),addList=False)
		# Signals and slots.
		widget.toggleOverlay.connect(partial(self.envXray.toggleOverlay))
		self.sbImaging.enableAcquisition()
		self.sbImaging.resetImageSetList()

	def loadXraySet(self,_set):
		logging.debug("Reading image set {}.".format(_set))
		# When the current image set is changed, get images and plot them.
		images = self.patient.dx.getImageSet(_set)
		# Set the amount of images required.
		self.envXray.loadImages(images)	
		# Toggle the ovelrays on and off to refresh them.
		self.sidebar.widget['xrayImageProperties'].refreshOverlays()
		# Populate new histograms.
		histogram = self.envXray.getPlotHistogram()
		self.sidebar.widget['xrayImageProperties'].addPlotHistogramWindow(histogram)

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
		self.sidebar.widget['ctImageProperties'].updateCtView.connect(self.patient.ct.changeView)
		self.patient.ct.newCtView.connect(self.updateCTEnv)
		# Load the CT images and get the histograms.
		self.updateCTEnv()
		# # Send ct dataset to plot.
		# self.envCt.loadImages(self.patient.ct.image)
		# # Get the plot histogram widgets and give them to the sidebar widget.
		# histogram = self.envCt.getPlotHistogram()
		# self.sidebar.widget['ctImageProperties'].addPlotHistogramWindow(histogram)
		# Force marker update for table.
		self.envCt.set('maxMarkers',config.markers.quantity)
		# Finalise import. Set open status to true and open the workspace.
		self._isCTOpen = True
		self.environment.button['CT'].clicked.emit()
		self.sidebar.linkPages('ImageProperties','ctImageProperties')

	def updateCTEnv(self):
		# Send ct dataset to plot.
		self.envCt.loadImages(self.patient.ct.image)
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
			self.envRtplan[i].set('patIso',self.patient.rtplan.beam[i].isocenter)
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

	def patientCalculateAlignment(self,index=-1):
		""" Send coordinates to algorithm and align. """
		# Treatment index will tell the method where the call was made from.
		logging.info('Calulating patient alignment with condition '+str(index))

		# Check first if we at least have an x-ray plus a CT or RTPLAN open.
		if (self._isXrayOpen & (self._isCTOpen|self._isRTPOpen) ) is False:
			logging.error('Need at least two datasets open: xray('+str(self._isXrayOpen)+'), ct('+str(self._isCTOpen)+'), rtplan('+str(self._isRTPOpen)+').')
			return


		# Initialise points (l:Dicom, r:Xray).
		numberOfPoints = self.sbAlignment.widget['maxMarkers'].value()
		l = np.zeros((numberOfPoints,3))
		r = np.zeros((numberOfPoints,3))

		# Check that each plot has enough points.
		if (len(self.envXray.plot[0].pointsX) != numberOfPoints): 
			logging.error("At least {} points required in X-ray for calculation.".format(numberOfPoints))
			return

		# 2D or 3D? (Default is 2D)
		# Dependent on how many x-ray images are used.
		_3D = False
		if len(self.envXray.plot) == 2: _3D = True

		# Get the x-ray (right) points.
		if _3D:
			if (len(self.envXray.plot[1].pointsX) != numberOfPoints): 
				logging.error("At least {} points required in X-ray for calculation.".format(numberOfPoints))
				return
			p1 = self.envXray.plot[0].markers()
			p2 = self.envXray.plot[1].markers()
			# Now we need to go through the new routine for non-orthogonal imaging.
			t1 = self.envXray.plot[0]._imagingAngle
			t2 = self.envXray.plot[1]._imagingAngle

			r = nonOrthogonalImaging.calculate(p1,p2,t1,t2)
		else:
			r[:,1] = self.envXray.plot[0].pointsX
			r[:,2] = self.envXray.plot[0].pointsY

		# Now we need to make sure they are in a cartesian Right-Hand XYZ format.
		# I think they are at this point. The output of nonOrthogonalImaging.calculate() should do this.

		# Now we need to take the dicom points.
		if index == -1:
			# Check that each plot has enough points.
			if (len(self.envCt.plot[0].pointsX) != numberOfPoints) or (len(self.envCt.plot[1].pointsX) != numberOfPoints): 
				logging.error("At least {} points required in CT for calculation.".format(numberOfPoints))
				return
			iso = np.array([0,0,0])
			# Take the depth down the BEV as X.
			l[:,0] = self.envCt.plot[1].pointsX
			# Take the BEV lateral view as Y.
			l[:,1] = self.envCt.plot[0].pointsX
			# Take the vertical of the BEV as Z.
			l[:,2] = (np.array(self.envCt.plot[0].pointsY)+np.array(self.envCt.plot[1].pointsY))/2

		else:
			# Check that each plot has enough points.
			if (len(self.envRtplan[index].plot[0].pointsX) != numberOfPoints) or (len(self.envRtplan[index].plot[1].pointsX) != numberOfPoints): 
				logging.error("At least {} points required in BEV{} for calculation.".format(numberOfPoints,treatmentIndex))
				return
			iso = self.patient.rtplan.beam[index].isocenter
			# Take the depth down the BEV as X.
			l[:,0] = self.envRtplan[index].plot[1].pointsX
			# Take the BEV lateral view as Y.
			l[:,1] = self.envRtplan[index].plot[0].pointsX
			# Take the vertical of the BEV as Z.
			l[:,2] = (np.array(self.envRtplan[index].plot[0].pointsY)+np.array(self.envRtplan[index].plot[1].pointsY))/2

		# Now we need to make sure they are also in a cartesian Right-Hand XYZ format.
		# Unsure if this is the case.

		# Finally, we can send the points off for calculation to `theBrain`!
		self.system.solver.setInputs(
			left=l,
			right=r,
			patientIsoc=iso
			)

		# We have some points. Calculate the global result.
		alignment6d = self.system.solver.solve()
		# Get synchrotron axes alignment.
		# synchrotron6d = [-alignment6d[2],alignment6d[1],-alignment6d[0],-alignment6d[5],alignment6d[4],-alignment6d[3]]

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(alignment6d[3]),float(alignment6d[4]),float(alignment6d[5])])
		self.property.updateVariable('Alignment',['Translation','x','y','z'],[float(alignment6d[0]),float(alignment6d[1]),float(alignment6d[2])])
		self.property.updateVariable('Alignment','Scale',float(self.system.solver.scale))

	def patientApplyAlignment(self,index=-1):
		"""Calculate alignment first."""
		self.patientCalculateAlignment(index=index)

		# Calculate alignment for stage.
		self.system.calculateAlignment()

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())