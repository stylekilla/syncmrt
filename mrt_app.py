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
		self.toolSelect.alignment['align'].clicked.connect(partial(self.alignPatient,treatmentIndex=-1))
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
		self.property.addVariable('Alignment','Theta',0)
		

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
			self.toolSelect.imageWindow['pbApply'].clicked.connect(partial(self.updateSettings,self.toolSelect.imageWindow['pbApply']))
			self.toolSelect.imageWindow['pbReset'].clicked.connect(partial(self.updateSettings,self.toolSelect.imageWindow['pbReset']))

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
		self.workEnvironment.addWorkspace('X-RAY')
		if len(files) != 2:
			self.toolSelect.alignment['checkXray'].setStyleSheet("color: red")
			log(self.logFile,"Please select 2 Xray images; these should be orthogonal images.","error")
			return

		log(self.logFile,"Loading Xray images...","event")

		self.xray.ds = files
		self.xray.fp = os.path.dirname(self.xray.ds[0])

		self.xray.arrayNormalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
		self.xray.arrayOrthogonalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
		self.xray.patientOrientation = settings.chairOrientation
		self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc

		self.property.addSection('X-Ray')
		self.property.addVariable('X-Ray',['Pixel Size','x','y'],self.xray.arrayNormalPixelSize.tolist())
		self.property.addVariable('X-Ray','Patient Orientation',self.xray.patientOrientation)
		self.property.addVariable('X-Ray',['Alignment Isocenter','x','y'],self.xray.alignmentIsoc[-2:].tolist())

		self.property.itemChanged.connect(self.updateSettings)

		imageFiles = fileHandler.importImage(self.xray.fp,'xray','npy')
		self.xray.arrayNormal = self.xray.ds[0]
		self.xray.arrayOrthogonal = self.xray.ds[1]

		self.xray.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['X-RAY'])
		self.xray.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
		self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,self.xray.arrayNormalPixelSize,self.xray.patientOrientation,imageIndex=1)
		self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,self.xray.arrayOrthogonalPixelSize,self.xray.patientOrientation,imageIndex=2)

		item = self.toolSelect.toolList.findItems('ImageProperties',QtCore.Qt.MatchExactly)[0]
		self.xray.plotEnvironment.nav0.actionImageSettings.triggered.connect(partial(self.toolSelect.showToolExternalTrigger,item))

		self.toolSelect.alignment['checkXray'].setStyleSheet("color: green")
		self.workEnvironment.button['X-RAY'].clicked.emit()

	def openCT(self,files):
		'''Open CT modality files.'''
		self.ct.ds = fileHandler.dicom.importDicom(files,'CT')
		self.workEnvironment.addWorkspace('CT')

		if len(self.ct.ds) == 0:
			self.toolSelect.alignment['checkDicom'].setStyleSheet("color: red")
			log(self.logFile,"No CT files were found.","warning")
			return

		# Continue as normal.
		log(self.logFile,"Loading %d CT files..." %len(self.ct.ds),"event")

		self.ct.ref = self.ct.ds[0]
		self.ct.fp = os.path.dirname(self.ct.ref)

		dicomData = fileHandler.dicom.importCT(self.ct.ds, arrayFormat="npy")
		self.ct.pixelSize = dicomData.pixelSize
		self.ct.arrayNormalPixelSize = dicomData.pix0
		self.ct.arrayOrthogonalPixelSize = dicomData.pix90
		self.ct.arrayDimensions = dicomData.dims
		self.ct.patientOrientation = dicomData.orientation
		self.ct.userOrigin = np.array(dicomData.userOrigin)
		self.ct.rescaleIntercept = dicomData.rescaleIntercept
		self.ct.rescaleSlope = dicomData.rescaleSlope

		self.property.addSection('CT')
		self.property.addVariable('CT',['Pixel Size','x','y'],self.ct.pixelSize[:2].tolist())
		self.property.addVariable('CT','Slice Thickness',float(self.ct.pixelSize[2]))
		self.property.addVariable('CT','Patient Orientation',self.ct.patientOrientation)
		self.property.addVariable('CT',['User Origin','x','y','z'],self.ct.userOrigin.tolist())

		imageFiles = fileHandler.importImage(self.ct.fp,'ct','npy')
		self.ct.array3d = imageFiles[0]
		self.ct.arrayNormal = imageFiles[1]
		self.ct.arrayOrthogonal = imageFiles[2]

		self.ct.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['CT'])
		self.ct.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
		self.ct.plotEnvironment.plot0.imageLoad(self.ct.arrayNormal,self.ct.arrayNormalPixelSize,self.ct.patientOrientation,imageIndex=1)
		self.ct.plotEnvironment.plot90.imageLoad(self.ct.arrayOrthogonal,self.ct.arrayOrthogonalPixelSize,self.ct.patientOrientation,imageIndex=2)

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
		dicomData.extractTreatmentBeams(self.ct.arrayNormal,self.ct.arrayNormalPixelSize)

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
			self.rtp.beam[i].plotEnvironment.plot0.imageLoad(self.rtp.beam[i].arrayNormal,self.rtp.beam[i].arrayNormalPixelSize,imageIndex=1)
			self.rtp.beam[i].plotEnvironment.plot90.imageLoad(self.rtp.beam[i].arrayOrthogonal,self.rtp.beam[i].arrayOrthogonalPixelSize,imageIndex=2)

			labels = ['BEV%i'%(i+1),'Gantry Angle','Pitch Angle','Roll Angle']
			values = [self.rtp.beam[i].gantryAngle,self.rtp.beam[i].pitchAngle,self.rtp.beam[i].rollAngle]
			self.property.addVariable('RTPLAN DICOM',labels,values)

			self.toolSelect.treatment['beam'][i]['align'].clicked.connect(partial(self.alignPatient,treatmentIndex=i))

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
		elif origin == self.toolSelect.imageWindow['pbApply']:
			'''When push apply window button, check for mode type and amount of windows.'''
			if self.toolSelect.imageWindow['rbMax'].isChecked():
				mode = 'max'
			else:
				mode = 'sum'
			if self.ct.plotEnvironment:
				# ADD: If ct ticked, then do.
				windows = self.toolSelect.getWindows(self.ct.rescaleSlope,self.ct.rescaleIntercept)
				self.ct.plotEnvironment.setRadiographMode(mode)
				self.ct.plotEnvironment.setWindows(windows)
				# ADD: If rtp ticked, then do.
				if self.rtp.beam[0]:
					for i in range(len(self.rtp.beam)):
						self.rtp.beam[i].plotEnvironment.setRadiographMode(mode)
						self.rtp.beam[i].plotEnvironment.setWindows(windows)

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


	def alignPatient(self,treatmentIndex=-1):
		'''Send coordinates to algorithm and align.'''

		# Do some check to see if Ly and Ry are the same/within a given tolerance?
		# Left is ct
		# Right is xr 
		# TESTING
		if treatmentIndex == -1:
			# Comes from alignment between xray and ct.
			left = np.array(([63.6,25.2,53.7],
				[53.2,43.5,87.7],
				[44.1,65.1,75.8],
				[69.2,65.8,62.6]))
			right = np.array(([82.7,38.3,57.7],
				[81.0,57.4,94.4],
				[69.2,79.9,84.4],
				[90.9,79.4,65.3]))
			self.xray.plotEnvironment.plot0.pointsX = right[:,0]
			self.xray.plotEnvironment.plot0.pointsY = right[:,1]
			self.xray.plotEnvironment.plot90.pointsX = right[:,2]
			self.xray.plotEnvironment.plot90.pointsY = right[:,1]
			self.ct.plotEnvironment.plot0.pointsX = left[:,0]
			self.ct.plotEnvironment.plot0.pointsY = left[:,1]
			self.ct.plotEnvironment.plot90.pointsX = left[:,2]
			self.ct.plotEnvironment.plot90.pointsY = left[:,1]

			# Optimise Points
			if self.toolSelect.alignment['optimise'].isEnabled():
				self.xray.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.xray.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.ct.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.ct.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				log(self.logFile,"Successfully optimised points.","event")

			# Collect points.
			left = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
			right = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
			left[:,0] = self.ct.plotEnvironment.plot0.pointsX
			left[:,1] = self.ct.plotEnvironment.plot0.pointsY
			left[:,2] = self.ct.plotEnvironment.plot90.pointsX
			right[:,0] = self.xray.plotEnvironment.plot0.pointsX
			right[:,1] = self.xray.plotEnvironment.plot0.pointsY
			right[:,2] = self.xray.plotEnvironment.plot90.pointsX

		if treatmentIndex != -1:
			# Is a treatment plan.
			print('Success!', treatmentIndex)
			# Optimise Points
			if self.toolSelect.alignment['optimise'].isEnabled():
				self.xray.plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.xray.plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.rtp.beam[treatmentIndex].plotEnvironment.plot0.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				self.rtp.beam[treatmentIndex].plotEnvironment.plot90.markerOptimise(self.toolSelect.alignment['markerSize'].value())
				log(self.logFile,"Successfully optimised points.","event")

			# Collect points.
			left = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
			right = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
			left[:,0] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsX
			left[:,1] = self.rtp.beam[treatmentIndex].plotEnvironment.plot0.pointsY
			left[:,2] = self.rtp.beam[treatmentIndex].plotEnvironment.plot90.pointsX
			right[:,0] = self.xray.plotEnvironment.plot0.pointsX
			right[:,1] = self.xray.plotEnvironment.plot0.pointsY
			right[:,2] = self.xray.plotEnvironment.plot90.pointsX			

		# Calcualte alignment requirement
		self.alignmentSolution = imageGuidance.affineTransform(left,right,
			self.rtp.beam[treatmentIndex].isocenter,
			self.ct.userOrigin,
			self.xray.alignmentIsoc)

		# If table already exists, update information...
		self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(self.alignmentSolution.theta),float(self.alignmentSolution.phi),float(self.alignmentSolution.gamma)])
		self.property.updateVariable('Alignment',['Translation','x','y','z'],self.alignmentSolution.translation.tolist())
		self.property.updateVariable('Alignment','Scale',float(self.alignmentSolution.scale))

		# print(self.alignmentSolution.theta)
		# print(type(self.alignmentSolution.theta))
		# print(self.alignmentSolution.phi)
		# print(self.alignmentSolution.gamma)
		# print(self.alignmentSolution.translation)
		# print(self.alignmentSolution.scale)

	# def eventFilter(self, source, event):
	# 	# Update ct and xr points in the table as the widget is clicked.
	# 	if event.type() == QtCore.QEvent.MouseButtonRelease:
	# 		self.updateMarkerTable()
	# 	else:
	# 		pass

	# 	return QtWidgets.QMainWindow.eventFilter(self, source, event)

	# def solve(self):
	# 	self.logFile.append('Attempting to solve transformation.')
	# 	# If fiducial mode then refine marker positions is true.
	# 	if len(ct.im0.x) == ct.im0.max_markers:
	# 		if self.sel_fiducial.isChecked() and self.opt_optimise.isChecked():
	# 			pts = imageGuidance.optimiseFiducials(np.column_stack((ct.im0.x,ct.im0.y)),ct.im0.image.get_array(),ct.PixelSize[[0,2]],ct.MarkersSize)
	# 			ct.im0.x = pts[:,0].tolist()
	# 			ct.im0.y = pts[:,1].tolist()
	# 			pts = imageGuidance.optimiseFiducials(np.column_stack((ct.im90.x,ct.im90.y)),ct.im90.image.get_array(),ct.PixelSize[[1,2]],ct.MarkersSize)
	# 			ct.im90.x = pts[:,0].tolist()
	# 			ct.im90.y = pts[:,1].tolist()
	# 			pts = imageGuidance.optimiseFiducials(np.column_stack((xr.im0.x,xr.im0.y)),xr.im0.image.get_array(),xr.PixelSize[[0,2]],xr.MarkersSize)
	# 			xr.im0.x = pts[:,0].tolist()
	# 			xr.im0.y = pts[:,1].tolist()
	# 			pts = imageGuidance.optimiseFiducials(np.column_stack((xr.im90.x,xr.im90.y)),xr.im90.image.get_array(),xr.PixelSize[[1,2]],xr.MarkersSize)
	# 			xr.im90.x = pts[:,0].tolist()
	# 			xr.im90.y = pts[:,1].tolist()
	# 			# Re-plot markers.
	# 			ct.im0.markerUpdate()
	# 			ct.im90.markerUpdate()
	# 			xr.im0.markerUpdate()
	# 			xr.im90.markerUpdate()
	# 			self.logFile.append('Successfully optimised marker points.')
	# 	else:
	# 		self.logFile.append('FAILED: Please ensure the same amount of markers is selected in each image.')


	# 	# Zero the markers into shape.
	# 	ct.Markers = np.zeros((self.num_markers.value(),3))
	# 	xr.Markers = np.zeros((self.num_markers.value(),3))
	# 	# Take markers directly from scatter plot pts (y,x,z).
	# 	ct.Markers = np.column_stack((ct.im90.x,ct.im0.x,ct.im0.y))
	# 	xr.Markers = np.column_stack((xr.im90.x,xr.im0.x,xr.im0.y))

	# 	# Are all the points there?
	# 	if len(ct.Markers) == len(xr.Markers) == ct.im0.max_markers:
	# 		# Send L and R points
	# 		self.solution = imageGuidance.affineTransform(ct.Markers,xr.Markers,ct.ImageDimensions,xr.ImageDimensions,ct.PatientIsoc,ct.UserOrigin,xr.AlignmentIsoc)
	# 		# Print Results
	# 		print(self.solution.translation[0])
	# 		self.tbl_results.setItem(0,1,QtWidgets.QTableWidgetItem(str(self.solution.translation[0])))
	# 		self.tbl_results.setItem(1,1,QtWidgets.QTableWidgetItem(str(self.solution.translation[1])))
	# 		self.tbl_results.setItem(2,1,QtWidgets.QTableWidgetItem(str(self.solution.translation[2])))
	# 		self.tbl_results.setItem(3,1,QtWidgets.QTableWidgetItem(str(self.solution.theta)))
	# 		self.tbl_results.setItem(4,1,QtWidgets.QTableWidgetItem(str(self.solution.phi)))
	# 		self.tbl_results.setItem(5,1,QtWidgets.QTableWidgetItem(str(self.solution.gamma)))
	# 		self.tbl_results.setItem(6,1,QtWidgets.QTableWidgetItem(str(self.solution.scale)))
	# 		self.logFile.append('Successfully computed transformation with '+str(self.solution.scale)+' accuracy.')
	# 	else:
	# 		self.logFile.append('FAILED: Please ensure the same amount of markers is selected in each image.')


if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())