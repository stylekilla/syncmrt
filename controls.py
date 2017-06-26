from PyQt5 import QtCore, QtGui, uic, QtWidgets

class controls:
	def __init__(self,parent):
		self.layout = QtWidgets.QGridLayout()
		parent.setLayout(self.layout)

	def addMotor(self):
		test = widget()
		self.layout.addWidget(test)


class widget(QtWidgets.QWidget):
	def __init__(self,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		uic.loadUi("genericmotorcontrol.ui",self)
		self.dosomething()

	def dosomething(self):
		self.limitLower.setText('Noob')

	def connectPV(self):
		pass