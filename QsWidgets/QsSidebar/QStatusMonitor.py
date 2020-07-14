from PyQt5 import QtWidgets, QtCore
from functools import partial
from resources import config
import QsWidgets
import logging

CSS_STYLESHEET = """
QWidget.StatusInvalid {
	color: red;
	background-color: red;
}

QWidget.StatusWarning {
	color: red;
	background-color: orange;
}

QWidget.StatusGood {
	background-color: green;
}
"""

class QStatusMonitor(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		# Dict for devices.
		self.device = {}
		# Make a form layout for this wiget.
		layout = QtWidgets.QFormLayout()
		layout.setSpacing(2)
		layout.setHorizontalSpacing(10)
		layout.setContentsMargins(0,0,0,0)
		layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		layout.setFormAlignment(QtCore.Qt.AlignLeft)
		self.setLayout(layout)

	def addMonitor(self,name):
		# Create a label for the status.
		status = QtWidgets.QLabel('Not Connected')
		# Add the title and status to the layout.
		self.layout().addRow("{}:".format(name),status)
		# Save the widgets.
		self.device[name] = status

	def removeMonitor(self,name):
		# Remove wigets from layout.
		self.layout().removeRow(self.device[name])
		# Remove from the dict.
		del self.device[name]

	def updateMonitor(self,name,status):
		# Update the value label with the new value.
		self.device[name].setText(status)