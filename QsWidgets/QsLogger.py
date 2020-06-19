from PyQt5 import QtWidgets, QtCore, QtGui
import logging, coloredlogs
from coloredlogs import converter

"""
USE:
import logging
import QcWidgets
class main(QtWidgets.QMainWindow):
	def __init__(self):
		logWidget = QcWidgets.QLog()
		logger = logging.getLogger(__name__)
		logger.addHandler(logWidget.handler)
		logger.setLevel(logging.INFO)
		logging.critical("Test critical message.")
"""

__all__ = ['QLog']

coloredlogs.install()

class QLogHandler(logging.Handler,QtCore.QObject):
	appendHtml = QtCore.pyqtSignal(str)

	def __init__(self,textOutputWidget):
		super().__init__()
		QtCore.QObject.__init__(self)
		# The output widget.
		self.widget = textOutputWidget
		# Set to read only.
		self.widget.setReadOnly(True)
		# Signal connections (thread safe).
		self.appendHtml.connect(self.widget.appendHtml)
		# Set up the log style.
		self.setFormatter(coloredlogs.ColoredFormatter("%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"))

	def emit(self,record):
		# Format the record.
		record = self.format(record)
		record = converter.convert(record, code=True, tabsize=4)
		# Add the record to the widget.
		self.appendHtml.emit(record)

class QLog(QtWidgets.QPlainTextEdit):
	def __init__(self,frame=None):
		super().__init__()
		# Make a handler for the logs.
		self.handler = QLogHandler(self)

		# Install logger into the allocated frame.
		self.frame = frame
		if self.frame is not None:
			layout = QtWidgets.QHBoxLayout()
			layout.addWidget(self)
			layout.setContentsMargins(0,0,0,0)
			self.frame.setLayout(layout)

	def toggleVisibility(self):
		'''Show/hide frane as requested.'''
		self.frame.setVisible(not self.frame.isVisible())
