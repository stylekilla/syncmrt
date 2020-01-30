from PyQt5 import QtWidgets, QtCore

class Detector(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""

	def __init__(self):
		super().__init__()
		self.setTitle("Set the detector settings.")
		# Description for wizard start checkboxes.
		self.name = "Detector"
		self.description = "Detector settings"
		self.enabled = False
		self._nextId = 0
		self.data = {}

		labels = []
		widgets = []

		# Pixel Size inputs.
		labels.append(QtWidgets.QLabel("Pixel Size (um)"))
		self.data['pixelSize'] = QtWidgets.QLineEdit()
		widgets.append(self.data['pixelSize'])
		# Pixel Size inputs.
		# labels.append(QtWidgets.QLabel("Flip Image"))
		# labels.append(QtWidgets.QLabel("Flip Image"))
		# labels.append(QtWidgets.QLabel("Flip Image"))

		# Create a layout.
		layout = QtWidgets.QFormLayout()
		# Add the widgets.
		for label, widget in zip(labels, widgets):
			layout.addRow(label,widget)
		# Set the layout.
		self.setLayout(layout)

	def setNextId(self,idx):
		self._nextId = idx

	def nextId(self):
		return self._nextId