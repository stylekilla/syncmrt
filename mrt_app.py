 # File is dependent on settings.py
from settings import settings
settings = settings()
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
from syncmrt import fileHandler, imageGuidance, treatment, widgets, tools
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

		# Tool panel
		self.toolSelect = toolSelector(self.toolSelectFrame,self.toolStack)
		self.toolSelect.addTool('Alignment')
		self.toolSelect.alignment['maxMarkers'].setValue(3)
		self.toolSelect.alignment['maxMarkers'].valueChanged.connect(partial(self.updateSettings,self.toolSelect.alignment['maxMarkers']))
		self.toolSelect.alignment['align'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=-1))
		self.toolSelect.alignment['optimise'].toggled.connect(partial(self.toggleOptimise))
		self.toolSelect.addTool('Treatment')
		self.toolSelect.addTool('Setup')
		self.toolSelect.setup['alignIsocX'].setText(str(settings.hamamatsuAlignmentIsoc[1]))
		self.toolSelect.setup['alignIsocY'].setText(str(settings.hamamatsuAlignmentIsoc[2]))
		self.toolSelect.setup['alignIsocX'].editingFinished.connect(partial(self.updateSettings,self.toolSelect.setup['alignIsocX']))
		self.toolSelect.setup['alignIsocY'].editingFinished.connect(partial(self.updateSettings,self.toolSelect.setup['alignIsocY']))

		# Work environment
		self.workEnvironment = workEnvironment(self.toolbarPane,self.workStack)

		# PropertyManager
		self.property = propertyModel()
		self.propertyTree = propertyManager(self.variableFrame,self.property)

		# Create a ct/mri/xray structure class.
		self.ct = fileHandler.dataDicom()
		self.xray = fileHandler.dataXray()
		self.mri = fileHandler.dataDicom()
		self.rtp = fileHandler.dataRtp()

		# Create alignment table.
		self.property.addSection('Alignment')
		# Hide table until alignment is clicked...
		self.property.addVariable('Alignment',['Rotation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment',['Translation','x','y','z'],[0,0,0])
		self.property.addVariable('Alignment','Scale',0)
		# Get zero alignment solution result.
		self.alignmentSolution = imageGuidance.affineTransform(0,0,0,0,0)

		# Connect buttons and widgets.
		self.menuFileOpenCT.triggered.connect(partial(self.openFiles,'ct'))
		self.menuFileOpenXray.triggered.connect(partial(self.openFiles,'xray'))
		self.menuFileOpenMRI.triggered.connect(partial(self.openFiles,'mri'))
		self.menuFileOpenRTP.triggered.connect(partial(self.openFiles,'rtp'))
		self.menuFolderOpen.triggered.connect(partial(self.openFiles,'folder'))

	def openFiles(self,modality):
		# Create tool selector for image settings. Only create if it doesn't exist.
		try:
			self.toolSelect.stackPage['ImageProperties']
		except KeyError:
			self.toolSelect.addTool('ImageProperties')
			self.toolSelect.ctWindow['pbApply'].clicked.connect(partial(self.updateSettings,self.toolSelect.ctWindow['pbApply']))
			self.toolSelect.ctWindow['pbReset'].clicked.connect(partial(self.updateSettings,self.toolSelect.ctWindow['pbReset']))
			self.toolSelect.xrayWindow['pbApply'].clicked.connect(partial(self.updateSettings,self.toolSelect.xrayWindow['pbApply']))
			self.toolSelect.xrayWindow['pbReset'].clicked.connect(partial(self.updateSettings,self.toolSelect.xrayWindow['pbReset']))

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
		if settings.xrayIsLoaded == False:
			# Add the x-ray workspace if no x-ray has been opened.
			self.workEnvironment.addWorkspace('X-RAY')
		if len(files) != 2:
			# Force the user to select two files (being orthogonal x-rays).
			self.toolSelect.alignment['checkXray'].setStyleSheet("color: red")
			log(self.logFile,"Please select 2 Xray images; these should be orthogonal images.","error")
			return

		self.xray.ds = files
		self.xray.fp = os.path.dirname(self.xray.ds[0])

		# self.xray.arrayNormalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
		# self.xray.arrayOrthogonalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
		self.xray.patientOrientation = settings.chairOrientation
		self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc
		self.xray.imagePixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
		self.xray.imageSize = settings.hamamatsuImageSize

		# Set extent for plotting. This is essentially the IMBL coordinate system according to the detector.
		left = -self.xray.alignmentIsoc[0]*self.xray.imagePixelSize[0]
		right = (self.xray.imageSize[0]-self.xray.alignmentIsoc[0])*self.xray.imagePixelSize[0]
		bottom = -(self.xray.imageSize[1]-self.xray.alignmentIsoc[1])*self.xray.imagePixelSize[0]
		top = self.xray.alignmentIsoc[1]*self.xray.imagePixelSize[0]
		self.xray.arrayNormalExtent = np.array([left,right,bottom,top])
		self.xray.arrayOrthogonalExtent = np.array([left,right,bottom,top])

		if settings.xrayIsLoaded == False:
			self.property.addSection('X-Ray')
			self.property.addVariable('X-Ray',['Pixel Size','x','y'],self.xray.imagePixelSize.tolist())
			self.property.addVariable('X-Ray','Patient Orientation',self.xray.patientOrientation)
			self.property.addVariable('X-Ray',['Alignment Isocenter (pixels)','x','y'],self.xray.alignmentIsoc[-2:].tolist())

			self.property.itemChanged.connect(self.updateSettings)

			imageFiles = fileHandler.importImage(self.xray.fp,'xray','npy')
			self.xray.arrayNormal = imageFiles[0]
			self.xray.arrayOrthogonal = imageFiles[1]

			self.xray.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['X-RAY'])
			self.xray.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
			self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,extent=self.xray.arrayNormalExtent,imageOrientation=self.xray.patientOrientation,imageIndex=0)
			self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,extent=self.xray.arrayOrthogonalExtent,imageOrientation=self.xray.patientOrientation,imageIndex=1)

			self.xray.plotEnvironment.plot0.overlayIsocenter(state=True)

			item = self.toolSelect.toolList.findItems('ImageProperties',QtCore.Qt.MatchExactly)[0]
			self.xray.plotEnvironment.nav0.actionImageSettings.triggered.connect(partial(self.toolSelect.showToolExternalTrigger,item))

			self.toolSelect.alignment['checkXray'].setStyleSheet("color: green")
			settings.xrayIsLoaded = True

		elif settings.xrayIsLoaded == True:
			imageFiles = fileHandler.importImage(self.xray.fp,'xray','npy')
			self.xray.arrayNormal = imageFiles[0]
			self.xray.arrayOrthogonal = imageFiles[1]
			self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,extent=self.xray.arrayNormalExtent,imageOrientation=self.xray.patientOrientation,imageIndex=0)
			self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,extent=self.xray.arrayOrthogonalExtent,imageOrientation=self.xray.patientOrientation,imageIndex=1)

		self.workEnvironment.button['X-RAY'].clicked.emit()

	def openCT(self,files):
		'''Open CT modality files.'''
		self.ct.ds = fileHandler.dicom.importDicom(files,'CT')
		self.workEnvironment.addWorkspace('CT')

		# Get dicom file list.
		if len(self.ct.ds) == 0:
			self.toolSelect.alignment['checkDicom'].setStyleSheet("color: red")
			log(self.logFile,"No CT files were found.","warning")
			return

		# Continue as normal.
		log(self.logFile,"Loading %d CT files..." %len(self.ct.ds),"event")

		# Get dicom file list.
		self.ct.ref = self.ct.ds[0]
		self.ct.fp = os.path.dirname(self.ct.ref)

		# Import dicom files.
		dicomData = fileHandler.dicom.importCT(self.ct.ds, arrayFormat="npy")
		self.ct.pixelSize = dicomData.pixelSize
		self.ct.patientPosition = dicomData.patientPosition
		self.ct.rescaleIntercept = dicomData.rescaleIntercept
		self.ct.rescaleSlope = dicomData.rescaleSlope
		self.ct.imageOrientationPatient = dicomData.imageOrientationPatient
		self.ct.imagePositionPatient = dicomData.imagePositionPatient
		self.ct.arrayExtent = dicomData.arrayExtent

		# Update property table.
		self.property.addSection('CT')
		self.property.addVariable('CT',['Pixel Size','x','y'],self.ct.pixelSize[:2].tolist())
		self.property.addVariable('CT','Slice Thickness',float(self.ct.pixelSize[2]))
		self.property.addVariable('CT','Patient Position',self.ct.patientPosition)

		# Import numpy files.
		imageFiles = fileHandler.importImage(self.ct.fp,'ct','npy')
		self.ct.arrayDicom = imageFiles[0]
		self.ct.array = imageFiles[1]

		# Plot data.
		self.ct.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['CT'])
		self.ct.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
		self.ct.plotEnvironment.plot0.imageLoad(self.ct.array,extent=self.ct.arrayExtent,imageIndex=0)
		self.ct.plotEnvironment.plot90.imageLoad(self.ct.array,extent=self.ct.arrayExtent,imageIndex=1)

		# Last checklist items.
		self.toolSelect.alignment['checkDicom'].setStyleSheet("color: green")
		self.workEnvironment.button['CT'].clicked.emit()

	def openRTP(self,files):
		'''Open RTP modality files.'''
		self.rtp.ds = fileHandler.dicom.importDicom(files,'RTPLAN')
		self.workEnvironment.addWorkspace('RTPLAN')

		if len(self.rtp.ds) == 0:
			self.toolSelect.alignment['checkRTP'].setStyleSheet("color: red")
			log(self.logFile,"No RTP files were found.","warning")
			return

		# Continue as normal.
		log(self.logFile,"Loading %d Radiation Treatment Plan files..." %len(self.rtp.ds),"event")

		self.rtp.fp = os.path.dirname(self.rtp.ds[0])
		dicomData = fileHandler.dicom.importRTP(self.rtp.ds)
		dicomData.extractTreatmentBeams(self.ct)

		# Assume single fraction.
		self.rtp.beam = dicomData.beam

		self.toolSelect.treatment['quantity'].setText(str(len(self.rtp.beam)))
		self.property.addSection('RTPLAN DICOM')
		self.property.addVariable('RTPLAN DICOM','Number of Beams',len(self.rtp.beam))

		self.toolSelect.populateTreatments()

		# Iterate through each planned beam.
		for i in range(len(self.rtp.beam)):
			self.workEnvironment.addWorkspace('BEV%i'%(i+1))
			self.rtp.beam[i].plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['BEV%i'%(i+1)])
			self.rtp.beam[i].plotEnvironment.settings('maxMarkers',settings.markerQuantity)
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
			self.toolSelect.treatment['beam'][i]['calculate'].clicked.connect(partial(self.patientCalculateAlignment,treatmentIndex=i))
			self.toolSelect.treatment['beam'][i]['align'].clicked.connect(self.patientApplyAlignment)

		self.workEnvironment.button['RTPLAN'].clicked.emit()

	def updateSettings(self,origin):
		'''Update variable based of changed data in property model (in some cases, external sources).'''
		if origin == self.toolSelect.setup['alignIsocX']:
			settings.hamamatsuAlignmentIsoc[:2] = origin.text()
			try:
				item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['x'])
				item.setData(origin.text(),QtCore.Qt.DisplayRole)
			except:
				pass
		elif origin == self.toolSelect.setup['alignIsocY']:
			settings.hamamatsuAlignmentIsoc[2] = origin.text()
			try:
				item = self.property.itemFromIndex(self.property.index['X-Ray']['Alignment Isocenter']['y'])
				item.setData(origin.text(),QtCore.Qt.DisplayRole)
			except:
				pass
		elif origin == self.toolSelect.alignment['maxMarkers']:
			value = self.toolSelect.alignment['maxMarkers'].value()
			settings.markerQuantity = value
			if self.xray.plotEnvironment:
				self.xray.plotEnvironment.settings('maxMarkers',value)
			if self.ct.plotEnvironment:
				self.ct.plotEnvironment.settings('maxMarkers',value)
			try:
				for i in range(len(self.rtp.beam)):
					self.rtp.beam[i].plotEnvironment.settings('maxMarkers',value)
			except:
				pass
		elif origin == self.toolSelect.ctWindow['pbApply']:
			'''When push apply window button, check for mode type and amount of windows.'''
			if self.toolSelect.ctWindow['rbMax'].isChecked():
				mode = 'max'
			else:
				mode = 'sum'
			if self.ct.plotEnvironment:
				# ADD: If ct ticked, then do.
				windows = self.toolSelect.getCTWindows(self.ct.rescaleSlope,self.ct.rescaleIntercept)
				self.ct.plotEnvironment.setRadiographMode(mode)
				self.ct.plotEnvironment.setWindows(windows)
				# ADD: If rtp ticked, then do.
				if self.rtp.beam[0]:
					for i in range(len(self.rtp.beam)):
						self.rtp.beam[i].plotEnvironment.setRadiographMode(mode)
						self.rtp.beam[i].plotEnvironment.setWindows(windows)
		elif origin == self.toolSelect.xrayWindow['pbApply']:
			'''When push apply window button, check for mode type and amount of windows.'''
			mode = 'radiograph'
			if self.xray.plotEnvironment:
				windows = self.toolSelect.getXrayWindows()
				self.xray.plotEnvironment.setRadiographMode(mode)
				self.xray.plotEnvironment.setWindows(windows)

		else:
			# If not from an existing widget, it then must originate from the table.
			try:
				index = self.property.indexFromItem(origin)

				if index == self.property.index['X-Ray']['Alignment Isocenter']['x']:
					settings.hamamatsuAlignmentIsoc[:2] = self.property.data(index)
					self.toolSelect.setup['alignIsocX'].setText(str(self.property.data(index)))
					self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc
				elif index == self.property.index['X-Ray']['Alignment Isocenter']['y']:
					settings.hamamatsuAlignmentIsoc[2] = self.property.data(index)
					self.toolSelect.setup['alignIsocY'].setText(str(self.property.data(index)))
					self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc
			except:
				pass

	def toggleOptimise(self,state):
		'''State(bool) tells you whether you should clear the optimisation plots or not.'''
		print('Executed toggleOptimise with state,',state)
		if state == True:
			pass
		elif state == False:
			print('Attempting to remove optimisation parameters.')
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

		left = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
		right = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
		if treatmentIndex == -1:
			'''Align to CT'''
			if len(self.xray.plotEnvironment.plot0.pointsX)>0:
				if self.toolSelect.alignment['optimise'].isChecked():
					'''Optimise points.'''
					self.xray.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.xray.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.ct.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.ct.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					log(self.logFile,"Successfully optimised points.","event")
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

				# Align to the CT assuming that the rtp isoc is zero.
				self.alignmentSolution = imageGuidance.affineTransform(left,right,
					np.array([0,0,0]),
					self.ct.userOrigin,
					self.xray.alignmentIsoc)

		elif treatmentIndex != -1:
			'''Align to RTPLAN[index]'''
			if len(self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsX)>0:
				# Optimise Points
				if self.toolSelect.alignment['optimise'].isChecked():
					self.xray.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.xray.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.rtp.beam[treatmentIndex].plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					self.rtp.beam[treatmentIndex].plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
					log(self.logFile,"Successfully optimised points.","event")
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
				self.alignmentSolution = imageGuidance.affineTransform(left,right,
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
		patientPosition = imageGuidance.patientPositioningSystems.DynMRT()
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