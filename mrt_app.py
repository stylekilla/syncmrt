import config as cfg
from classBin import *
from sidebar import *
# As normal...
import os
import sys
from functools import partial
import numpy as np
# Pyqt5
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtGui, QtWidgets, uic
# SyncMRT Tools.
import syncmrt as mrt
# Select Qt5 user interface.
qtCreatorFile = "main.ui"
qtStyleSheet = open("stylesheet.css")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

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
		self.sidebarStack = sidebarStack(self.frameSidebarStack)
		self.sidebarList = sidebarList(self.widgetSidebarList)
		self.sidebarSelector = sidebarSelector(self.sidebarList,self.sidebarStack)

		# Add alignment section to sidebar (list+stack).
		self.sidebarSelector.addPage('Alignment',before='all')
		self.sbAlignment = sbAlignment(self.sidebarStack.stackDict['Alignment'])
		self.sbAlignment.widget['maxMarkers'].setValue(3)
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		self.sbAlignment.widget['calcAlignment'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=-1))
		self.sbAlignment.widget['doAlignment'].clicked.connect(partial(self.patientApplyAlignment,treatmentIndex=-1))
		self.sbAlignment.widget['optimise'].toggled.connect(partial(self.toggleOptimise))

		# Add treatment section to sidebar.
		self.sidebarSelector.addPage('Treatment',after='Alignment')
		self.sbTreatment = sbTreatment(self.sidebarStack.stackDict['Treatment'])

		# Add image properties section to sidebar.
		self.sidebarSelector.addPage('ImageProperties',after='Treatment')

		# Add settings section to sidebar.
		self.sidebarSelector.addPage('Settings',after='all')
		self.sbSettings = sbSettings(self.sidebarStack.stackDict['Settings'])

		# Create work environment
		self.workEnvironment = workEnvironment(self.toolbarPane,self.workStack)

		# Create patient alignment machine.
		# self.pps = mrt.imageGuidance.patientPositioningSystem.newSystem()
		# self.pps.stageConnected.connect(partial(self.enableDoAlignment))

		# Create controls work environment.
		self.workEnvironment.addWorkspace('Controls',alignment='Right')
		self.controls = mrt.tools.epics.controls.controlsPage(parent=self.workEnvironment.stackPage['Controls'])
		self.sbSettings.modeChanged.connect(self.setControlsComplexity)
		self.sbSettings.stageChanged.connect(self.setStage)
		# self.sbSettings.detectorChanged.connect(self.setControlsComplexity)
		self.sbSettings.controls['cbReadOnly'].stateChanged.connect(partial(self.setControlsReadOnly))
		self.setControlsReadOnly(True)
		self.sbSettings.loadStages(self.controls.stageList)
		self.sbSettings.loadDetectors(self.controls.detectorList)

		# PropertyManager
		self.property = propertyModel()
		self.propertyTree = propertyManager(self.frameVariablePane,self.property)

		# Collapsing button for Property Manager.
		icon = QtGui.QIcon('resources/CollapseRight.png')
		icon.pixmap(20,20)
		self.pbCollapseProperties = QtWidgets.QPushButton(icon,'')
		self.pbCollapseProperties.setFlat(True)
		self.statusBar.addPermanentWidget(self.pbCollapseProperties)
		self.pbCollapseProperties.clicked.connect(partial(self.propertyTree.toggleFrame,self.frameVariablePane))

		# Temporarily turn off the stacked widget at the bottom.
		self.stackedWidget.setEnabled(False)
		self.stackedWidget.setVisible(False)

		# Create a ct/mri/xray structure class.
		# self.patient.ct = mrt.fileHandler.dataDicom()
		# self.xray = mrt.fileHandler.dataXray()
		# self.mri = mrt.fileHandler.dataDicom()
		# self.rtp = mrt.fileHandler.dataRtp()

		# Create alignment table.
		self.property.addSection('Alignment')
		self.property.addVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment',['Translation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment','Scale',0)
		self.propertyTree.expandAll()
		
		# Create initial zero alignment solution result.
		# self.alignmentSolution = mrt.imageGuidance.affineTransform(0,0)

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
		self.system = mrt.system()
		# Create a new patient, this has room for medical scans and synchrotron scans + other data.
		self.patient = mrt.patient()

	def testing(self):
		xrayfiles = ['/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/xray0deg-inverted.npy', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/xray90deg-inverted.npy']
		self.openXray(xrayfiles)
		ctfiles = ['/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.1.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.2.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.3.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.4.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.5.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.6.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.7.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.8.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.9.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.10.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.11.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.12.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.13.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.14.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.15.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.16.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.17.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.18.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.19.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.20.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.21.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.22.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.23.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.24.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.25.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.26.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.27.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.28.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.29.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.30.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.31.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.32.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.33.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.34.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.35.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.36.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.37.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.38.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.39.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.40.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.41.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.42.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.43.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.44.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.45.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.46.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.47.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.48.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.49.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.50.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.51.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.52.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.53.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.54.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.55.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.56.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.57.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.58.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.59.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.60.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.61.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.62.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.63.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.64.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.65.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.66.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.67.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.68.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.69.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.70.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.71.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.72.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.73.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.74.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.75.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.76.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.77.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.78.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.79.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.80.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.81.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.82.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.83.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.84.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.85.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.86.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.87.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.88.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.89.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.90.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.91.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.92.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.93.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.94.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.95.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.96.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.97.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.98.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.99.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.100.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.101.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.102.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.103.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.104.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.105.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.106.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.107.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.108.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.109.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.110.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.111.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.112.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.113.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.114.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.115.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.116.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.117.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.118.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.119.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.120.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.121.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.122.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.123.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.124.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.125.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.126.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.127.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.128.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.129.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.130.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.131.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.132.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.133.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.134.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.135.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.136.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.137.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.138.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.139.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.140.dcm', '/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/CT.1.2.840.113619.2.278.3.380434001.45.1470083911.126.141.dcm']
		self.openCT(ctfiles,skipGPU=True,skipGPUfiles='/Users/micahbarnes/OneDrive/University/MR233 Health and Medical Physics/Research/Image Alignment/python/mrt_app/test/ct1_correctlyOrientated.npy')
		self.xray.plotEnvironment.plot0.markerAdd(12.37,-4.02)
		self.xray.plotEnvironment.plot0.markerAdd(7.88,-23.00)
		self.xray.plotEnvironment.plot0.markerAdd(21.17,-44.38)
		self.xray.plotEnvironment.plot90.markerAdd(-34.25,-4.02)
		self.xray.plotEnvironment.plot90.markerAdd(2.35,-23.00)
		self.xray.plotEnvironment.plot90.markerAdd(-5.38,-44.38)
		self.patient.ct.plotEnvironment.plot0.markerAdd(-1.03,-26.02)
		self.patient.ct.plotEnvironment.plot0.markerAdd(9.10,-43.64)
		self.patient.ct.plotEnvironment.plot0.markerAdd(18.17,-65.51)
		self.patient.ct.plotEnvironment.plot90.markerAdd(9.32,-26.02)
		self.patient.ct.plotEnvironment.plot90.markerAdd(-25.45,-43.64)
		self.patient.ct.plotEnvironment.plot90.markerAdd(-13.29,-65.51)

	@QtCore.pyqtSlot(str)
	def setControlsComplexity(self,level):
		self.controls.setLevel(level)

	@QtCore.pyqtSlot(str)
	def setDetector(self,level):
		pass

	@QtCore.pyqtSlot(str)
	def setStage(self,stage):
		self.controls.setStage(stage)
		try:
			self.pps.connectMotors(self.controls.patient)
			self.pps.setStageConnected(True)
		except:
			pass	

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

			print('xray files',files)
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
		# If no xray is open... do stuff.
		if self._isXrayOpen is False:
			# Add the x-ray workspace.
			self.workEnvironment.addWorkspace('X-RAY')

			# Load the files.
			self.patient.loadXR(files)
			print('Freshly loaded in MRTAPP')
			print(self.patient.xr.image[0])

			# Create stack page for xray image properties and populate.
			self.sidebarStack.addPage('xrImageProperties')
			self.sbXrayProperties = sbXrayProperties(self.sidebarStack.stackDict['xrImageProperties'])
			self.sbXrayProperties.widget['cbBeamIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='beam'))
			self.sbXrayProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='patient'))
			self.sbXrayProperties.widget['cbCentroid'].stateChanged.connect(partial(self.xrayOverlay,overlay='centroid'))

			# Link to environment
			
			# self.sbXrayProperties.widget['alignIsocX'].setText(str(cfg.hamamatsuAlignmentIsoc[1]))
			# self.sbXrayProperties.widget['alignIsocY'].setText(str(cfg.hamamatsuAlignmentIsoc[2]))

			# Add property variables.
			# self.property.addSection('X-Ray')
			# self.property.addVariable('X-Ray',['Pixel Size','x','y'],self.patient.xr.imagePixelSize.tolist())
			# self.property.addVariable('X-Ray','Patient Orientation',self.xr.patientOrientation)
			# self.property.addVariable('X-Ray',['Alignment Isocenter','x','y'],self.xr.alignmentIsoc[-2:].tolist())

			# Connect changes to updates in settings.
			# self.property.itemChanged.connect(self.updateSettings)

			# imageFiles = mrt.fileHandler.importImage(self.xr.fp,'xray','npy')
			# self.xr.arrayNormal = imageFiles[0]
			# self.xr.arrayOrthogonal = imageFiles[1]
			# self.xr.imageSize = np.load(imageFiles[0]).shape[::-1]
			# self.xrayCalculateExtent(update=False)

			# Plot data.
			self.patient.xr.plot = plotEnvironment(self.workEnvironment.stackPage['X-RAY'])
			self.patient.xr.plot.settings('maxMarkers',cfg.markerQuantity)

			# item = self..findItems('ImageProperties',QtCore.Qt.MatchExactly)[0]
			# print(item)
			# self.xr.plotEnvironment.nav0.actionImageSettings.triggered.connect(partial(self.toolSelect.showToolExternalTrigger,item))

			# Signals and slots.
			self.sbXrayProperties.widget['alignIsocX'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocX']))
			self.sbXrayProperties.widget['alignIsocY'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocY']))
			self.sbXrayProperties.window['pbApply'].clicked.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.window['pbApply']))

			# Set image properties in sidebar to x-ray image properties whenever the workspace is open.
			self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
			self.setImagePropertiesStack()

			self.sbAlignment.widget['checkXray'].setStyleSheet("color: green")
			self._isXrayOpen = True

		elif self._isXrayOpen is True:
			self.patient.xr.reloadFiles(files)

		print('Xray Image Array')
		print(self.patient.xr.image[0])

		# Set plots.
		self.patient.xr.plot.plot0.imageLoad(self.patient.xr.image[0].array,extent=self.patient.xr.image[0].extent,imageIndex=0)
		self.patient.xr.plot.plot90.imageLoad(self.patient.xr.image[0].array,extent=self.patient.xr.image[0].extent,imageIndex=1)

		# Set to current working environment (in widget stack).
		self.workEnvironment.button['X-RAY'].clicked.emit()

	def xrayOverlay(self,overlay):
		'''Control x-ray plot overlays.'''
		if overlay == 'beam':
			if self.sbXrayProperties.widget['cbBeamIsoc'].isChecked():
				self.xr.plotEnvironment.plot0.overlayIsocenter(state=True)
				self.xr.plotEnvironment.plot90.overlayIsocenter(state=True)
			else:
				self.xr.plotEnvironment.plot0.overlayIsocenter(state=False)
				self.xr.plotEnvironment.plot90.overlayIsocenter(state=False)
		elif overlay == 'patient':
			pass
		elif overlay == 'centroid':
			if self.sbXrayProperties.widget['cbCentroid'].isChecked():
				self.xr.plotEnvironment.plot0.overlayCentroid(state=True)
				self.xr.plotEnvironment.plot90.overlayCentroid(state=True)
			else:
				self.xr.plotEnvironment.plot0.overlayCentroid(state=False)
				self.xr.plotEnvironment.plot90.overlayCentroid(state=False)
		else:
			pass

	# def xrayCalculateExtent(self,update=True):
	# 	'''Should umbrella all this under an x-ray class.'''
	# 	# Force update of alignment isocenter from settings.
	# 	self.xray.alignmentIsoc = cfg.hamamatsuAlignmentIsoc

	# 	# Synchrotron image geometry is vec directions (xyz), note reversed direction of y for looking downstream.
	# 	self.xray.imageAxes = np.array([1,-1,1])

	# 	# Set extent for plotting. This is essentially the IMBL coordinate system according to the detector.
	# 	left = (0-self.xray.alignmentIsoc[0])*self.xray.imagePixelSize[0]*self.xray.imageAxes[1]
	# 	right = left+(self.xray.imageSize[0]*self.xray.imagePixelSize[0]*self.xray.imageAxes[1])
	# 	top = (0+self.xray.alignmentIsoc[1])*self.xray.imagePixelSize[1]*self.xray.imageAxes[2]
	# 	bottom = top-(self.xray.imageSize[1]*self.xray.imagePixelSize[1]*self.xray.imageAxes[2])
	# 	self.xray.arrayExtentNormal = np.array([left,right,bottom,top])

	# 	left = (0-self.xray.alignmentIsoc[0])*self.xray.imagePixelSize[0]*self.xray.imageAxes[0]
	# 	right = left+(self.xray.imageSize[0]*self.xray.imagePixelSize[0]*self.xray.imageAxes[0])
	# 	top = (0+self.xray.alignmentIsoc[1])*self.xray.imagePixelSize[1]*self.xray.imageAxes[2]
	# 	bottom = top-(self.xray.imageSize[1]*self.xray.imagePixelSize[1]*self.xray.imageAxes[2])
	# 	self.xray.arrayExtentOrthogonal = np.array([left,right,bottom,top])

	# 	if update is True:
	# 		# Force re-draw on plots.
	# 		# self.xray.plotEnvironment.plot0.extent = self.xray.arrayExtentNormal
	# 		# self.xray.plotEnvironment.plot90.extent = self.xray.arrayExtentOrthogonal
	# 		# self.xray.plotEnvironment.plot0.image.set_extent(self.xray.arrayExtentNormal)
	# 		# self.xray.plotEnvironment.plot90.image.set_extent(self.xray.arrayExtentOrthogonal)
	# 		self.xray.plotEnvironment.plot0.setExtent(self.xray.arrayExtentNormal)
	# 		self.xray.plotEnvironment.plot90.setExtent(self.xray.arrayExtentOrthogonal)
	# 		self.xray.plotEnvironment.plot0.canvas.draw()
	# 		self.xray.plotEnvironment.plot90.canvas.draw()

	def openCT(self,files,skipGPU=False,skipGPUfiles=''):
		'''Open CT modality files.'''
		# self.patient.ct.ds = mrt.fileHandler.dicom.importDicom(files,'CT')
		# Create a work environment in the application.
		self.workEnvironment.addWorkspace('CT')
		# Load the ct dataset into the patient.
		self.patient.loadCT(files)

		# Create stack page for xray image properties and populate.
		self.sidebarStack.addPage('ctImageProperties')
		self.sbCTProperties = sbCTProperties(self.sidebarStack.stackDict['ctImageProperties'])
		self.sbCTProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.ctOverlay,overlay='patient'))
		self.sbCTProperties.widget['cbCentroid'].stateChanged.connect(partial(self.ctOverlay,overlay='centroid'))

		# Update property table.
		# self.property.addSection('CT')
		# self.property.addVariable('CT',['Pixel Size','x','y'],self.patient.ct.pixelSize[:2].tolist())
		# self.property.addVariable('CT','Slice Thickness',float(self.patient.ct.pixelSize[2]))
		# self.property.addVariable('CT','Patient Position',self.patient.ct.patientPosition)

		# Import numpy files.
		# imageFiles = mrt.fileHandler.importImage(self.patient.ct.fp,'ct','npy')
		# self.patient.ct.arrayDicom = imageFiles[0]
		# self.patient.ct.array = imageFiles[1]

		# Plot data.
		self.patient.ct.plot = plotEnvironment(self.workEnvironment.stackPage['CT'])
		self.patient.ct.plot.settings('maxMarkers',cfg.markerQuantity)
		self.patient.ct.plot.plot0.imageLoad(self.patient.ct.image[0].array,extent=self.patient.ct.image[0].extent,imageIndex=0)
		self.patient.ct.plot.plot90.imageLoad(self.patient.ct.image[0].array,extent=self.patient.ct.image[0].extent,imageIndex=1)

		# Signals and slots.
		self.sbCTProperties.window['pbApply'].clicked.connect(partial(self.updateSettings,'ct',self.sbCTProperties.window['pbApply']))

		# Last checklist items.
		self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
		self.setImagePropertiesStack()

		# Set open switch to true and open the workspace (also sets the image properties stack?).
		self._isCTOpen = True
		self.sbAlignment.widget['checkDicom'].setStyleSheet("color: green")
		self.workEnvironment.button['CT'].clicked.emit()

	def ctOverlay(self,overlay):
		'''Control ct plot overlays.'''
		if overlay == 'patient':
			pass
		elif overlay == 'centroid':
			print('in overlay ctd')
			if self.sbCTProperties.widget['cbCentroid'].isChecked():
				print('adding overlay')
				self.patient.ct.plot.plot0.overlayCentroid(state=True)
				self.patient.ct.plot.plot90.overlayCentroid(state=True)
			else:
				self.patient.ct.plot.plot0.overlayCentroid(state=False)
				self.patient.ct.plot.plot90.overlayCentroid(state=False)
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

			# Create stack page for xray image properties and populate.
			self.sidebarStack.addPage('bev%iImageProperties'%(i+1))

			self.workEnvironment.addWorkspace('BEV%i'%(i+1))
			self.patient.rtplan.plot[i] = plotEnvironment(self.workEnvironment.stackPage['BEV%i'%(i+1)])
			self.patient.rtplan.guiInterface[i] = sbCTProperties(self.sidebarStack.stackDict['bev%iImageProperties'%(i+1)])
			self.patient.rtplan.plot[i].plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['BEV%i'%(i+1)])
			self.patient.rtplan.plot[i].plotEnvironment.settings('maxMarkers',cfg.markerQuantity)
			# self.patient.rtplan.plot[i].arrayExtent = dicomData.beam[i].arrayExtent

			# Plot.
			self.patient.rtplan.plot[i].plot0.imageLoad(self.patient.rtplan.image[i].array,extent=self.patient.rtplan.image[i].extent,imageIndex=0)
			self.patient.rtplan.plot[i].plot90.imageLoad(self.patient.rtplan.image[i].array,extent=self.patient.rtplan.image[i].extent,imageIndex=1)

			# Update property table.
			# labels = ['BEV%i'%(i+1),'Gantry Angle','Patient Support Angle','Collimator Angle']
			# values = [self.patient.rtplan.image[i].gantryAngle,self.patient.rtplan.image[i].patientSupportAngle,self.patient.rtplan.image[i].collimatorAngle]
			# self.property.addVariable('RTPLAN DICOM',labels,values)
			# labels = ['BEV%i Isocenter (adjusted)'%(i+1),'x','y','z']
			# values = np.round(self.patient.rtplan.image[i].isocenter,decimals=2).tolist()
			# self.property.addVariable('RTPLAN DICOM',labels,values)

			# Button connections.
			self.sbTreatment.widget['beam'][i]['calculate'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=i))
			self.sbTreatment.widget['beam'][i]['align'].clicked.connect(self.patientApplyAlignment)

		self._isRTPOpen = True
		self.workEnvironment.button['RTPLAN'].clicked.emit()

	def setImagePropertiesStack(self):
		if self._isXrayOpen:
			if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['X-RAY']) == self.workEnvironment.stack.currentIndex():
				self.sidebarStack.stackDict['ImageProperties'] = self.sidebarStack.stackDict['xrImageProperties']
		if self._isCTOpen:
			if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['CT']) == self.workEnvironment.stack.currentIndex():
				self.sidebarStack.stackDict['ImageProperties'] = self.sidebarStack.stackDict['ctImageProperties']
		if self._isRTPOpen:
			for i in range(len(self.patient.rtplan.image)):
				if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['BEV%i'%(i+1)]) == self.workEnvironment.stack.currentIndex():
						self.sidebarStack.stackDict['ImageProperties'] = self.sidebarStack.stackDict['bev%iImageProperties'%(i+1)]

		# Force refresh.
		if (self.sidebarSelector.list.currentItem() == self.sidebarSelector.getListItem('ImageProperties')):
			self.sidebarStack.setCurrentWidget(self.sidebarStack.stackDict['ImageProperties'])

	def updateSettings(self,mode,origin):
		'''Update variable based of changed data in property model (in some cases, external sources).'''
		if (mode == 'xr') & (self._isXrayOpen):
			'''Update x-ray specific properties.'''
			if origin == self.sbXrayProperties.widget['alignIsocY']:
				# Overwrite the alignment isoc in settings.
				# cfg.hamamatsuAlignmentIsoc[:2] = origin.text()
				cfg.hamamatsuAlignmentIsoc[0] = origin.text()
				cfg.hamamatsuAlignmentIsoc[2] = origin.text()
				# Update the property variables.
				item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['y'])
				item.setData(origin.text(),QtCore.Qt.DisplayRole)
				# Re-calculate the extent.
				self.xrayCalculateExtent()
			elif origin == self.sbXrayProperties.widget['alignIsocX']:
				# Overwrite the alignment isoc in settings.
				# cfg.hamamatsuAlignmentIsoc[2] = origin.text()
				cfg.hamamatsuAlignmentIsoc[1] = origin.text()
				# Update the property variables.
				item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['x'])
				item.setData(origin.text(),QtCore.Qt.DisplayRole)
				# Re-calculate the extent.
				self.xrayCalculateExtent()
			elif origin == self.sbXrayProperties.window['pbApply']:
				# Must be in radiograph mode.
				mode = 'radiograph'
				# Get the windows and apply them.
				windows = self.sbXrayProperties.getWindows()
				self.patient.xr.plotEnvironment.setRadiographMode(mode)
				self.patient.xr.plotEnvironment.setWindows(windows)

		elif (mode == 'ct') & (self._isCTOpen):
			'''Update ct specific properties.'''
			if origin == self.sbCTProperties.window['pbApply']:
				# Check mode type.
				if self.sbCTProperties.window['rbMax'].isChecked():
					mode = 'max'
				else:
					mode = 'sum'
				# Get windows and apply them.
				windows = self.sbCTProperties.getWindows(self.patient.ct.rescaleSlope,self.patient.ct.rescaleIntercept)
				self.patient.ct.plotEnvironment.setRadiographMode(mode)
				self.patient.ct.plotEnvironment.setWindows(windows)

		elif mode == 'global':
			'''Update global variables, applicable to all modes.'''
			if origin == self.sbAlignment.widget['maxMarkers']:
				value = self.sbAlignment.widget['maxMarkers'].value()
				# Update settings.
				cfg.markerQuantity = value
				# Update plot tables.
				if self._isXrayOpen: self.patient.xr.plotEnvironment.settings('maxMarkers',value)
				if self._isCTOpen: self.patient.ct.plotEnvironment.settings('maxMarkers',value)
				if self._isRTPOpen: 
					for i in range(len(self.rtp.beam)):
						self.rtp.beam[i].plotEnvironment.settings('maxMarkers',value)

		# else:
		# 	# If not from an existing widget, it then must originate from the table.
		# 	try:
		# 		index = self.property.indexFromItem(origin)

		# 		if index == self.property.index['X-Ray']['Alignment Isocenter']['x']:
		# 			cfg.hamamatsuAlignmentIsoc[:2] = self.property.data(index)
		# 			self.sbSettings.widget['alignIsocX'].setText(str(self.property.data(index)))
		# 			self.xray.alignmentIsoc = cfg.hamamatsuAlignmentIsoc
		# 		elif index == self.property.index['X-Ray']['Alignment Isocenter']['y']:
		# 			cfg.hamamatsuAlignmentIsoc[2] = self.property.data(index)
		# 			self.sbSettings.widget['alignIsocY'].setText(str(self.property.data(index)))
		# 			self.xray.alignmentIsoc = cfg.hamamatsuAlignmentIsoc
		# 	except:
		# 		pass

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
		left = np.zeros((numberOfPoints,3))
		right = np.zeros((numberOfPoints,3))

		# Plot xyz maps onto synchrotron yzx.

		if treatmentIndex == -1:
			'''Align to CT'''
			if len(self.xray.plotEnvironment.plot0.pointsX)>0:
				if self.sbAlignment.widget['optimise'].isChecked():
					markerSize = self.sbAlignment.widget['markerSize'].value()
					threshold = self.sbAlignment.widget['threshold'].value()
					'''Optimise points.'''
					self.xray.plotEnvironment.plot0.markerOptimise(markerSize,threshold)
					self.xray.plotEnvironment.plot90.markerOptimise(markerSize,threshold)
					self.patient.ct.plotEnvironment.plot0.markerOptimise(markerSize,threshold)
					self.patient.ct.plotEnvironment.plot90.markerOptimise(markerSize,threshold)
					# log(self.logFile,"Successfully optimised points.","event")
					# Collect points.
					left[:,1] = self.patient.ct.plotEnvironment.plot0.pointsXoptimised
					left[:,2] = self.patient.ct.plotEnvironment.plot0.pointsYoptimised
					left[:,0] = self.patient.ct.plotEnvironment.plot90.pointsXoptimised
					right[:,1] = self.xray.plotEnvironment.plot0.pointsXoptimised
					right[:,2] = self.xray.plotEnvironment.plot0.pointsYoptimised
					right[:,0] = self.xray.plotEnvironment.plot90.pointsXoptimised
				else:
					'''Do not optimise anything.'''
					left[:,1] = self.patient.ct.plotEnvironment.plot0.pointsX
					left[:,2] = self.patient.ct.plotEnvironment.plot0.pointsY
					left[:,0] = self.patient.ct.plotEnvironment.plot90.pointsX
					right[:,1] = self.xray.plotEnvironment.plot0.pointsX
					right[:,2] = self.xray.plotEnvironment.plot0.pointsY
					right[:,0] = self.xray.plotEnvironment.plot90.pointsX

				# Align to the CT assuming that the rtp isoc is zero.
				self.alignmentSolution = mrt.imageGuidance.affineTransform(left,right)

				# Update ct centroid position.
				self.patient.ct.plotEnvironment.plot0.ctd = [self.alignmentSolution.ct_ctd[0],self.alignmentSolution.ct_ctd[1]]
				self.patient.ct.plotEnvironment.plot90.ctd = [self.alignmentSolution.ct_ctd[2],self.alignmentSolution.ct_ctd[1]]

		elif treatmentIndex != -1:
			'''Align to RTPLAN[index]'''
			if len(self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsX)>0:
				# Optimise Points
				if self.toolSelect.alignment['optimise'].isChecked():
					self.xray.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value(),threshold)
					self.xray.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value(),threshold)
					self.rtp.beam[treatmentIndex].plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value(),threshold)
					self.rtp.beam[treatmentIndex].plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value(),threshold)
					# log(self.logFile,"Successfully optimised points.","event")
					# Collect points.
					left[:,1] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsXoptimised
					left[:,2] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsYoptimised
					left[:,0] = self.rtp.beam[treatmentIndex].plotEnvironment.plot90.pointsXoptimised
					right[:,1] = self.xray.plotEnvironment.plot0.pointsXoptimised
					right[:,2] = self.xray.plotEnvironment.plot0.pointsYoptimised
					right[:,0] = self.xray.plotEnvironment.plot90.pointsXoptimised
				else:
					'''Do not optimise anyting.'''
					left[:,1] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsX
					left[:,2] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsY
					left[:,0] = self.rtp.beam[treatmentIndex].plotEnvironment.plot90.pointsX
					right[:,1] = self.xray.plotEnvironment.plot0.pointsX
					right[:,2] = self.xray.plotEnvironment.plot0.pointsY
					right[:,0] = self.xray.plotEnvironment.plot90.pointsX

				success = True

			# Calcualte alignment requirement
			if success:
				# self.alignmentSolution = mrt.imageGuidance.affineTransform(left,right,
				# 	self.rtp.beam[treatmentIndex].isocenter,
				# 	self.patient.ct.userOrigin,
				# 	self.xray.alignmentIsoc)
				self.alignmentSolution = mrt.imageGuidance.affineTransform(left,right)

		else:
			pass

		# Update x-ray centroid position.
		self.xray.plotEnvironment.plot0.ctd = [self.alignmentSolution.synch_ctd[1],self.alignmentSolution.synch_ctd[2]]
		self.xray.plotEnvironment.plot90.ctd = [self.alignmentSolution.synch_ctd[0],self.alignmentSolution.synch_ctd[2]]

		# Update x-ray centroid position.
		self.patient.ct.plotEnvironment.plot0.ctd = [self.alignmentSolution.ct_ctd[1],self.alignmentSolution.ct_ctd[2]]
		self.patient.ct.plotEnvironment.plot90.ctd = [self.alignmentSolution.ct_ctd[0],self.alignmentSolution.ct_ctd[2]]

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(self.alignmentSolution.rotation[0]),float(self.alignmentSolution.rotation[1]),float(self.alignmentSolution.rotation[2])])
		self.property.updateVariable('Alignment',['Translation','x','y','z'],self.alignmentSolution.translation.tolist())
		self.property.updateVariable('Alignment','Scale',float(self.alignmentSolution.scale))

	def patientApplyAlignment(self,treatmentIndex=-1):
		'''Calculate alignment first.'''
		self.patientCalculateAlignment(treatmentIndex=treatmentIndex)

		# Apply alignment.
		if self.pps._isStageConnected:
			completion = self.pps.movePatient(np.concatenate((self.alignmentSolution.translation,self.alignmentSolution.rotation)))
			self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(completion[3]),float(completion[4]),float(completion[5])])
			self.property.updateVariable('Alignment',['Translation','x','y','z'],[float(completion[0]),float(completion[1]),float(completion[2])])


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