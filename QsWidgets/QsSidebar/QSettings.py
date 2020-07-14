from PyQt5 import QtWidgets, QtCore
from functools import partial
import QsWidgets
from .. import QsGeneric
import logging

class QSettings(QtWidgets.QWidget):
	modeChanged = QtCore.pyqtSignal('QString')
	stageChanged = QtCore.pyqtSignal('QString')
	detectorChanged = QtCore.pyqtSignal('QString')
	maskSizeChanged = QtCore.pyqtSignal(float)
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
		detectorLabel = QtWidgets.QLabel('Stage')
		self.hardware['stage'] = QtWidgets.QComboBox()
		stageLabel = QtWidgets.QLabel('Detector')
		self.hardware['detector'] = QtWidgets.QComboBox()
		self.hardware['refresh'] = QtWidgets.QPushButton("Refresh Connections")
		# Layout
		hardwareGroupLayout = QtWidgets.QVBoxLayout()
		hardwareGroupLayout.addWidget(detectorLabel)
		hardwareGroupLayout.addWidget(self.hardware['stage'])
		hardwareGroupLayout.addWidget(stageLabel)
		hardwareGroupLayout.addWidget(self.hardware['detector'])
		hardwareGroupLayout.addWidget(QsGeneric.QHLine())
		hardwareGroupLayout.addWidget(self.hardware['refresh'])
		self.group['hardware'].setLayout(hardwareGroupLayout)
		# Signals and Slots
		self.hardware['stage'].currentIndexChanged.connect(self.stageChange)
		self.hardware['detector'].currentIndexChanged.connect(self.detectorChange)
		self.hardware['refresh'].clicked.connect(self._refreshConnections)

		# Mask Settings.
		self.group['mask'] = QtWidgets.QGroupBox()
		self.group['mask'].setTitle("Mask Settings")
		self.widget['maskSize'] = QsWidgets.QRangeEdit()
		self.widget['maskSize'].setRange([0,30.0],20.0)
		self.widget['maskSize'].editingFinished.connect(self._emitMaskSizeChanged)
		# Layout.
		lyt = QtWidgets.QFormLayout()
		lyt.addRow(QtWidgets.QLabel("Size (mm):"),self.widget['maskSize'])
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
