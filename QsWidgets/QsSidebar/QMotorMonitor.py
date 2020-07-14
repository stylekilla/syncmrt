from PyQt5 import QtWidgets, QtCore
from functools import partial
from resources import config
import QsWidgets
import logging
import epics

class QMotorMonitor(QtWidgets.QWidget):
	def __init__(self,monitor):
		super().__init__()
		# Dict of pv's that are being monitored.
		self.motor = {}

		# Create the monitor. This should be part of your backend system and should run on a separate thread.
		self.monitor = monitor
		# Signals and slots.
		self.monitor.pvUpdated.connect(self.updatePV)

		# Make a form layout for this wiget.
		layout = QtWidgets.QFormLayout()
		layout.setSpacing(2)
		layout.setHorizontalSpacing(10)
		layout.setContentsMargins(0,0,0,0)
		layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		layout.setFormAlignment(QtCore.Qt.AlignLeft)
		self.setLayout(layout)

	def addPV(self,pvName,displayName=''):
		# Set the display name for the pv.
		if displayName is not '':
			name = str(displayName)
		else:
			name = str(pvName)

		# Create a label for the value.
		value = QtWidgets.QLabel('Not Connected')
		# Add the title and value to the layout.
		self.layout().addRow("{}:".format(name),value)
		# Save the widgets.
		self.motor[pvName] = value

		# Add the pv to the monitor.
		self.monitor.addPV(pvName,displayName)

	def removePV(self,pvName):
		# Disconnect the PV from the monitor including all callbacks.
		self.monitor.removePV(pvName)
		# Remove wigets from layout.
		self.layout().removeRow(self.motor[pvName])
		# Remove from the dict.
		del self.motor[pvName]

	def updatePV(self,pvName,value):
		# Update the value label with the new value.
		self.motor[pvName].setText("{:.3f}".format(value))