from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

# Green: #67F554;
# Red: #F55847;
# Orange: #FA873C;
CSS_STYLESHEET = """
QLabel#motorMoving {
    color: #FA873C;
}

QLabel#motorFinished {
	color: #67F554
}
"""

class QMovementWindow(QtWidgets.QMainWindow):
	def __init__(self,device,motors,uid):
		super().__init__()
		# Set the stylesheet for self and all child widgets.
		self.setStyleSheet(CSS_STYLESHEET)
		# Window setup details.
		centralWidget = QtWidgets.QWidget()
		layout = QtWidgets.QGridLayout()
		layout.setColumnMinimumWidth(1,100)
		layout.setColumnMinimumWidth(2,100)
		layout.setColumnMinimumWidth(3,100)

		# Widget holder.
		self.motor = {}
		# Set the device name as the header.
		header = QtWidgets.QLabel("{} ({})".format(device,uid))
		# Add it to the layout.
		layout.addWidget(header,1,1,1,3)
		# Column headers.
		name = QtWidgets.QLabel("Motor Name")
		readback = QtWidgets.QLabel("Position")
		target = QtWidgets.QLabel("Target")
		# Add them to the layout.
		layout.addWidget(name,2,1)
		layout.addWidget(readback,2,2)
		layout.addWidget(target,2,3)
		# Add widgets and connect signals for each motor.
		for index, motor in enumerate(motors):
			# Create the widgets.
			self.motor[motor.name] = [
				QtWidgets.QLabel(motor.name),
				QtWidgets.QLabel(str(motor.readPosition())),
				QtWidgets.QLabel('-')
			]
			# Add the widgets to the layout.
			layout.addWidget(self.motor[motor.name][0],index+3,1)
			layout.addWidget(self.motor[motor.name][1],index+3,2)
			layout.addWidget(self.motor[motor.name][1],index+3,3)
			# Signals.
			motor.position.connect(partial(self.updateMotorPosition,motor.name))
			motor.moveFinished.connect(partial(self.motorFinished,motor.name))

		centralWidget.setLayout(layout)
		self.setCentralWidget(centralWidget)

	def updateMotorPosition(self,name):
		# Set the stylesheet to say finished.
		for widget in self.motor[motor.name]:
			widget.setObjectName("motorMoving")
		# Set the text of the widget.
		self.motor[motor.name][1].setText(str(value))

	def motorFinished(self,name):
		# Set the stylesheet to say finished.
		for widget in self.motor[motor.name]:
			widget.setObjectName("motorFinished")

	def movementFinished(self):
		# Disconnect all signals.
		motor.position.disconnect(self.updateMotorPosition)
		motor.moveFinished.disconnect(self.motorFinished)