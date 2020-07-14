from PyQt5 import QtWidgets, QtCore
from functools import partial
from resources import config
import logging

class QAlignment(QtWidgets.QWidget):
	markersChanged = QtCore.pyqtSignal(int)
	calculateAlignment = QtCore.pyqtSignal(int)
	doAlignment = QtCore.pyqtSignal()

	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Markers
		markerGroup = QtWidgets.QGroupBox()
		markerGroup.setTitle('Marker Options')
		label1 = QtWidgets.QLabel('No. of Markers:')
		self.widget['maxMarkers'] = QtWidgets.QSpinBox()
		self.widget['maxMarkers'].setRange(3,10)
		self.widget['maxMarkers'].valueChanged.connect(self.updateMarkers)
		self.widget['maxMarkers'].setToolTip("Number of markers to use for registration.")
		self.widget['anatomical'] = QtWidgets.QRadioButton('Anatomical')
		self.widget['anatomical'].setToolTip("Align using anatomical features.")
		self.widget['fiducial'] = QtWidgets.QRadioButton('Fiducial')
		self.widget['fiducial'].setToolTip("Align using fiducials, offers optimisation parameters.")
		self.widget['optimise'] = QtWidgets.QCheckBox('Optimise')
		self.widget['optimise'].setToolTip("Optimise the fiducial positions.")
		label2 = QtWidgets.QLabel('Marker Size (mm):')
		self.widget['markerSize'] = QtWidgets.QDoubleSpinBox()
		self.widget['markerSize'].setToolTip("Choose the largest dimension of the fiducial markers used.")
		label3 = QtWidgets.QLabel('Threshold (%):')
		self.widget['threshold'] = QtWidgets.QDoubleSpinBox()
		self.widget['threshold'].setToolTip("Threshold for optimisation. Playing with this will change optimisation results.")
		# Layout
		markerGroupLayout = QtWidgets.QFormLayout()
		markerGroupLayout.addRow(label1,self.widget['maxMarkers'])
		markerGroupLayout.addRow(self.widget['anatomical'])
		markerGroupLayout.addRow(self.widget['fiducial'])
		markerGroupLayout.addRow(self.widget['optimise'])
		markerGroupLayout.addRow(label2,self.widget['markerSize'])
		markerGroupLayout.addRow(label3,self.widget['threshold'])
		markerGroup.setLayout(markerGroupLayout)
		self.layout.addWidget(markerGroup)
		# Default Positions
		self.widget['optimise'].setEnabled(False)
		self.widget['anatomical'].setChecked(True)
		self.widget['markerSize'].setEnabled(False)
		self.widget['markerSize'].setRange(1,5)
		self.widget['markerSize'].setSingleStep(0.25)
		self.widget['markerSize'].setValue(2.00)
		self.widget['maxMarkers'].setMinimum(1)
		self.widget['maxMarkers'].setValue(config.markers.quantity)
		self.widget['threshold'].setEnabled(False)
		self.widget['threshold'].setRange(0,50)
		self.widget['threshold'].setValue(3)
		self.widget['threshold'].setSingleStep(0.5)
		# Signals and Slots
		self.widget['anatomical'].toggled.connect(self.markerMode)
		self.widget['fiducial'].toggled.connect(self.markerMode)
		self.widget['optimise'].toggled.connect(self.markerMode)

		# Group 2: Checklist
		alignGroup = QtWidgets.QGroupBox()
		alignGroup.setTitle('Patient Alignment: CT')
		self.widget['calcAlignment'] = QtWidgets.QPushButton('Calculate')
		self.widget['calcAlignment'].setToolTip("Calculate alignment of XR to CT")
		self.widget['doAlignment'] = QtWidgets.QPushButton('Align')
		self.widget['doAlignment'].setToolTip("Perform the calculated alignment")
		# Layout
		alignGroupLayout = QtWidgets.QFormLayout()
		alignGroupLayout.addRow(self.widget['calcAlignment'],self.widget['doAlignment'])
		alignGroup.setLayout(alignGroupLayout)
		self.layout.addWidget(alignGroup)
		# Defaults
		# self.widget['doAlignment'].setEnabled(False)
		# Signals and Slots
		self.widget['calcAlignment'].clicked.connect(partial(self.calculateAlignment.emit,0))
		self.widget['doAlignment'].clicked.connect(self.doAlignment.emit)

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)

	def updateMarkers(self,value):
		# Send signal that the number of markers has changed.
		self.markersChanged.emit(value)

	def markerMode(self):
		'''If fiducial markers are chosen then enable optimisation checkbox and sizing.'''
		# Enabling/toggling optimise.
		if self.widget['fiducial'].isChecked():
			self.widget['optimise'].setEnabled(True)
		else:
			self.widget['optimise'].setEnabled(False)
			self.widget['optimise'].setChecked(False)
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

		# Enabling/toggling markerSize.
		if self.widget['optimise'].isChecked():
			self.widget['markerSize'].setEnabled(True)
			self.widget['threshold'].setEnabled(True)
		else:
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout