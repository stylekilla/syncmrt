from PyQt5 import QtWidgets, QtCore

class Markers(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""

	def __init__(self,defaults):
		super().__init__()
		self.setTitle("Set marker properties.")
		# Description for wizard start checkboxes.
		self.name = "Markers"
		self.description = "Marker settings"
		self.enabled = True
		self._nextId = 0
		self.data = {}

		labels = []
		widgets = []

		# Quantity.
		labels.append(QtWidgets.QLabel("Number Of Markers"))
		self.data['quantity'] = QtWidgets.QSpinBox()
		self.data['quantity'].setMinimum(3)
		self.data['quantity'].setMaximum(10)
		self.data['quantity'].setValue(int(defaults['quantity']))
		widgets.append(self.data['quantity'])
		# Marker size.
		labels.append(QtWidgets.QLabel("Marker Size"))
		self.data['size'] = QtWidgets.QDoubleSpinBox()
		self.data['size'].setMinimum(1.0)
		self.data['size'].setMaximum(5.0)
		self.data['size'].setValue(float(defaults['size']))
		widgets.append(self.data['size'])

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