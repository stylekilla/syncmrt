 # File is dependent on gv.py
from settings import globalVariables as gv
gv = gv()
from classBin import *
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

		# Sidebar panels
		self.sidebarStack = sidebarStack(self.widgetSidebarStack)
		self.sidebarList = sidebarList(self.widgetSidebarList)
		self.sidebarSelector = sidebarSelector(self.sidebarList,self.sidebarStack)

		# Add alignment section to sidebar (list+stack).
		self.sidebarSelector.addPage('Alignment',before='all')
		self.sbAlignment = sbAlignment(self.sidebarStack.stackDict['Alignment'])
		self.sbAlignment.widget['maxMarkers'].setValue(3)
		self.sbAlignment.widget['maxMarkers'].valueChanged.connect(partial(self.updateSettings,'global',self.sbAlignment.widget['maxMarkers']))
		self.sbAlignment.widget['align'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=-1))
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

		# Create controls work environment.
		self.workEnvironment.addWorkspace('Controls')
		self.controls = mrt.tools.epics.controls.controlsPage(parent=self.workEnvironment.stackPage['Controls'])
		self.controls.addMotor('DynMRT','ROTATE V')

		# PropertyManager
		self.property = propertyModel()
		self.propertyTree = propertyManager(self.variableWidget,self.property)

		# Create a ct/mri/xray structure class.
		self.ct = mrt.fileHandler.dataDicom()
		self.xray = mrt.fileHandler.dataXray()
		self.mri = mrt.fileHandler.dataDicom()
		self.rtp = mrt.fileHandler.dataRtp()

		# Create alignment table.
		self.property.addSection('Alignment')
		self.property.addVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment',['Translation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment','Scale',0)
		# Create initial zero alignment solution result.
		self.alignmentSolution = mrt.imageGuidance.affineTransform(0,0,0,0,0)

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

	def openFiles(self,modality):
		# We don't do any importing of pixel data in here; that is left up to the plotter by sending the filepath.
		if modality == 'ct':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open CT dataset", "", fileFormat)
			self.openCT(files)

		elif modality == 'xray':
			fileFormat = 'NumPy (*.npy)'
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
					if (fn.endswith(tuple('.npy'))) & (fn[:len(modality)] == modality):
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
		if self._isXrayOpen is False:
			# Add the x-ray workspace.
			self.workEnvironment.addWorkspace('X-RAY')

		if len(files) != 2:
			# Force the user to select two files (being orthogonal x-rays).
			self.sbAlignment.widget['checkXray'].setStyleSheet("color: red")
			# log(self.logFile,"Please select 2 Xray images; these should be orthogonal images.","error")
			return

		# Capture the filepath and dataset.
		self.xray.ds = files
		self.xray.fp = os.path.dirname(self.xray.ds[0])

		self.xray.patientOrientation = gv.chairOrientation
		self.xray.alignmentIsoc = gv.hamamatsuAlignmentIsoc
		self.xray.imagePixelSize = np.array([gv.hamamatsuPixelSize,gv.hamamatsuPixelSize])
		self.xray.imageSize = gv.hamamatsuImageSize

		# Create stack page for xray image properties and populate.
		self.sidebarStack.addPage('xrImageProperties')
		self.sbXrayProperties = sbXrayProperties(self.sidebarStack.stackDict['xrImageProperties'])
		self.sbXrayProperties.widget['cbBeamIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='beam'))
		self.sbXrayProperties.widget['cbPatIsoc'].stateChanged.connect(partial(self.xrayOverlay,overlay='patient'))
		self.sbXrayProperties.widget['cbCentroid'].stateChanged.connect(partial(self.xrayOverlay,overlay='centroid'))

		# Link to environment
		self.sbXrayProperties.widget['alignIsocX'].setText(str(gv.hamamatsuAlignmentIsoc[1]))
		self.sbXrayProperties.widget['alignIsocY'].setText(str(gv.hamamatsuAlignmentIsoc[2]))

		# Calculate extent for x-ray images.
		self.xrayCalculateExtent(update=False)

		if self._isXrayOpen is False:
			# Add property variables.
			self.property.addSection('X-Ray')
			self.property.addVariable('X-Ray',['Pixel Size','x','y'],self.xray.imagePixelSize.tolist())
			self.property.addVariable('X-Ray','Patient Orientation',self.xray.patientOrientation)
			self.property.addVariable('X-Ray',['Alignment Isocenter','x','y'],self.xray.alignmentIsoc[-2:].tolist())

			# Connect changes to updates in settings.
			# self.property.itemChanged.connect(self.updateSettings)

			imageFiles = mrt.fileHandler.importImage(self.xray.fp,'xray','npy')
			self.xray.arrayNormal = imageFiles[0]
			self.xray.arrayOrthogonal = imageFiles[1]

			# Create work environment (inclusive of plots and tables).
			self.xray.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['X-RAY'])
			self.xray.plotEnvironment.settings('maxMarkers',gv.markerQuantity)
			self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,extent=self.xray.arrayExtent,imageOrientation=self.xray.patientOrientation,imageIndex=0)
			self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,extent=self.xray.arrayExtent,imageOrientation=self.xray.patientOrientation,imageIndex=1)

			# item = self..findItems('ImageProperties',QtCore.Qt.MatchExactly)[0]
			# print(item)
			# self.xray.plotEnvironment.nav0.actionImageSettings.triggered.connect(partial(self.toolSelect.showToolExternalTrigger,item))

			self.sbAlignment.widget['checkXray'].setStyleSheet("color: green")
			self._isXrayOpen = True

		elif self._isXrayOpen is True:
			# Get new files and plot.
			imageFiles = mrt.fileHandler.importImage(self.xray.fp,'xray','npy')
			self.xray.arrayNormal = imageFiles[0]
			self.xray.arrayOrthogonal = imageFiles[1]
			self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,extent=self.xray.arrayExtent,imageOrientation=self.xray.patientOrientation,imageIndex=0)
			self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,extent=self.xray.arrayExtent,imageOrientation=self.xray.patientOrientation,imageIndex=1)
		
		# Signals and slots.
		self.sbXrayProperties.widget['alignIsocX'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocX']))
		self.sbXrayProperties.widget['alignIsocY'].editingFinished.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.widget['alignIsocY']))
		self.sbXrayProperties.window['pbApply'].clicked.connect(partial(self.updateSettings,'xr',self.sbXrayProperties.window['pbApply']))

		# Set image properties in sidebar to x-ray image properties whenever the workspace is open.
		self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
		self.setImagePropertiesStack()

		# Set to current working environment (in widget stack).
		self.workEnvironment.button['X-RAY'].clicked.emit()

	def xrayOverlay(self,overlay):
		'''Control x-ray plot overlays.'''
		if overlay == 'beam':
			if self.sbXrayProperties.widget['cbBeamIsoc'].isChecked():
				self.xray.plotEnvironment.plot0.overlayIsocenter(state=True)
				self.xray.plotEnvironment.plot90.overlayIsocenter(state=True)
			else:
				self.xray.plotEnvironment.plot0.overlayIsocenter(state=False)
				self.xray.plotEnvironment.plot90.overlayIsocenter(state=False)
		elif overlay == 'patient':
			pass
		elif overlay == 'centroid':
			pass
		else:
			pass

	def xrayCalculateExtent(self,update=True):
		'''Should umbrella all this under an x-ray class.'''
		# Force update of alignment isocenter from settings.
		self.xray.alignmentIsoc = gv.hamamatsuAlignmentIsoc

		# Set extent for plotting. This is essentially the IMBL coordinate system according to the detector.
		left = -self.xray.alignmentIsoc[0]*self.xray.imagePixelSize[0]
		right = (self.xray.imageSize[0]-self.xray.alignmentIsoc[0])*self.xray.imagePixelSize[0]
		bottom = -(self.xray.imageSize[1]-self.xray.alignmentIsoc[1])*self.xray.imagePixelSize[0]
		top = self.xray.alignmentIsoc[1]*self.xray.imagePixelSize[0]
		self.xray.arrayExtent = np.array([left,right,bottom,top])

		if update is True:
			# Force re-draw on plots.
			self.xray.plotEnvironment.plot0.extent = self.xray.arrayExtent
			self.xray.plotEnvironment.plot90.extent = self.xray.arrayExtent
			self.xray.plotEnvironment.plot0.image.set_extent(self.xray.arrayExtent)
			self.xray.plotEnvironment.plot90.image.set_extent(self.xray.arrayExtent)
			self.xray.plotEnvironment.plot0.canvas.draw()
			self.xray.plotEnvironment.plot90.canvas.draw()

	def openCT(self,files):
		'''Open CT modality files.'''
		self.ct.ds = mrt.fileHandler.dicom.importDicom(files,'CT')
		self.workEnvironment.addWorkspace('CT')

		# Get dicom file list.
		if len(self.ct.ds) == 0:
			self.sbAlignment.widget['checkDicom'].setStyleSheet("color: red")
			# log(self.logFile,"No CT files were found.","warning")
			return

		# Continue as normal.
		# log(self.logFile,"Loading %d CT files..." %len(self.ct.ds),"event")

		# Get dicom file list.
		self.ct.ref = self.ct.ds[0]
		self.ct.fp = os.path.dirname(self.ct.ref)

		# Import dicom files.
		dicomData = mrt.fileHandler.dicom.importCT(self.ct.ds, arrayFormat="npy")
		self.ct.pixelSize = dicomData.pixelSize
		self.ct.patientPosition = dicomData.patientPosition
		self.ct.rescaleIntercept = dicomData.rescaleIntercept
		self.ct.rescaleSlope = dicomData.rescaleSlope
		self.ct.imageOrientationPatient = dicomData.imageOrientationPatient
		self.ct.imagePositionPatient = dicomData.imagePositionPatient
		self.ct.arrayExtent = dicomData.arrayExtent

		# Create stack page for xray image properties and populate.
		self.sidebarStack.addPage('ctImageProperties')
		self.sbCTProperties = sbCTProperties(self.sidebarStack.stackDict['ctImageProperties'])

		# Update property table.
		self.property.addSection('CT')
		self.property.addVariable('CT',['Pixel Size','x','y'],self.ct.pixelSize[:2].tolist())
		self.property.addVariable('CT','Slice Thickness',float(self.ct.pixelSize[2]))
		self.property.addVariable('CT','Patient Position',self.ct.patientPosition)

		# Import numpy files.
		imageFiles = mrt.fileHandler.importImage(self.ct.fp,'ct','npy')
		self.ct.arrayDicom = imageFiles[0]
		self.ct.array = imageFiles[1]

		# Plot data.
		self.ct.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['CT'])
		self.ct.plotEnvironment.settings('maxMarkers',gv.markerQuantity)
		self.ct.plotEnvironment.plot0.imageLoad(self.ct.array,extent=self.ct.arrayExtent,imageIndex=0)
		self.ct.plotEnvironment.plot90.imageLoad(self.ct.array,extent=self.ct.arrayExtent,imageIndex=1)

		# Signals and slots.
		self.sbCTProperties.window['pbApply'].clicked.connect(partial(self.updateSettings,'ct',self.sbCTProperties.window['pbApply']))

		# Last checklist items.
		self.workEnvironment.stack.currentChanged.connect(self.setImagePropertiesStack)
		self.setImagePropertiesStack()

		# Set open switch to true and open the workspace (also sets the image properties stack?).
		self._isCTOpen = True
		self.sbAlignment.widget['checkDicom'].setStyleSheet("color: green")
		self.workEnvironment.button['CT'].clicked.emit()

	def openRTP(self,files):
		'''Open RTP modality files.'''
		self.rtp.ds = mrt.fileHandler.dicom.importDicom(files,'RTPLAN')
		self.workEnvironment.addWorkspace('RTPLAN')

		if len(self.rtp.ds) == 0:
			self.sbTreatment.widget['checkRTP'].setStyleSheet("color: red")
			# log(self.logFile,"No RTP files were found.","warning")
			return

		# Continue as normal.
		# log(self.logFile,"Loading %d Radiation Treatment Plan files..." %len(self.rtp.ds),"event")

		self.rtp.fp = os.path.dirname(self.rtp.ds[0])
		dicomData = mrt.fileHandler.dicom.importRTP(self.rtp.ds)
		dicomData.extractTreatmentBeams(self.ct)

		# Assume single fraction.
		self.rtp.beam = dicomData.beam

		self.sbTreatment.widget['quantity'].setText(str(len(self.rtp.beam)))
		self.property.addSection('RTPLAN DICOM')
		self.property.addVariable('RTPLAN DICOM','Number of Beams',len(self.rtp.beam))

		self.sbTreatment.populateTreatments()

		# Iterate through each planned beam.
		for i in range(len(self.rtp.beam)):
			# Create stack page for xray image properties and populate.
			self.sidebarStack.addPage('bev%iImageProperties'%(i+1))
			self.rtp.beam[i].sbImageProperties = sbCTProperties(self.sidebarStack.stackDict['bev%iImageProperties'%(i+1)])

			self.workEnvironment.addWorkspace('BEV%i'%(i+1))
			self.rtp.beam[i].plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['BEV%i'%(i+1)])
			self.rtp.beam[i].plotEnvironment.settings('maxMarkers',gv.markerQuantity)
			self.rtp.beam[i].arrayExtent = dicomData.beam[i].arrayExtent

			# Plot.
			self.rtp.beam[i].plotEnvironment.plot0.imageLoad(self.rtp.beam[i].array,extent=self.rtp.beam[i].arrayExtent,imageIndex=0)
			self.rtp.beam[i].plotEnvironment.plot90.imageLoad(self.rtp.beam[i].array,extent=self.rtp.beam[i].arrayExtent,imageIndex=1)

			# Update property table.
			labels = ['BEV%i'%(i+1),'Gantry Angle','Patient Support Angle','Collimator Angle']
			values = [self.rtp.beam[i].gantryAngle,self.rtp.beam[i].patientSupportAngle,self.rtp.beam[i].collimatorAngle]
			self.property.addVariable('RTPLAN DICOM',labels,values)
			labels = ['BEV%i Isocenter (adjusted)'%(i+1),'x','y','z']
			values = np.round(self.rtp.beam[i].isocenter,decimals=2).tolist()
			self.property.addVariable('RTPLAN DICOM',labels,values)

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
			for i in range(len(self.rtp.beam)):
				if self.workEnvironment.stack.indexOf(self.workEnvironment.stackPage['BEV%i'%(i+1)]) == self.workEnvironment.stack.currentIndex():
						self.sidebarStack.stackDict['ImageProperties'] = self.sidebarStack.stackDict['bev%iImageProperties'%(i+1)]

		# Force refresh.
		self.sidebarStack.setCurrentWidget(self.sidebarStack.stackDict['ImageProperties'])

	def updateSettings(self,mode,origin):
		'''Update variable based of changed data in property model (in some cases, external sources).'''
		if (mode == 'xr') & (self._isXrayOpen):
			'''Update x-ray specific properties.'''
			if origin == self.sbXrayProperties.widget['alignIsocY']:
				# Overwrite the alignment isoc in settings.
				# gv.hamamatsuAlignmentIsoc[:2] = origin.text()
				gv.hamamatsuAlignmentIsoc[0] = origin.text()
				gv.hamamatsuAlignmentIsoc[2] = origin.text()
				# Update the property variables.
				item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['y'])
				item.setData(origin.text(),QtCore.Qt.DisplayRole)
				# Re-calculate the extent.
				self.xrayCalculateExtent()
			elif origin == self.sbXrayProperties.widget['alignIsocX']:
				# Overwrite the alignment isoc in settings.
				# gv.hamamatsuAlignmentIsoc[2] = origin.text()
				gv.hamamatsuAlignmentIsoc[1] = origin.text()
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
				self.xray.plotEnvironment.setRadiographMode(mode)
				self.xray.plotEnvironment.setWindows(windows)

		elif (mode == 'ct') & (self._isCTOpen):
			'''Update ct specific properties.'''
			if origin == self.sbCTProperties.window['pbApply']:
				# Check mode type.
				if self.sbCTProperties.window['rbMax'].isChecked():
					mode = 'max'
				else:
					mode = 'sum'
				# Get windows and apply them.
				windows = self.sbCTProperties.getWindows(self.ct.rescaleSlope,self.ct.rescaleIntercept)
				self.ct.plotEnvironment.setRadiographMode(mode)
				self.ct.plotEnvironment.setWindows(windows)

		elif mode == 'global':
			'''Update global variables, applicable to all modes.'''
			if origin == self.sbAlignment.widget['maxMarkers']:
				value = self.sbAlignment.widget['maxMarkers'].value()
				# Update settings.
				gv.markerQuantity = value
				# Update plot tables.
				if self._isXrayOpen: self.xray.plotEnvironment.settings('maxMarkers',value)
				if self._isCTOpen: self.ct.plotEnvironment.settings('maxMarkers',value)
				if self._isRTPOpen: 
					for i in range(len(self.rtp.beam)):
						self.rtp.beam[i].plotEnvironment.settings('maxMarkers',value)

		# else:
		# 	# If not from an existing widget, it then must originate from the table.
		# 	try:
		# 		index = self.property.indexFromItem(origin)

		# 		if index == self.property.index['X-Ray']['Alignment Isocenter']['x']:
		# 			gv.hamamatsuAlignmentIsoc[:2] = self.property.data(index)
		# 			self.sbSettings.widget['alignIsocX'].setText(str(self.property.data(index)))
		# 			self.xray.alignmentIsoc = gv.hamamatsuAlignmentIsoc
		# 		elif index == self.property.index['X-Ray']['Alignment Isocenter']['y']:
		# 			gv.hamamatsuAlignmentIsoc[2] = self.property.data(index)
		# 			self.sbSettings.widget['alignIsocY'].setText(str(self.property.data(index)))
		# 			self.xray.alignmentIsoc = gv.hamamatsuAlignmentIsoc
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
				self.ct.plotEnvironment.plot0.markerRemove(marker=-2)
				self.ct.plotEnvironment.plot90.markerRemove(marker=-2)
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

		# Do some check to see if Ly and Ry are the same/within a given tolerance?
		# Left is ct
		# Right is xr
		numberOfPoints = self.sbAlignment.widget['maxMarkers'].value()
		left = np.zeros((numberOfPoints,3))
		right = np.zeros((numberOfPoints,3))

		if treatmentIndex == -1:
			'''Align to CT'''
			if len(self.xray.plotEnvironment.plot0.pointsX)>0:
				if self.sbAlignment.widget['optimise'].isChecked():
					markerSize = self.sbAlignment.widget['markerSize'].value()
					threshold = self.sbAlignment.widget['threshold'].value()
					'''Optimise points.'''
					self.xray.plotEnvironment.plot0.markerOptimise(markerSize,threshold)
					self.xray.plotEnvironment.plot90.markerOptimise(markerSize,threshold)
					self.ct.plotEnvironment.plot0.markerOptimise(markerSize,threshold)
					self.ct.plotEnvironment.plot90.markerOptimise(markerSize,threshold)
					# log(self.logFile,"Successfully optimised points.","event")
					# Collect points.
					left[:,0] = self.ct.plotEnvironment.plot0.pointsXoptimised
					left[:,1] = self.ct.plotEnvironment.plot0.pointsYoptimised
					left[:,2] = self.ct.plotEnvironment.plot90.pointsXoptimised
					right[:,0] = self.xray.plotEnvironment.plot0.pointsXoptimised
					right[:,1] = self.xray.plotEnvironment.plot0.pointsYoptimised
					right[:,2] = self.xray.plotEnvironment.plot90.pointsXoptimised
				else:
					'''Do not optimise anything.'''
					left[:,0] = self.ct.plotEnvironment.plot0.pointsX
					left[:,1] = self.ct.plotEnvironment.plot0.pointsY
					left[:,2] = self.ct.plotEnvironment.plot90.pointsX
					right[:,0] = self.xray.plotEnvironment.plot0.pointsX
					right[:,1] = self.xray.plotEnvironment.plot0.pointsY
					right[:,2] = self.xray.plotEnvironment.plot90.pointsX

				print('left pts:',left)
				print('right pts:',right)

				# Align to the CT assuming that the rtp isoc is zero.
				self.alignmentSolution = mrt.imageGuidance.affineTransform(left,right,
					np.array([0,0,0]),
					self.ct.userOrigin,
					self.xray.alignmentIsoc)

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
					left[:,0] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsXoptimised
					left[:,1] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsYoptimised
					left[:,2] = self.rtp.beam[treatmentIndex].plotEnvironment.plot90.pointsXoptimised
					right[:,0] = self.xray.plotEnvironment.plot0.pointsXoptimised
					right[:,1] = self.xray.plotEnvironment.plot0.pointsYoptimised
					right[:,2] = self.xray.plotEnvironment.plot90.pointsXoptimised
				else:
					'''Do not optimise anyting.'''
					left[:,0] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsX
					left[:,1] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsY
					left[:,2] = self.rtp.beam[treatmentIndex].plotEnvironment.plot90.pointsX
					right[:,0] = self.xray.plotEnvironment.plot0.pointsX
					right[:,1] = self.xray.plotEnvironment.plot0.pointsY
					right[:,2] = self.xray.plotEnvironment.plot90.pointsX

				success = True

			# Calcualte alignment requirement
			if success:
				self.alignmentSolution = mrt.imageGuidance.affineTransform(left,right,
					self.rtp.beam[treatmentIndex].isocenter,
					self.ct.userOrigin,
					self.xray.alignmentIsoc)

		else:
			pass

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(self.alignmentSolution.theta),float(self.alignmentSolution.phi),float(self.alignmentSolution.gamma)])
		self.property.updateVariable('Alignment',['Translation','x','y','z'],self.alignmentSolution.translation.tolist())
		self.property.updateVariable('Alignment','Scale',float(self.alignmentSolution.scale))

	def patientApplyAlignment(self):
		'''Connect to motors and apply alignment'''
		patientPosition = mrt.imageGuidance.patientPositioningSystems.DynMRT()
		patientPosition.write('tx',self.alignmentSolution.translation[0])
		patientPosition.write('ty',self.alignmentSolution.translation[1])
		patientPosition.write('tz',self.alignmentSolution.translation[2])
		patientPosition.write('ry',self.alignmentSolution.phi)

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