# Program imports
import config
import workspace
import menubar
from sidebar import Sidebar
from synctools import QsWidgets
import time

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
import epics

# For PyInstaller:
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader extends the sys module by a flag frozen=True and sets the app path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
resourceFilepath = application_path+'/resources/'

# Select Qt5 user interface.
qtCreatorFile = application_path+"/resources/main.ui"
qtStyleSheet = open(application_path+"/resources/stylesheet.css")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

import logging, coloredlogs
coloredlogs.install(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',datefmt='%H:%M:%S',level=logging.INFO)

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
		self.setWindowTitle('syncMRT')
		self.setWindowIcon(QtGui.QIcon(resourceFilepath+'icon.png'))  

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
		# Sidebar: Imaging
		self.sidebar.addPage('Imaging',QsWidgets.QImaging(),before='all')
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
		# Connect the calculate alignment button to the solver.
		self.sbTreatment.calculate.connect(partial(self.solve))
		# Connect the apply alignment button to the patient movement.
		self.sbTreatment.align.connect(partial(self.align))
		# Connect the treatment button to the patient treatment delivery.
		self.sbTreatment.deliver.connect(partial(self.treat))

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
			isocenter = self.envXray.getPlotIsocenter()
			self.sidebar.widget['xrayImageProperties'].addEditableIsocenter(isocenter)
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
			self.openXray(file[0])

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

	def solve(self,_index):
		logging.info("Solving alignment for dataset {}".format(_index))
		# Get the corresponding images.
		images = self.patient.dx.getImageSet(self.sbImaging.widget['imageList'].currentText())
		# Get the angle.
		theta = -float(images[_index].view['title'][:-1])
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
		theta = float(images[_index].view['title'][:-1])
		_imagePos = images[_index].patientPosition
		_imagePos[5] = theta
		_solution = self.system.solver[_index]
		moveTo = np.array(_imagePos) + np.array(_solution)
		self.system.patientSupport.setPosition(moveTo)
		self.sbTreatment.widget['beam'][_index]['alignmentComplete'] = True
		self.sbTreatment.treatmentInterlock(_index)

	def treat(self,_index):
		_preTreatmentPos = self.system.patientSupport.position()
		_breathHold = False
		_beam = True
		_speed = 2.5
		_z_start = -11.6
		_z_stop = 11.6
		_z_home = 0.0
		_pv = "SR08ID01SST25:Z"

		# Close 1A Shutter.
		logging.debug("Closing 1A shutters.")
		epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)
		# Set up the scan.
		epics.caput(_pv+".VELO", float(10))
		# Start the breath-hold.
		if _breathHold:
			logging.debug("Turning breath hold on.")
			epics.caput("asImblZebra:SOFT_IN",0)
		# Push the mouse to the start pos.
		logging.debug("Moving to start position.")
		epics.caput(_pv+".VAL", float(_z_start),wait=True)
		# Set the treatment speed.
		epics.caput(_pv+".VELO", float(_speed))
		_reply = QtWidgets.QMessageBox.question(None,"Treatment Delivery","Do you want to treat?")
		if _reply == QtWidgets.QMessageBox.Yes:
			pass
		else:
			# Set everything back to normal and return.
			logging.critical("Treatment cancelled.")
			# Close 1A Shutter.
			logging.debug("Closing 1A shutters.")
			epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)
			# Turn breath hold off.
			if _breathHold:
				logging.debug("Turning off breath hold.")
				epics.caput("asImblZebra:SOFT_IN",1)
			# Move back to what was before irradiation.
			epics.caput(_pv+".VELO", float(10))
			self.system.patientSupport.setPosition(_preTreatmentPos)
			self.sbTreatment.resetTreatmentDelivery(_index)
			# Return
			return
		# Open the shutter.
		if _beam:
			logging.debug("Opening shutter.")
			epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD", 1, wait=True)
			time.sleep(3)
		# Move to the finish position.
		logging.debug("Scanning dynamic-wedge through beam.")
		epics.caput(_pv+".VAL", float(_z_stop),wait=True)
		# Close 1A Shutter.
		logging.debug("Closing 1A shutters.")
		epics.caput("SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD", 1, wait=True)
		time.sleep(3)
		# Turn breath hold off.
		if _breathHold:
			logging.debug("Turning off breath hold.")
			epics.caput("asImblZebra:SOFT_IN",1)
		# Set movement speed.
		epics.caput(_pv+".VELO", float(10))
		# Move to start position.
		logging.debug("Resetting to home position.")
		epics.caput(_pv+".VAL", float(_z_home),wait=True)

		# Move back to what was before irradiation.
		self.system.patientSupport.setPosition([0,0,0,0,0,0])

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())