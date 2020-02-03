from PyQt5 import QtWidgets, QtCore

class Resources(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""
	settingsUpdated = QtCore.pyqtSignal()

	def __init__(self,defaults):
		super().__init__()
		self.setTitle("Set the detector settings.")
		# Description for wizard start checkboxes.
		self.name = "Files"
		self.configSection = "files"
		self.description = "Set the database paths"
		self.enabled = True
		self._nextId = 0
		self.data = {}

		labels = []
		widgets = []

		# Detectors.
		labels.append(QtWidgets.QLabel("Detector List"))
		self.data['detectors'] = QtWidgets.QLineEdit()
		self.data['detectors'].setText(str(defaults['detectors']))
		self.data['detectors'].editingFinished.connect(self.settingsUpdated.emit)
		widgets.append(self.data['detectors'])
		# Patient supports.
		labels.append(QtWidgets.QLabel("Patient Supports List"))
		self.data['patientSupports'] = QtWidgets.QLineEdit()
		self.data['patientSupports'].setText(str(defaults['patientSupports']))
		self.data['patientSupports'].editingFinished.connect(self.settingsUpdated.emit)
		widgets.append(self.data['patientSupports'])

		# Create a layout.
		layout = QtWidgets.QFormLayout()
		# Add the widgets.
		for label, widget in zip(labels, widgets):
			layout.addRow(label,widget)
		# Set the layout.
		self.setLayout(layout)

	def getData(self):
		data = {}
		data['detectors'] = self.data['detectors'].text()
		data['patientSupports'] = self.data['patientSupports'].text()
		return data

	def setNextId(self,idx):
		self._nextId = idx

	def nextId(self):
		return self._nextId