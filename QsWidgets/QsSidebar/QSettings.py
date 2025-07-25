from PyQt5 import QtWidgets, QtCore
from functools import partial
import QsWidgets
from .. import QsGeneric
import logging
from resources import config

class QSettings(QtWidgets.QWidget):
	modeChanged = QtCore.pyqtSignal('QString')
	maskSizeChanged = QtCore.pyqtSignal(float)
	maskSizeXChanged = QtCore.pyqtSignal(float)
	maskSizeYChanged = QtCore.pyqtSignal(float)
	maskSource = QtCore.pyqtSignal('QString')
	refreshConnections = QtCore.pyqtSignal()

	def __init__(self):
		super().__init__()
		self.controls = {}
		self.hardware = {}
		self.widget = {}
		self.group = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Hardware
		self.group['hardware'] = QtWidgets.QGroupBox()
		self.group['hardware'].setTitle('Hardware Configuration')
		self.hardware['detector'] = QtWidgets.QComboBox()
		self.hardware['refresh'] = QtWidgets.QPushButton("Refresh Connections")
		# Layout
		hardwareGroupLayout = QtWidgets.QVBoxLayout()
		hardwareGroupLayout.addWidget(self.hardware['refresh'])
		self.group['hardware'].setLayout(hardwareGroupLayout)
		# Signals and Slots
		self.hardware['refresh'].clicked.connect(self._refreshConnections)

		# Mask Settings.
		self.group['mask'] = QtWidgets.QGroupBox()
		self.group['mask'].setTitle("Mask Settings")
		self.widget['maskShapeSquare'] = QtWidgets.QRadioButton('Square')
		self.widget['maskShapeSquare'].setChecked(False)
		self.widget['maskShapeSquare'].clicked.connect(partial(self.maskSource.emit,'Square'))
		self.widget['maskShapeCircle'] = QtWidgets.QRadioButton('Circle')
		self.widget['maskShapeCircle'].clicked.connect(partial(self.maskSource.emit,'Circle'))
		self.widget['maskShapePlan'] = QtWidgets.QRadioButton('Plan')
		self.widget['maskShapePlan'].clicked.connect(partial(self.maskSource.emit,'Plan'))
		self.widget['maskShapeRectangle'] = QtWidgets.QRadioButton('Rectangle')
		self.widget['maskShapeRectangle'].clicked.connect(partial(self.maskSource.emit,'Rectangle'))
		self.widget['maskSize'] = QsWidgets.QRangeEdit()
		self.widget['maskSize'].setRange([0,50.0],config.general.defaultMaskSize)
		self.widget['maskSize'].editingFinished.connect(self._emitMaskSizeChanged)
		#
		self.widget['maskSizeX'] = QsWidgets.QRangeEdit()
		self.widget['maskSizeX'].setRange([0,50.0],config.general.defaultMaskSizeX)
		self.widget['maskSizeX'].editingFinished.connect(self._emitMaskSizeXChanged)
		self.widget['maskSizeY'] = QsWidgets.QRangeEdit()
		self.widget['maskSizeY'].setRange([0,50.0],config.general.defaultMaskSizeY)
		self.widget['maskSizeY'].editingFinished.connect(self._emitMaskSizeYChanged)

		if  "Square" in config.general.defaultMaskType : self.widget['maskShapeSquare'].setChecked(True)
		elif  "Circle" in config.general.defaultMaskType : self.widget['maskShapeCircle'].setChecked(True)
		elif  "Rectangle" in config.general.defaultMaskType : self.widget['maskShapeRectangle'].setChecked(True)
		# Layout.
		lyt = QtWidgets.QFormLayout()
		lyt.addRow(QtWidgets.QLabel("Size (mm):"),self.widget['maskSize'])
		lyt.addRow(QtWidgets.QLabel("Shape:"))
		lyt.addRow(self.widget['maskShapeSquare'])
		lyt.addRow(self.widget['maskShapeCircle'])
		#lyt.addRow(self.widget['maskShapePlan'])
		lyt.addRow(self.widget['maskShapeRectangle'])
		lyt.addRow(QtWidgets.QLabel("Size X (mm):"),self.widget['maskSizeX'])
		lyt.addRow(QtWidgets.QLabel("Size Y (mm):"),self.widget['maskSizeY'])
		self.group['mask'].setLayout(lyt)

		# Add Sections
		self.layout.addWidget(self.group['hardware'])
		self.layout.addWidget(self.group['mask'])
		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def loadStages(self,stageList):
		# stageList should be a list of strings of the stages available to choose from.
		self.hardware['motorsList'] = stageList

		# For each item in the list, add it to the drop down list.
		for item in self.hardware['motorsList']:
			self.hardware['stage'].addItem(item)

		# Sort the model alphanumerically.
		self.hardware['stage'].model().sort(0)

	def stageChange(self):
		self.stageChanged.emit(self.hardware['stage'].currentText())

	def _refreshConnections(self):
		self.refreshConnections.emit()

	def _emitMaskSizeChanged(self):
		# Turn the line edit text into a float.
		if self.widget['maskSize'].isValid(): self.maskSizeChanged.emit(float(self.widget['maskSize'].text()))

	def _emitMaskSizeXChanged(self):
		# Turn the line edit text into a float.
		if self.widget['maskSizeX'].isValid(): self.maskSizeXChanged.emit(float(self.widget['maskSizeX'].text()))

	def _emitMaskSizeYChanged(self):
		# Turn the line edit text into a float.
		if self.widget['maskSizeY'].isValid(): self.maskSizeYChanged.emit(float(self.widget['maskSizeY'].text()))		


	def loadDetectors(self,stageList):
		# stageList should be a list of strings of the stages available to choose from.
		self.hardware['detectorList'] = stageList

		# For each item in the list, add it to the drop down list.
		for item in self.hardware['detectorList']:
			self.hardware['detector'].addItem(item)

		# Sort the model alphanumerically.
		self.hardware['detector'].model().sort(0)

	def detectorChange(self):
		self.detectorChanged.emit(self.hardware['detector'].currentText())

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout
