from PyQt5 import QtWidgets, QtCore
from functools import partial
from resources import config
import QsWidgets
import logging

class QStatusMonitor(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		layout = QtWidgets.QVBoxLayout()
		layout.setSpacing(0)
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(QtWidgets.QPushButton("1"))
		self.setLayout(layout)
