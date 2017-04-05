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
from syncmrt import fileHandler, imageGuidance, treatment, widgets
# Select Qt5 user interface.
qtCreatorFile = "python/mrt_app/main_copy.ui"
qtStyleSheet = open("python/mrt_app/stylesheet.css")
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
		self.toolSelect.alignment['maxMarkers'].valueChanged.connect(self.updateMarkers)
		self.toolSelect.alignment['align'].clicked.connect(self.alignPatient)
		self.toolSelect.addTool('Treatment')
		self.toolSelect.addTool('Setup')
		self.toolSelect.setup['alignIsocX'].setText(str(settings.hamamatsuAlignmentIsoc[1]))
		self.toolSelect.setup['alignIsocY'].setText(str(settings.hamamatsuAlignmentIsoc[2]))
		self.toolSelect.setup['alignIsocX'].editingFinished.connect(self.updateAlignmentIsocenter)
		self.toolSelect.setup['alignIsocY'].editingFinished.connect(self.updateAlignmentIsocenter)

		# Work environment
		toolbarButtons = [self.toolButtonXray,self.toolButtonCT,self.toolButtonMRI,self.toolButtonRTP]
		self.workEnvironment = workEnvironment(toolbarButtons,self.workStack)
		# Variable panel
		self.variableTreeWidget = QtWidgets.QTreeWidget(self.variableFrame)
		self.variablePane = variablePane(self.variableTreeWidget)

		# Create a ct/mri/xray structure class.
		self.ct = fileHandler.dataDicom()
		self.xray = fileHandler.dataXray()
		self.mri = fileHandler.dataDicom()
		self.rtp = fileHandler.dataRtp()

		# # Connect buttons and widgets.
		self.menuFileOpenCT.triggered.connect(partial(self.openFiles,'ct'))
		self.menuFileOpenXray.triggered.connect(partial(self.openFiles,'xray'))
		self.menuFileOpenMRI.triggered.connect(partial(self.openFiles,'mri'))
		self.menuFileOpenRTP.triggered.connect(partial(self.openFiles,'rtp'))

	def openFiles(self,modality):
		# We don't do any importing of pixel data in here; that is left up to the plotter by sending the filepath.
		if modality == 'ct':
			# Open filedialogue.
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open CT dataset", "", fileFormat)

			# Get CT modality files.
			self.ct.ds = fileHandler.dicom.importDicom(files,'CT')	

			if len(self.ct.ds) > 0:
				log(self.logFile,"Loading %d CT files..." %len(self.ct.ds),"event")

				# Start table model to show variables.
				self.ct.tableModel = variableModel()
				self.variablePane.addTable(self.variableTreeWidget,"CT DICOM",self.ct.tableModel)
				self.ct.ref = self.ct.ds[0]
				self.ct.fp = os.path.dirname(self.ct.ref)

				dicomData = fileHandler.dicom.importCT(self.ct.ds, arrayFormat="npy")
				self.ct.pixelSize = dicomData.pixelSize
				self.ct.arrayNormalPixelSize = dicomData.pix0
				self.ct.arrayOrthogonalPixelSize = dicomData.pix90
				self.ct.arrayDimensions = dicomData.dims
				self.ct.patientOrientation = dicomData.orientation
				self.ct.userOrigin = np.array(dicomData.userOrigin)

				self.ct.tableModel.addMultiVariable(['Pixel Size','x','y'],self.ct.arrayDimensions[:2].tolist())
				self.ct.tableModel.addTableRow('Slice Thickness',float(self.ct.arrayDimensions[2]))
				self.ct.tableModel.addTableRow('Patient Orientation',self.ct.patientOrientation)
				self.ct.tableModel.addMultiVariable(['User Origin','x','y','z'],self.ct.userOrigin.tolist())

				imageFiles = fileHandler.importImage(self.ct.fp,'ct','npy')
				self.ct.array3d = imageFiles[0]
				self.ct.arrayNormal = imageFiles[1]
				self.ct.arrayOrthogonal = imageFiles[2]

				self.ct.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['CT'])
				self.ct.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
				self.ct.plotEnvironment.plot0.imageLoad(self.ct.arrayNormal,self.ct.arrayNormalPixelSize,self.ct.patientOrientation,imageIndex=1)
				self.ct.plotEnvironment.plot90.imageLoad(self.ct.arrayOrthogonal,self.ct.arrayOrthogonalPixelSize,self.ct.patientOrientation,imageIndex=2)

				self.toolSelect.alignment['checkDicom'].setStyleSheet("color: green")
				self.toolButtonCT.clicked.emit()

			else:
				self.toolSelect.alignment['checkDicom'].setStyleSheet("color: red")
				log(self.logFile,"No CT files were found.","warning")

		elif modality == 'xray':
			fileFormat = 'NumPy (*.npy)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open Xray dataset", "", fileFormat)

			if len(files) == 2:
				log(self.logFile,"Loading Xray images...","event")

				self.xray.ds = files
				self.xray.tableModel = variableModel()
				self.variablePane.addTable(self.variableTreeWidget,"Xray",self.xray.tableModel)
				self.xray.fp = os.path.dirname(self.xray.ds[0])

				# We would get or define some settings here...
				self.xray.arrayNormalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
				self.xray.arrayOrthogonalPixelSize = np.array([settings.hamamatsuPixelSize,settings.hamamatsuPixelSize])
				self.xray.patientOrientation = settings.chairOrientation
				self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc

				self.xray.tableModel.addMultiVariable(['Pixel Size','x','y'],self.xray.arrayNormalPixelSize.tolist())
				self.xray.tableModel.addTableRow('Patient Orientation',self.xray.patientOrientation)
				self.xray.tableModel.addMultiVariable(['Alignment Isocenter','x','y','z'],self.xray.alignmentIsoc.tolist())

				imageFiles = fileHandler.importImage(self.xray.fp,'xray','npy')
				self.xray.arrayNormal = imageFiles[0]
				self.xray.arrayOrthogonal = imageFiles[1]

				self.xray.plotEnvironment = plotEnvironment(self.workEnvironment.stackPage['X-RAY'])
				self.xray.plotEnvironment.settings('maxMarkers',settings.markerQuantity)
				self.xray.plotEnvironment.plot0.imageLoad(self.xray.arrayNormal,self.xray.arrayNormalPixelSize,self.xray.patientOrientation,imageIndex=1)
				self.xray.plotEnvironment.plot90.imageLoad(self.xray.arrayOrthogonal,self.xray.arrayOrthogonalPixelSize,self.xray.patientOrientation,imageIndex=2)

				self.toolSelect.alignment['checkXray'].setStyleSheet("color: green")
				self.toolButtonXray.clicked.emit()

			else:
				self.toolSelect.alignment['checkXray'].setStyleSheet("color: red")
				log(self.logFile,"Please select 2 Xray images; these should be orthogonal images.","error")

		elif modality == 'rtp':
			fileFormat = 'DICOM (*.dcm)'
			fileDialogue = QtWidgets.QFileDialog()
			fileDialogue.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
			files, dtype = fileDialogue.getOpenFileNames(self, "Open RP dataset", "", fileFormat)

			self.rtp.ds = fileHandler.dicom.importDicom(files,'RTPLAN')
			if len(self.rtp.ds) > 0:
				log(self.logFile,"Loading %d Radiation Treatment Plan files..." %len(self.rtp.ds),"event")

				self.rtp.tableModel = variableModel()
				self.variablePane.addTable(self.variableTreeWidget,"RTP DICOM",self.rtp.tableModel)
				self.rtp.fp = os.path.dirname(self.rtp.ds[0])

				file = fileHandler.dicom.importRTP(self.rtp.ds)
				# Assume single fraction.
				self.rtp.beam = np.empty(file.FractionGroupSequence[0].NumberOfBeams,dtype=object)
				self.rtp.tableModel.addTableRow('Number of Beams',len(self.rtp.beam))

				for i in range(len(self.rtp.beam)):
					self.rtp.beam[i] = fileHandler.dataBeam()
					self.rtp.beam[i].numberOfBlocks = np.empty(file.BeamSequence[i].NumberOfBlocks,dtype=object)
					# Assume single block.
					self.rtp.beam[i].blockData = file.BeamSequence[i].BlockSequence[0].BlockData
					self.rtp.beam[i].blockThickness = file.BeamSequence[i].BlockSequence[0].BlockThickness
					# Assume single control point sequence.
					self.rtp.beam[i].gantryAngle = float(file.BeamSequence[i].ControlPointSequence[0].GantryAngle)
					self.rtp.beam[i].pitchAngle = float(file.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
					self.rtp.beam[i].rollAngle = float(file.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)
					self.rtp.beam[i].isocenter = np.array(file.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)
					# self.rtp.beam[i].yawAngle =file.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle

					labels = ['Beam %i'%i,'Gantry Angle',' Pitch Angle','Roll Angle']
					values = [self.rtp.beam[i].gantryAngle,self.rtp.beam[i].pitchAngle,self.rtp.beam[i].rollAngle]
					self.rtp.tableModel.addMultiVariable(labels,values)

				self.toolSelect.alignment['checkRTP'].setStyleSheet("color: green")
				self.toolButtonRTP.clicked.emit()

			else:
				self.toolSelect.alignment['checkRTP'].setStyleSheet("color: red")
				log(self.logFile,"No RTP files were found.","warning")

	def updateMarkers(self):
		'''Connect the max markers value to the plot environments.'''
		value = self.toolSelect.alignment['maxMarkers'].value()
		if self.xray.plotEnvironment:
			self.xray.plotEnvironment.settings('maxMarkers',value)
		if self.ct.plotEnvironment:
			self.ct.plotEnvironment.settings('maxMarkers',value)

	def updateAlignmentIsocenter(self):
		settings.hamamatsuAlignmentIsoc[:2] = self.toolSelect.setup['alignIsocX'].text()
		settings.hamamatsuAlignmentIsoc[2] = self.toolSelect.setup['alignIsocY'].text()
		try:
			self.xray.alignmentIsoc = settings.hamamatsuAlignmentIsoc
			print(self.xray.alignmentIsoc)
		except:
			pass

	def alignPatient(self,treatmentIndex=0):
		'''Send coordinates to algorithm and align.'''
		# left = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
		# right = np.zeros((self.toolSelect.alignment['maxMarkers'].value(),3))
		# left[:,0] = self.ct.plotEnvironment.plot0.pointsX
		# left[:,1] = self.ct.plotEnvironment.plot0.pointsY
		# left[:,2] = self.ct.plotEnvironment.plot90.pointsX
		# right[:,0] = self.xray.plotEnvironment.plot0.pointsX
		# right[:,1] = self.xray.plotEnvironment.plot0.pointsY
		# right[:,2] = self.xray.plotEnvironment.plot90.pointsX

		# TESTING
		left = np.array(([25,53,61],
			[65,63,55],
			[64,76,80]))
		right = np.array(([23,50,65],
			[64,62,56],
			[63,77,80]))

		print('Isoc in RTP is: ',self.rtp.beam[treatmentIndex].isocenter)
		self.alignmentSolution = imageGuidance.affineTransform(left,right,
			self.rtp.beam[treatmentIndex].isocenter,
			self.ct.userOrigin,
			self.xray.alignmentIsoc)

		print(self.alignmentSolution.theta)
		print(self.alignmentSolution.phi)
		print(self.alignmentSolution.gamma)
		print(self.alignmentSolution.translation)
		print(self.alignmentSolution.scale)

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