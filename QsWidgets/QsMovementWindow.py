from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

class QMovementWindow(QtWidgets.QMainWindow):
	def __init__(self,device,motors,uid):
		super().__init__()
		# Window setup details.
		centralWidget = QtWidgets.QWidget()
		layout = QtWidgets.QGridLayout()
		layout.setColumnMinimumWidth(1,100)
		layout.setColumnMinimumWidth(2,100)
		layout.setColumnMinimumWidth(3,100)

		# Set the device name as the header.
		header = QtWidgets.QLabel("{} ({})".format(device,uid))
		# Add it to the layout.
		layout.addWidget(header,1,1,1,3)
		# Column headers/
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
			name = QtWidgets.QLabel(motor.name)
			readback = QtWidgets.QLabel(str(motor.readPosition()))
			target = QtWidgets.QLabel('-')
			# Add the widgets to the layout.
			layout.addWidget(name,index+3,1)
			layout.addWidget(readback,index+3,2)
			layout.addWidget(target,index+3,3)
			motor.position.connect(partial(self.updateMotorPosition,readback))
			# motor.moveFinished.connect()

		centralWidget.setLayout(layout)
		self.setCentralWidget(centralWidget)

	def updateMotorPosition(self,widget,value):
		# Set the text of the widget.
		widget.setText(str(value))

	def motorFinished(self):
		# Disconnect all signals.
		# motor.position.disconnect()
		# motor.moveFinished.disconnect()
		# Destroy the widget.
		pass