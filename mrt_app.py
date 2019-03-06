# Program imports
import config
import workspace
import sidebar
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

import logging
# Debug levels: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(level=logging.CRITICAL)

'''
MAIN CLASS
- def openFiles(self, modality): Imports files, gathers variables and plots. 
'''

class main(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		# Inititate UI.
		QtWidgets.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setStyleSheet(qtStyleSheet.read())
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		'''
		Qt5 Setup
		'''
		# Layout margins.
		self.layoutCentralWidget.setContentsMargins(0,0,0,0)
		self.statusBar.setContentsMargins(0,0,0,0)
		self.layoutSidebar.setContentsMargins(0,0,0,0)
		self.layoutWorkspace.setContentsMargins(0,0,0,0)

		# Sidebar panels
		self.sbStack = sidebar.stack(self.frameSidebarStack)
		self.sbList = sidebar.stackList(self.widgetSidebarList)
		self.sbSelector = sidebar.selector(self.sbList,self.sbStack)

		# Add alignment section to sidebar (list+stack).
		self.sbSelector.addPage('Alignment',before='all')
		self.sbAlignment = sidebar.alignment(self.sbStack.stackDict['Alignment'])
		self.sbAlignment.widget['maxMarkers'].setValue(3)
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		self.sbAlignment.widget['calcAlignment'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=-1))
		self.sbAlignment.widget['doAlignment'].clicked.connect(partial(self.patientApplyAlignment,treatmentIndex=-1))
		self.sbAlignment.widget['optimise'].toggled.connect(partial(self.toggleOptimise))

		# Add treatment section to sidebar.
		self.sbSelector.addPage('Treatment',after='Alignment')
		self.sbTreatment = sidebar.treatment(self.sbStack.stackDict['Treatment'])

		# Add image properties section to sidebar.
		self.sbSelector.addPage('ImageProperties',after='Treatment')

		# Add settings section to sidebar.
		self.sbSelector.addPage('Settings',after='all')
		self.sbSettings = sidebar.settings(self.sbStack.stackDict['Settings'])

		# Create work environment
		self.workEnvironment = workspace.environment(self.toolbarPane,self.workStack)

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
		self.property.addVariable('Alignment',['Translation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment','Scale',0)
		self.propertyTree.expandAll()

		# Connect buttons and widgets.
		self.menuFileOpenCT.triggered.connect(partial(self.openFiles,'ct'))
		self.menuFileOpenXray.triggered.connect(partial(self.openFiles,'xray'))
		self.menuFileOpenMRI.triggered.connect(partial(self.openFiles,'mri'))
		self.menuFileOpenRTP.triggered.connect(partial(self.openFiles,'rtp'))
		self.menuFolderOpen.triggered.connect(partial(self.openFiles,'folder'))

		# Switches.
		self._isXrayOpen = False
		self._isCTOpen = False
		self._isMRIOpen = False
		self._isRTPOpen = False

		# TESTING MENU
		self.menuTESTING.triggered.connect(self.testing)

		'''
		SyncMRT Setup
		'''
		# Create a new system, this has a solver, detector and stage.
		self.system = mrt.system(application_path+config.motorList)
		# Create a new patient, this has room for medical scans and synchrotron scans + other data.
		self.patient = mrt.patient()

		'''
		More GUI linking from System and Patient.
		'''
		# Create controls work environment.
		self.workEnvironment.addWorkspace('Controls',alignment='Right')
		# self.controls = mrt.widgets.controls.controlsPage(parent=self.workEnvironment.stackPage['Controls'])
		self.sbSettings.modeChanged.connect(self.setControlsComplexity)
		self.sbSettings.stageChanged.connect(self.setStage)
		# self.sbSettings.detectorChanged.connect(self.setControlsComplexity)
		self.sbSettings.controls['cbReadOnly'].stateChanged.connect(partial(self.setControlsReadOnly))
		# self.setControlsReadOnly(True)
		self.sbSettings.loadStages(self.system.stageList)
		# self.sbSettings.loadDetectors(self.system.detectorList)

	def testing(self):
		self.openFiles('folder')
		self.patient.xr.plot.plot0.markerAdd(-27.036,45.995)
		self.patient.xr.plot.plot0.markerAdd(32.8665,45.001)
		self.patient.xr.plot.plot0.markerAdd(34.6091,-15.0564)
		self.patient.xr.plot.plot90.markerAdd(-23.2147,46.0205)
		self.patient.xr.plot.plot90.markerAdd(-57.9952,43.4355)
		self.patient.xr.plot.plot90.markerAdd(43.1843,-15.4921)
		self.patient.rtplan.plot[0].plot0.markerAdd(25.527,-27.8264)
		self.patient.rtplan.plot[0].plot0.markerAdd(-29.334,-25.1335)
		self.patient.rtplan.plot[0].plot0.markerAdd(-34.1097,32.0152)
		self.patient.rtplan.plot[0].plot90.markerAdd(-0.3594,-27.2985)
		self.patient.rtplan.plot[0].plot90.markerAdd(-35.9191,-25.8618)
		self.patient.rtplan.plot[0].plot90.markerAdd(63.9358,31.6087)

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

	@QtCore.pyqtSlot(str)
	def setDetector(self,level):
		pass

	@QtCore.pyqtSlot(str)
	def setStage(self,stage):
		self.system.setStage(stage)

	@QtCore.pyqtSlot(bool)
	def enableDoAlignment(self,state=False):
		# self.pps._isStageConnected
		self.sbAlignment.widget['doAlignment'].setEnabled(state)

	def setControlsReadOnly(self,state):
		self.controls.setReadOnly(bool(not state))

	def openFiles(self,modality):
		# We don't do any importing of pixel data in here; that is left up to the plotter by sending the filepath.
		if modality == 'ct':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open CT dataset", "", fileFormat)
			self.openCT(files)

		elif modality == 'xray':
			fileFormat = 'HDF5 (*.hdf5)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open Xray dataset", "", fileFormat)
			self.openXray(files)

		elif modality == 'rtp':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open RP dataset", "", fileFormat)
			self.openRTP(files)

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

			self.workEnvironment.button['CT'].clicked.emit()

	def openXray(self,files):
		'''Open Xray modality files.'''
		# Create new Xray workspace if required.
		if self._isXrayOpen == False:
			self.createWorkEnvironmentXray()
			logging.info('Created Xray Work Environment')

		# Load Xray Dataset.
		self.patient.loadXR(files)
		# Connect Xray plots to workspace.
		self.patient.xr.plot = self.workEnvironment.workspaceWidget['X-RAY']
		# Set maximum markers according to settings.
		self.patient.xr.plot.settings('maxMarkers',config.markerQuantity)
		# Load Xray images into plot areas.
		self.patient.xr.plot.plot0.imageLoad(self.patient.xr.image[0].array,extent=self.patient.xr.image[0].extent,imageIndex=0)
		self.patient.xr.plot.plot90.imageLoad(self.patient.xr.image[0].array,extent=self.patient.xr.image[0].extent,imageIndex=1)
		# Refresh image property tools.
		self.sbXrayProperties.window['histogram'][0].refreshControls()
		self.sbXrayProperties.window['histogram'][1].refreshControls()

		# Finalise import. Set open status to true and open the workspace.
		self._isXrayOpen = True
		self.workEnvironment.button['X-RAY'].clicked.emit()


		# If no xray is open... do stuff.
		# if self._isXrayOpen is False:
			# Add the x-ray workspace.
			# self.workEnvironment.addWorkspace('X-RAY')
			# Load the files.
			# self.patient.loadXR(files)
			# Plot data.
			# self.patient.xr.plot = workspace.plot(self.workEnvironment.stackPage['X-RAY'])
			# self.patient.xr.plot.settings('maxMarkers',config.markerQuantity)
			# Create stack page for xray image properties and populate.
			# self.sbStack.addPage('xrImageProperties')
			# self.sbXrayProperties = sidebar.xrayProperties(self.sbStack.stackDict['xrImageProperties'])
			# self.sbXrayProperties.widget['cbBeamIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='beam'))
			# self.sbXrayProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='patient'))
			# self.sbXrayProperties.widget['cbCentroid'].stateChanged.connect(partial(self.xrayOverlay,overlay='centroid'))
			# Signals and slots.
			# self.sbXrayProperties.widget['alignIsocX'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocX']))
			# self.sbXrayProperties.widget['alignIsocY'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocY']))
			# Set image properties in sidebar to x-ray image properties whenever the workspace is open.
			# self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
			# self.setImagePropertiesStack()
			# Do other stuff.
			# self.sbAlignment.widget['checkXray'].setStyleSheet("color: green")
			# self._isXrayOpen = True

		# elif self._isXrayOpen is True:
			# If an xray is already open, clear the environments and load the new data.
			# self.patient.xr.reloadFiles(files)

		# Set plots.
		# self.patient.xr.plot.plot0.imageLoad(self.patient.xr.image[0].array,extent=self.patient.xr.image[0].extent,imageIndex=0)
		# self.patient.xr.plot.plot90.imageLoad(self.patient.xr.image[1].array,extent=self.patient.xr.image[1].extent,imageIndex=1)
		# self.sbXrayProperties.addPlotWindow(self.sbXrayProperties.window['window'][0],self.patient.xr.plot.plot0)
		# self.sbXrayProperties.addPlotWindow(self.patient.xr.plot.plot0,0)
		# self.sbXrayProperties.addPlotWindow(self.patient.xr.plot.plot90,1)
		# Set to current working environment (in widget stack).
		# self.workEnvironment.button['X-RAY'].clicked.emit()

	def createWorkEnvironmentXray(self):
		# Main Xray plot workspace.
		self.workEnvironment.addWorkspace('X-RAY')
		self.workEnvironment.workspaceWidget['X-RAY'] = workspace.plot(self.workEnvironment.stackPage['X-RAY'])
		# Sidebar page for Xray image properties.
		self.sbStack.addPage('xrImageProperties')
		self.sbXrayProperties = sidebar.xrayProperties(self.sbStack.stackDict['xrImageProperties'])
		# Add windowing controls to sidebar.
		self.sbXrayProperties.addPlotWindow(self.workEnvironment.workspaceWidget['X-RAY'].plot0,0)
		self.sbXrayProperties.addPlotWindow(self.workEnvironment.workspaceWidget['X-RAY'].plot90,1)
		# Connect UI buttons.
		self.sbXrayProperties.widget['cbBeamIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='beam'))
		self.sbXrayProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='patient'))
		self.sbXrayProperties.widget['cbCentroid'].stateChanged.connect(partial(self.xrayOverlay,overlay='centroid'))
		# Connect image properties stack to work environment.
		self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
		self.setImagePropertiesStack()

	def xrayOverlay(self,overlay):
		'''Control x-ray plot overlays.'''
		if overlay == 'beam':
			if self.sbXrayProperties.widget['cbBeamIsoc'].isChecked():
				self.patient.xr.plot.plot0.toggleOverlay(1,state=True)
				self.patient.xr.plot.plot90.toggleOverlay(1,state=True)
			else:
				self.patient.xr.plot.plot0.toggleOverlay(1,state=False)
				self.patient.xr.plot.plot90.toggleOverlay(1,state=False)
		elif overlay == 'patient':
			if self.sbXrayProperties.widget['cbPatIsoc'].isChecked():
				self.patient.xr.plot.plot0.toggleOverlay(2,state=True)
				self.patient.xr.plot.plot90.toggleOverlay(2,state=True)
			else:
				self.patient.xr.plot.plot0.toggleOverlay(2,state=False)
				self.patient.xr.plot.plot90.toggleOverlay(2,state=False)
		elif overlay == 'centroid':
			if self.sbXrayProperties.widget['cbCentroid'].isChecked():
				self.patient.xr.plot.plot0.toggleOverlay(0,state=True)
				self.patient.xr.plot.plot90.toggleOverlay(0,state=True)
			else:
				self.patient.xr.plot.plot0.toggleOverlay(0,state=False)
				self.patient.xr.plot.plot90.toggleOverlay(0,state=False)
		else:
			pass

	def openCT(self,files):
		# Create new CT workspace if required.
		if self._isCTOpen == False:
			self.createWorkEnvironmentCT()
			logging.info('Created CT Work Environment')

		# Load CT Dataset.
		self.patient.loadCT(files)
		# Connect CT plots to workspace.
		self.patient.ct.plot = self.workEnvironment.workspaceWidget['CT']
		# Set maximum markers according to settings.
		self.patient.ct.plot.settings('maxMarkers',config.markerQuantity)
		# Load CT images into plot areas.
		self.patient.ct.plot.plot0.imageLoad(self.patient.ct.image[0].array,extent=self.patient.ct.image[0].extent,imageIndex=0)
		self.patient.ct.plot.plot90.imageLoad(self.patient.ct.image[0].array,extent=self.patient.ct.image[0].extent,imageIndex=1)
		# Refresh image property tools.
		self.sbCTProperties.window['histogram'][0].refreshControls()
		self.sbCTProperties.window['histogram'][1].refreshControls()
		# Enable Isocenter group.
		self.sbCTProperties.group['editIsocenter'].setEnabled(True)
		# Finalise import. Set open status to true and open the workspace.
		self._isCTOpen = True
		self.workEnvironment.button['CT'].clicked.emit()

	def createWorkEnvironmentCT(self):
		# Main CT plot workspace.
		self.workEnvironment.addWorkspace('CT')
		self.workEnvironment.workspaceWidget['CT'] = workspace.plot(self.workEnvironment.stackPage['CT'])
		# Sidebar page for CT image properties.
		self.sbStack.addPage('ctImageProperties')
		self.sbCTProperties = sidebar.ctProperties(self.sbStack.stackDict['ctImageProperties'])
		# Add windowing controls to sidebar.
		self.sbCTProperties.addPlotWindow(self.workEnvironment.workspaceWidget['CT'].plot0,0)
		self.sbCTProperties.addPlotWindow(self.workEnvironment.workspaceWidget['CT'].plot90,1)
		# Connect UI buttons/signals.
		self.sbCTProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.ctOverlay,overlay='patient'))
		self.sbCTProperties.widget['cbCentroid'].stateChanged.connect(partial(self.ctOverlay,overlay='centroid'))
		self.sbCTProperties.isocenterChanged.connect(partial(self.ctUpdateIsocenter))
		# Connect image properties stack to work environment.
		self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
		self.setImagePropertiesStack()

	def ctOverlay(self,overlay):
		'''Control ct plot overlays.'''
		if overlay == 'patient':
			if self.sbCTProperties.widget['cbPatIsoc'].isChecked():
				self.patient.ct.plot.plot0.toggleOverlay(2,state=True)
				self.patient.ct.plot.plot90.toggleOverlay(2,state=True)
			else:
				self.patient.ct.plot.plot0.toggleOverlay(2,state=False)
				self.patient.ct.plot.plot90.toggleOverlay(2,state=False)
		elif overlay == 'centroid':
			if self.sbCTProperties.widget['cbCentroid'].isChecked():
				self.patient.ct.plot.plot0.toggleOverlay(0,state=True)
				self.patient.ct.plot.plot90.toggleOverlay(0,state=True)
			else:
				self.patient.ct.plot.plot0.toggleOverlay(0,state=False)
				self.patient.ct.plot.plot90.toggleOverlay(0,state=False)
		else:
			pass

	def openRTP(self,files):
		'''Open RTP modality files.'''
		# self.rtp.ds = mrt.fileHandler.dicom.importDicom(files,'RTPLAN')
		# Create a work environment in the application.
		self.workEnvironment.addWorkspace('RTPLAN')
		# Load the ct dataset into the patient.
		self.patient.loadRTPLAN(files,self.patient.ct.image[0])

		# Assume single fraction.
		# self.rtp.beam = dicomData.beam		

		self.sbTreatment.widget['quantity'].setText(str(len(self.patient.rtplan.image)))
		# self.property.addSection('RTPLAN DICOM')
		# self.property.addVariable('RTPLAN DICOM','Number of Beams',len(self.rtp.beam))

		self.sbTreatment.populateTreatments()

		# Create a plot list the same length as the amount of images.
		self.patient.rtplan.plot = np.empty(len(self.patient.rtplan.image),dtype=object)
		self.patient.rtplan.guiInterface = np.empty(len(self.patient.rtplan.image),dtype=object)

		# Iterate through each planned beam.
		for i in range(len(self.patient.rtplan.image)):

			# Create stack page for rtplan image properties and populate.
			self.sbStack.addPage('bev%iImageProperties'%(i+1))
			self.workEnvironment.addWorkspace('BEV%i'%(i+1))
			self.patient.rtplan.plot[i] = workspace.plot(self.workEnvironment.stackPage['BEV%i'%(i+1)])
			self.patient.rtplan.plot[i].settings('maxMarkers',config.markerQuantity)
			self.patient.rtplan.guiInterface[i] = sidebar.ctProperties(self.sbStack.stackDict['bev%iImageProperties'%(i+1)])
			self.patient.rtplan.guiInterface[i].widget['cbPatIsoc'].stateChanged.connect(partial(self.rtpOverlay,overlay='patient'))
			self.patient.rtplan.guiInterface[i].widget['cbCentroid'].stateChanged.connect(partial(self.rtpOverlay,overlay='centroid'))

			# self.patient.rtplan.plot[i].arrayExtent = dicomData.beam[i].arrayExtent

			# Plot.
			self.patient.rtplan.plot[i].plot0.imageLoad(self.patient.rtplan.image[i].array,extent=self.patient.rtplan.image[i].extent,imageIndex=0)
			self.patient.rtplan.plot[i].plot90.imageLoad(self.patient.rtplan.image[i].array,extent=self.patient.rtplan.image[i].extent,imageIndex=1)
			# Add plotting windowing tools to sidebar.
			self.patient.rtplan.guiInterface[i].addPlotWindow(self.patient.rtplan.plot[i].plot0,0)
			self.patient.rtplan.guiInterface[i].addPlotWindow(self.patient.rtplan.plot[i].plot90,1)

			# Add isocenters to plots.
			# x1,y1,x2 = self.patient.rtplan.image[i].isocenter
			# mpl_iso = np.array([x2,x1,y1])
			self.patient.rtplan.plot[i].plot0.patientIsocenter = self.patient.rtplan.image[i].isocenter
			self.patient.rtplan.plot[i].plot90.patientIsocenter = self.patient.rtplan.image[i].isocenter

			# Update property table.
			# labels = ['BEV%i'%(i+1),'Gantry Angle','Patient Support Angle','Collimator Angle']
			# values = [self.patient.rtplan.image[i].gantryAngle,self.patient.rtplan.image[i].patientSupportAngle,self.patient.rtplan.image[i].collimatorAngle]
			# self.property.addVariable('RTPLAN DICOM',labels,values)
			# labels = ['BEV%i Isocenter (adjusted)'%(i+1),'x','y','z']
			# values = np.round(self.patient.rtplan.image[i].isocenter,decimals=2).tolist()
			# self.property.addVariable('RTPLAN DICOM',labels,values)

			# Button connections.
			self.sbTreatment.widget['beam'][i]['calculate'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=i))
			self.sbTreatment.widget['beam'][i]['align'].clicked.connect(partial(self.patientApplyAlignment,treatmentIndex=i))
			# Signals and slots.
			# self.patient.rtplan.guiInterface[i].window['pbApply'].clicked.connect(partial(self.updateSettings,'rtplan',self.patient.rtplan.guiInterface[i].window['pbApply'],idx=i))

		# Add rtp isoc to ct.
		self.patient.ct.isocenter = self.patient.rtplan.ctisocenter
		self.patient.ct.plot.plot0.patientIsocenter = self.patient.ct.isocenter
		self.patient.ct.plot.plot90.patientIsocenter = self.patient.ct.isocenter

		self._isRTPOpen = True
		self.workEnvironment.button['RTPLAN'].clicked.emit()

	def rtpOverlay(self,overlay):
		'''Control rtplan plot overlays.'''
		if overlay == 'patient':
			for i in range(len(self.patient.rtplan.guiInterface)):
				if self.patient.rtplan.guiInterface[i].widget['cbPatIsoc'].isChecked():
					self.patient.rtplan.plot[i].plot0.toggleOverlay(2,state=True)
					self.patient.rtplan.plot[i].plot90.toggleOverlay(2,state=True)
				else:
					self.patient.rtplan.plot[i].plot0.toggleOverlay(2,state=False)
					self.patient.rtplan.plot[i].plot90.toggleOverlay(2,state=False)
		elif overlay == 'centroid':
			for i in range(len(self.patient.rtplan.guiInterface)):
				if self.patient.rtplan.guiInterface[i].widget['cbCentroid'].isChecked():
					self.patient.rtplan.plot[i].plot0.toggleOverlay(0,state=True)
					self.patient.rtplan.plot[i].plot90.toggleOverlay(0,state=True)
				else:
					self.patient.rtplan.plot[i].plot0.toggleOverlay(0,state=False)
					self.patient.rtplan.plot[i].plot90.toggleOverlay(0,state=False)
		else:
			pass

	def setImagePropertiesStack(self):
		if self._isXrayOpen:
			if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['X-RAY']) == self.workEnvironment.stack.currentIndex():
				self.sbStack.stackDict['ImageProperties'] = self.sbStack.stackDict['xrImageProperties']
		if self._isCTOpen:
			if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['CT']) == self.workEnvironment.stack.currentIndex():
				self.sbStack.stackDict['ImageProperties'] = self.sbStack.stackDict['ctImageProperties']
		if self._isRTPOpen:
			for i in range(len(self.patient.rtplan.image)):
				if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['BEV%i'%(i+1)]) == self.workEnvironment.stack.currentIndex():
						self.sbStack.stackDict['ImageProperties'] = self.sbStack.stackDict['bev%iImageProperties'%(i+1)]

		# Force refresh.
		if (self.sbSelector.list.currentItem() == self.sbSelector.getListItem('ImageProperties')):
			self.sbStack.setCurrentWidget(self.sbStack.stackDict['ImageProperties'])

	def updateSettings(self,mode,origin,idx=0):
		'''Update variable based of changed data in property model (in some cases, external sources).'''
		if (mode == 'xr') & (self._isXrayOpen):
			'''Update x-ray specific properties.'''
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
				self.patient.xr.plot.setRadiographMode(mode)
				self.patient.xr.plot.setWindows(windows)

		elif (mode == 'ct') & (self._isCTOpen):
			'''Update ct specific properties.'''
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
			'''Update rtplan specific properties.'''
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

		elif mode == 'global':
			'''Update global variables, applicable to all modes.'''
			if origin == self.sbAlignment.widget['maxMarkers']:
				value = self.sbAlignment.widget['maxMarkers'].value()
				# Update settings.
				config.markerQuantity = value
				# Update plot tables.
				if self._isXrayOpen: self.patient.xr.plot.settings('maxMarkers',value)
				if self._isCTOpen: self.patient.ct.plot.settings('maxMarkers',value)
				if self._isRTPOpen: 
					for i in range(len(self.patient.rtplan.plot)):
						self.patient.rtplan.plot[i].settings('maxMarkers',value)

	def toggleOptimise(self,state):
		'''State(bool) tells you whether you should clear the optimisation plots or not.'''
		if state == True:
			pass
		elif state == False:
			try:
				'''Remove X-ray optimised points.'''
				self.xray.plotEnvironment.plot0.markerRemove(marker=-2)
				self.xray.plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass
			try:
				'''Remove X-ray optimised points.'''
				self.patient.ct.plotEnvironment.plot0.markerRemove(marker=-2)
				self.patient.ct.plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass
			try:
				'''Remove X-ray optimised points.'''
				for i in range(len(self.rtp.beam)):
					self.rtp.beam[i].plotEnvironment.plot0.markerRemove(marker=-2)
					self.rtp.beam[i].plotEnvironment.plot90.markerRemove(marker=-2)
			except:
				pass

	def patientCalculateAlignment(self,treatmentIndex=-1):
		'''Send coordinates to algorithm and align.'''
		success = False

		# Check first if we at least have an x-ray plus CT/MRI open.
		if (self._isXrayOpen & (self._isCTOpen|self._isMRIOpen)):
			pass
		else:
			return

		# Do some check to see if Ly and Ry are the same/within a given tolerance?
		# Left is ct
		# Right is xr
		numberOfPoints = self.sbAlignment.widget['maxMarkers'].value()
		l = np.zeros((numberOfPoints,3))
		r = np.zeros((numberOfPoints,3))

		# Plot xyz maps onto synchrotron yzx.

		if treatmentIndex == -1:
			'''Align to CT'''
			if len(self.patient.xr.plot.plot0.pointsX)>0:
				if self.sbAlignment.widget['optimise'].isChecked():
					markerSize = self.sbAlignment.widget['markerSize'].value()
					threshold = self.sbAlignment.widget['threshold'].value()
					'''Optimise points.'''
					self.patient.xr.plot.plot0.markerOptimise(markerSize,threshold)
					self.patient.xr.plot.plot90.markerOptimise(markerSize,threshold)
					self.patient.ct.plot.plot0.markerOptimise(markerSize,threshold)
					self.patient.ct.plot.plot90.markerOptimise(markerSize,threshold)
					# log(self.logFile,"Successfully optimised points.","event")
					# Collect points.
					l[:,1] = self.patient.ct.plot.plot0.pointsXoptimised
					l[:,2] = self.patient.ct.plot.plot0.pointsYoptimised
					l[:,0] = self.patient.ct.plot.plot90.pointsXoptimised
					r[:,1] = self.patient.xr.plot.plot0.pointsXoptimised
					r[:,2] = self.patient.xr.plot.plot0.pointsYoptimised
					r[:,0] = self.patient.xr.plot.plot90.pointsXoptimised
				else:
					'''Do not optimise anything.'''
					l[:,1] = self.patient.ct.plot.plot0.pointsX
					l[:,2] = self.patient.ct.plot.plot0.pointsY
					l[:,0] = self.patient.ct.plot.plot90.pointsX
					r[:,1] = self.patient.xr.plot.plot0.pointsX
					r[:,2] = self.patient.xr.plot.plot0.pointsY
					r[:,0] = self.patient.xr.plot.plot90.pointsX

				# Re-align the points with the synchrotron axes.
				# Use the extent to get the axes directions.
				if (self.patient.ct.image[0].extent[4] < self.patient.ct.image[0].extent[5]):
					xd = 1
				else:
					xd = -1
				if (self.patient.ct.image[0].extent[0] < self.patient.ct.image[0].extent[1]):
					yd = 1
				else:
					yd = -1
				if (self.patient.ct.image[0].extent[2] < self.patient.ct.image[0].extent[3]):
					zd = 1
				else:
					zd = -1
				# Dicom axes are:
				dicomAxes = np.array([xd,yd,zd])
				# Synchrotron axes are fixed:
				synchrotronAxes = np.array([1,-1,1])
				# Divide to get the direction difference.
				changeAxes = dicomAxes/synchrotronAxes

				# Solve.
				self.system.solver.updateVariable(
					left=l,
					right=r,
					patientIsoc=self.patient.ct.isocenter,
					axesDirection=changeAxes)
				self.system.solver.solve()

		# elif treatmentIndex != -1:
		else:
			'''Align to RTPLAN[index]'''
			if len(self.patient.rtplan.plot[treatmentIndex].plot0.pointsX)>0:
				# Optimise Points
				if self.sbAlignment.widget['optimise'].isChecked():
					self.patient.xr.plot.plot0.markerOptimise(self.sbAlignment.widget['markerSize'].value(),threshold)
					self.patient.xr.plot.plot90.markerOptimise(self.sbAlignment.widget['markerSize'].value(),threshold)
					self.patient.rtplan.plot[treatmentIndex].plot0.markerOptimise(self.sbAlignment.widget['markerSize'].value(),threshold)
					self.patient.rtplan.plot[treatmentIndex].plot90.markerOptimise(self.sbAlignment.widget['markerSize'].value(),threshold)
					# log(self.logFile,"Successfully optimised points.","event")
					# Collect points.
					l[:,1] = self.patient.rtplan.plot[treatmentIndex].plot0.pointsXoptimised
					l[:,2] = self.patient.rtplan.plot[treatmentIndex].plot0.pointsYoptimised
					l[:,0] = self.patient.rtplan.plot[treatmentIndex].plot90.pointsXoptimised
					r[:,1] = self.patient.xr.plot.plot0.pointsXoptimised
					r[:,2] = self.patient.xr.plot.plot0.pointsYoptimised
					r[:,0] = self.patient.xr.plot.plot90.pointsXoptimised
				else:
					'''Do not optimise anyting.'''
					l[:,1] = self.patient.rtplan.plot[treatmentIndex].plot0.pointsX
					l[:,2] = self.patient.rtplan.plot[treatmentIndex].plot0.pointsY
					l[:,0] = self.patient.rtplan.plot[treatmentIndex].plot90.pointsX
					r[:,1] = self.patient.xr.plot.plot0.pointsX
					r[:,2] = self.patient.xr.plot.plot0.pointsY
					r[:,0] = self.patient.xr.plot.plot90.pointsX

				success = True

			# Calcualte alignment requirement
			if success:
				# Re-align the points with the synchrotron axes.
				# Use the extent to get the axes directions.
				if (self.patient.rtplan.image[treatmentIndex].extent[4] < self.patient.rtplan.image[treatmentIndex].extent[5]):
					xd = 1
				else:
					xd = -1
				if (self.patient.rtplan.image[treatmentIndex].extent[0] < self.patient.rtplan.image[treatmentIndex].extent[1]):
					yd = 1
				else:
					yd = -1
				if (self.patient.rtplan.image[treatmentIndex].extent[2] < self.patient.rtplan.image[treatmentIndex].extent[3]):
					zd = 1
				else:
					zd = -1
				# Dicom axes are:
				# np.sign(self.patient.rtplan.image[treatmentIndex].pixelSize)
				dicomAxes = np.array([xd,yd,zd])
				# Synchrotron axes are fixed:
				synchrotronAxes = np.array([1,-1,1])
				# Divide to get the direction difference.
				changeAxes = dicomAxes/synchrotronAxes
				# Solve.
				self.system.solver.updateVariable(
					left=l,
					right=r,
					patientIsoc=self.patient.rtplan.image[treatmentIndex].isocenter,
					axesDirection=changeAxes)
				self.system.solver.solve()

				# Update centroids.
				self.patient.rtplan.plot[treatmentIndex].plot0.ctd = self.system.solver._leftCentroid
				self.patient.rtplan.plot[treatmentIndex].plot90.ctd = self.system.solver._leftCentroid
				# Update x-ray patient isocenter.
				temp = self.system.solver._syncPatientIsocenter
				# Convert back to x1,y1,x2 plot.
				_syncPatientIsocenter = np.array([temp[1],temp[2],temp[0]])
				self.patient.xr.plot.plot0.patientIsocenter = _syncPatientIsocenter
				self.patient.xr.plot.plot90.patientIsocenter = _syncPatientIsocenter

		# Update x-ray centroid position.
		self.patient.xr.plot.plot0.ctd = self.system.solver._rightCentroid
		self.patient.xr.plot.plot90.ctd = self.system.solver._rightCentroid

		# Update ct centroid position.
		self.patient.ct.plot.plot0.ctd = self.system.solver._leftCentroid
		self.patient.ct.plot.plot90.ctd = self.system.solver._leftCentroid

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(self.system.solver.solution[3]),float(self.system.solver.solution[4]),float(self.system.solver.solution[5])])
		self.property.updateVariable('Alignment',['Translation','x','y','z'],[float(self.system.solver.solution[0]),float(self.system.solver.solution[1]),float(self.system.solver.solution[2])])
		self.property.updateVariable('Alignment','Scale',float(self.system.solver.scale))

		# # Calculate alignment for stage.
		# self.system.calculateAlignment()

	def patientApplyAlignment(self,treatmentIndex=-1):
		'''Calculate alignment first.'''
		self.patientCalculateAlignment(treatmentIndex=treatmentIndex)

		# Calculate alignment for stage.
		self.system.calculateAlignment()
		print('in mrt app, system motion is:',self.system.stage._motion)

		# Apply alignment.
		# self.system.applyAlignment()
		print('mrtapp.py Line 784: commented out alignment')

		# completion = self.system.movePatient(self.system.solver.solution)
		# print('This should be updating the values as they move and reduce to zero.')
		# self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(completion[3]),float(completion[4]),float(completion[5])])
		# self.property.updateVariable('Alignment',['Translation','x','y','z'],[float(completion[0]),float(completion[1]),float(completion[2])])

	# def eventFilter(self, source, event):
	# 	# Update ct and xr points in the table as the widget is clicked.
	# 	if event.type() == QtCore.QEvent.MouseButtonRelease:
	# 		self.updateMarkerTable()
	# 	else:
	# 		pass

	# 	return QtWidgets.QMainWindow.eventFilter(self, source, event)

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())