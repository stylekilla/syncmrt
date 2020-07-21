from PyQt5 import QtWidgets, QtCore
import logging

class QMotorMonitor(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		# Dict of pv's that are being monitored.
		self.motor = {}

		# Make a form layout for this wiget.
		layout = QtWidgets.QFormLayout()
		layout.setSpacing(2)
		layout.setHorizontalSpacing(10)
		layout.setContentsMargins(0,0,0,0)
		layout.setLabelAlignment(QtCore.Qt.AlignLeft)
		layout.setFormAlignment(QtCore.Qt.AlignLeft)
		self.setLayout(layout)

	def addMotor(self,name,value='-'):
		# Create a label for the value.
		self.motor[name] = QtWidgets.QLabel(value)
		# Add the title and value to the layout.
		self.layout().addRow("{}:".format(name),self.motor[name])
		logging.info("Adding motor {}".format(name))

	def removeMotor(self,name=None):
		if name is None:
			# Remove all widgets.
			for key in self.motor:
				self.layout().removeRow(self.motor[key])
			# Clear the dictionary.
			self.motor.clear()

		elif name in self.motor:
			# Remove the singular widget.
			self.layout().removeRow(self.motor[name])
			del self.motor[name]

		else:
			logging.warning("Motor {} not in list of active motor monitors.".format(name))

	def newMotors(self,name,motors):
		# Remove any existing motors.
		self.removeMotor()
		# Add each new motor.
		for motor in motors:
			self.addMotor(motor)

	def updateMotor(self,name,value):
		# Update the value label with the new value.
		if name in self.motor:
			self.motor[name].setText("{:.3f}".format(value))