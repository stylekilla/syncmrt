from PyQt5 import QtWidgets, QtCore

class Finish(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""
	settingsUpdated = QtCore.pyqtSignal()

	def __init__(self):
		super().__init__()
		self.setTitle("Complete.")
		self.name = "Finish"
		self.description = ""
		self.enabled = True
		self._nextId = -1
		self.data = {}
		# Create a widget.
		widget = QtWidgets.QLabel("The configuration wizard is now complete.")
		# Create a layout.
		layout = QtWidgets.QHBoxLayout()
		# Add the widgets.
		layout.addWidget(widget)
		# Set the layout.
		self.setLayout(layout)

	def setNextId(self,idx):
		# We can never go past the finish.
		pass

	def nextId(self):
		# Always return the enxt id as -1, nominating the end of the wizard.
		return -1