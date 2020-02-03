from PyQt5 import QtWidgets, QtCore

class Detector(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""
	settingsUpdated = QtCore.pyqtSignal()

	def __init__(self,defaults):
		super().__init__()
		self.setTitle("Set the detector settings.")
		# Description for wizard start checkboxes.
		self.name = "Detector"
		self.configSection = "imager"
		self.description = "Detector settings"
		self.enabled = True
		self._nextId = 0
		self.data = {}

		labels = []
		widgets = []

		# Pixel Size inputs.
		labels.append(QtWidgets.QLabel("Pixel Size (um)"))
		self.data['pixelSize'] = QtWidgets.QLineEdit()
		self.data['pixelSize'].setText(str(defaults['pixelSize'][0]))
		self.data['pixelSize'].editingFinished.connect(self.settingsUpdated.emit)
		widgets.append(self.data['pixelSize'])

		# Configure ROI.
		# Configure pixel size.
		# Configure isocentre (use middle by default).
		# Configure SAD/SID.

		# Create a layout.
		layout = QtWidgets.QFormLayout()
		# Add the widgets.
		for label, widget in zip(labels, widgets):
			layout.addRow(label,widget)
		# Set the layout.
		self.setLayout(layout)

	def getData(self):
		data = {}
		data['pixelSize'] = [float(self.data['pixelSize'].text()),float(self.data['pixelSize'].text())]
		return data

	def setNextId(self,idx):
		self._nextId = idx

	def nextId(self):
		return self._nextId