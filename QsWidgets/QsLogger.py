import os, sys
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
import logging, coloredlogs
from coloredlogs import converter

# For PyInstaller:
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader extends the sys module by a flag frozen=True and sets the app path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
resourceFilepath = application_path+'/../resources/'

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

CSS_STYLESHEET = """
TopBar {
	margin: 0px;
}

QToolBar {
	margin: 0px;
    border-style: none;			/* Remove the stupid top and bottom lines */
}

QToolButton {
	padding: 3px;
	margin: 0px;
    background: #262626;
    border-radius: 1px; 
}

QToolButton:menu-indicator {
	image: none;
}
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
		self.setFormatter(coloredlogs.ColoredFormatter("%(asctime)s,%(msecs)-3d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"))
		# Set the level.
		self.setLevel(logging.INFO)

	def emit(self,record):
		# Format the record.
		record = self.format(record)
		record = converter.convert(record, code=True, tabsize=4)
		# Add the record to the widget.
		self.appendLog.emit(record)

class QLog(QtWidgets.QWidget):
	def __init__(self,frame=None,visible=False):
		super().__init__()
		# Set the style sheet.
		self.setStyleSheet(CSS_STYLESHEET)
		# Make a handler for the logs.
		self.handler = QLogHandler(self)

		# Top Widget.
		topBar = QtWidgets.QWidget()
		topBar.setStyleSheet("QWidget {background-color: #1A1A1A;}")

		# Title.
		self.title = QtWidgets.QLabel("Log Output (Warning)")
		self.title.setContentsMargins(20,0,0,0)

		# Toolbar.
		toolbar = QtWidgets.QToolBar()
		toolbar.setContentsMargins(0,0,10,0)
		toolbar.setFixedHeight(24)

		# Menu Button.
		burger = QtWidgets.QToolButton()
		burger.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		burger.setFixedSize(24,24)
		icon = QtGui.QIcon(resourceFilepath+'/images/BurgerMenu-Light.png')
		icon.pixmap(18,18)
		burger.setIcon(icon)

		# Popup Menu.
		menu = QtWidgets.QMenu()
		# Logging level.
		logLevelInfo = menu.addAction("Info")
		logLevelWarning = menu.addAction("Warning")
		logLevelCritical = menu.addAction("Critical")
		# Log io options.
		menu.addSeparator()
		logOptionsSave = menu.addAction("Save")
		logOptionsClear = menu.addAction("Clear")

		# Add menu to button.
		burger.setMenu(menu)
		# Add button to toolbar.
		toolbar.addWidget(burger)

		# Layout of top widget.
		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		layout.addWidget(self.title)
		layout.insertWidget(1,toolbar,0,QtCore.Qt.AlignRight)
		topBar.setLayout(layout)

		# Log Display Widget.
		self.logDisplay = QtWidgets.QPlainTextEdit()
		self.logDisplay.setReadOnly(True)

		# Create our layout of widgets.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		layout.addWidget(topBar)
		layout.addWidget(self.logDisplay)
		self.setLayout(layout)

		# Install logger into the allocated frame (sent into this constructor method).
		self.frame = frame

		# Set ourselves as the widget in the frame.
		if self.frame is not None:
			frameLayout = QtWidgets.QHBoxLayout()
			frameLayout.setContentsMargins(0,0,0,0)
			frameLayout.setSpacing(0)
			frameLayout.addWidget(self)
			self.frame.setLayout(frameLayout)

		# Signals and slots.
		logLevelInfo.triggered.connect(partial(self.setLogLevel,"Info"))
		logLevelWarning.triggered.connect(partial(self.setLogLevel,"Warning"))
		logLevelCritical.triggered.connect(partial(self.setLogLevel,"Critical"))
		logOptionsSave.triggered.connect(self.saveLog)
		logOptionsClear.triggered.connect(self.clearLog)

		# Set visibility state (False by default).
		self.frame.setVisible(visible)

	def setLogLevel(self,levelName):
		if levelName == 'Info':
			level = logging.INFO
		elif levelName == 'Warning':
			level = logging.WARNING
		elif levelName == 'Critical':
			level = logging.CRITICAL
		# Set the log levelName.
		self.handler.setLevel(level)
		# Update the title bar.
		self.title.setText("Log Output ({})".format(levelName))

	def appendLog(self,*args,**kwargs):
		# Append the log.
		self.logDisplay.appendHtml(*args,**kwargs)

	def saveLog(self):
		text = self.logDisplay.toPlainText()
		# Pop up menu of where to save.
		fileFormat = 'Plain Text (*.txt)'
		fileDialogue = QtWidgets.QFileDialog()
		file, dtype = fileDialogue.getSaveFileName(self, "Save log output", "", fileFormat)
		# Save the text file if a filename was given.
		if file is not "":
			if file.endswith('.txt') is False:
				file += '.txt'
			with open(file,"w") as outFile:
				outFile.write(text)

	def clearLog(self):
		self.logDisplay.clear()

	def toggleVisibility(self):
		'''Show/hide frane as requested.'''
		self.frame.setVisible(not self.frame.isVisible())
