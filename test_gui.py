from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os, sys

# https://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt

class main(QtWidgets.QMainWindow):
	def __init__(self):
		# Inititate UI.
		QtWidgets.QMainWindow.__init__(self)
		self.setStyleSheet(open('./test_gui.css').read())
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setWindowTitle('syncMRT-SmallTestEnvironment')

		# Central widget.
		widget = QtWidgets.QWidget()
		widget.setMinimumWidth(210)
		widget.setMaximumWidth(210)

		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)

		# Create widgets.
		systemStatus = StatusGroup('System Status')
		systemStatus.addItem('Patient Positioning')
		systemStatus.addItem('Imaging')
		systemStatus.addItem('Beam Delivery')

		datasets = StatusGroup('Datasets')
		datasets.addItem('Patient Positioning')
		datasets.addItem('Imaging')
		datasets.addItem('Beam Delivery')

		# Add widgets to layout.
		layout.addWidget(systemStatus)
		layout.addWidget(datasets)

		# Set central widget.
		widget.setLayout(layout)
		self.setCentralWidget(widget)

class StatusGroup(QtWidgets.QWidget):
	def __init__(self,title='Empty'):
		super().__init__()

		layout = QtWidgets.QVBoxLayout()
		layout.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(1)

		# header = QtWidgets.QWidget()
		self.header = QGroupHeader()
		self.header.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.header.setProperty('class','Fail')
		# print(self.header.property('background-color'))
		self.header.clicked.connect(self.toggleVisibility)
		# header.setMinimumHeight(24)
		# header.setMaximumHeight(24)

		headerLayout = QtWidgets.QHBoxLayout()
		headerLayout.setContentsMargins(10,5,0,5)
		label = QtWidgets.QLabel(title.upper())
		label.setProperty('class','GroupHeader')
		label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		headerLayout.addWidget(label)
		self.header.setLayout(headerLayout)

		self.children = []

		layout.addWidget(self.header)
		self.setLayout(layout)

	def addItem(self,name):
		child = StatusItem(name)
		child.setProperty('class','Group')

		layout = self.layout()
		layout.addWidget(child)

		self.children.append(child)

	def toggleVisibility(self):
		state = self.children[0].isVisible()
		for child in self.children:
			child.setVisible(not state)

		# formerGeometry = QtCore.QRect(self.geometry())
		# newGeometry = QtCore.QRect(self.header.geometry())

		# anim = QtCore.QPropertyAnimation(self, b"geometry")
		# anim.setDuration(250)
		# anim.setStartValue(formerGeometry)
		# anim.setEndValue(newGeometry)
		# anim.start()

		# https://stackoverflow.com/questions/40287398/pyqt5-stylesheet-animation
		# http://zetcode.com/pyqt/qpropertyanimation/

	def paintEvent(self, event):
		opt = QtWidgets.QStyleOption()
		opt.initFrom(self)
		painter = QtGui.QPainter(self)
		self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, painter, self)

class StatusItem(QtWidgets.QWidget):
	def __init__(self,title='Empty'):
		super().__init__()

		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)

		status = QtWidgets.QLabel()
		status.setProperty('class','Fail')
		status.setMinimumSize(18,18)
		status.setMaximumSize(18,18)

		label = QtWidgets.QLabel(title.upper())

		layout.addWidget(status)
		layout.addWidget(label)

		self.setLayout(layout)

class QGroupHeader(QtWidgets.QWidget):
	clicked = QtCore.pyqtSignal()
	def __init__(self, parent=None):
		super().__init__()

	def mousePressEvent(self, ev):
		self.clicked.emit()

if __name__ == "__main__":
	# QApp 
	app = QtWidgets.QApplication(sys.argv)
	# QWidget (MainWindow).
	window = main()
	window.show()
	# App wide event filter.
	app.installEventFilter(window)
	sys.exit(app.exec_())