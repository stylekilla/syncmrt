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

# Remove matplotlib warnings.
logging.info("Removing matplotlib logs.")
logging.getLogger("matplotlib").setLevel(logging.CRITICAL)
logging.getLogger("backend_managers").setLevel(logging.CRITICAL)

class QLogHandler(logging.Handler,QtCore.QObject):
	appendLog = QtCore.pyqtSignal(str)

	def __init__(self,masterWidget):
		super().__init__()
		QtCore.QObject.__init__(self)
		# The output widget.
		self.widget = masterWidget
		# Signal connections (thread safe).
		self.appendLog.connect(self.widget.appendLog)
		# Set up the log style.
		self.setFormatter(coloredlogs.ColoredFormatter("%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"))
		# Set the level.
		self.setLevel(logging.WARNING)

	def emit(self,record):
		# Format the record.
		record = self.format(record)
		record = converter.convert(record, code=True, tabsize=4)
		# Add the record to the widget.
		self.appendLog.emit(record)

class QLog(QtWidgets.QWidget):
	def __init__(self,frame=None):
		super().__init__()
		# Make the widgets.
		self.w = {}
		self.w['title'] = QtWidgets.QLabel('Log Output')
		self.w['title'].setStyleSheet("QLabel { background-color : #323232;}")
		self.w['display'] = QtWidgets.QPlainTextEdit()
		self.w['display'].setReadOnly(True)

		# Make a handler for the logs.
		self.handler = QLogHandler(self)

		# Create our layout of widgets.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(self.w['title'])
		layout.addWidget(self.w['display'])
		self.setLayout(layout)

		# Install logger into the allocated frame (sent into this constructor method).
		self.frame = frame

		# Set ourselves as the widget in the frame.
		if self.frame is not None:
			frameLayout = QtWidgets.QHBoxLayout()
			frameLayout.setContentsMargins(0,0,0,0)
			frameLayout.addWidget(self)
			self.frame.setLayout(frameLayout)

		# Set default to invisibile.
		self.frame.setVisible(False)

	def appendLog(self,*args,**kwargs):
		# Append the log.
		self.w['display'].appendHtml(*args,**kwargs)

	def toggleVisibility(self):
		'''Show/hide frane as requested.'''
		self.frame.setVisible(not self.frame.isVisible())
