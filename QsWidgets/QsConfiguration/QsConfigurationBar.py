from PyQt5 import QtWidgets,QtCore,QtGui
import epics
import logging

__all__ = ['ConfigurationManager','ConfigurationItem']

class ConfigurationManager(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		# Widget styling.
		self.setFixedWidth(300)
		# List of configurations.
		self.configurations = []
		# Layout.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(2,2,2,2)
		# Title widget.
		title = QtWidgets.QLabel("Configuration Manager")
		title.setFixedWidth(300)
		# Add the title widget.
		layout.addWidget(title)
		# Set the layout.
		self.setLayout(layout)
		# Tell the window to always stay on top.
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		# Shortcuts.
		shortcutHide = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
		shortcutHide.activated.connect(self.hide)

	def addItem(self,item):
		if isinstance(item,ConfigurationItem):
			# Add it to the layout.
			layout = self.layout()
			layout.addWidget(item)
			# Keep a reference to the configuration.
			self.configurations.append(item)
		else:
			logging.critical("Could not add {} to configuration manager.".format(item))


class ConfigurationItem(QtWidgets.QWidget):
	""" A bar that allows one to edit and apply a beamline configuration. """
	def __init__(self,name,configFile):
		super().__init__()
		# Save our args.
		self.name = str(name)
		self.file = configFile
		# Make a layout.
		layout = QtWidgets.QHBoxLayout()
		# Make a title.
		title = QtWidgets.QLabel(self.name.capitalize())
		# Make an edit button.
		edit = QtWidgets.QPushButton("Edit")
		# Make a go button.
		go = QtWidgets.QPushButton("Go")
		# If go button pressed, execute the script - must be thread blocking... disables the main window with spinny wheel!
		go.clicked.connect(self.go)
		edit.clicked.connect(self.edit)
		# Add widgets.
		layout.addWidget(title)
		layout.addWidget(edit)
		layout.addWidget(go)
		# Set layout.
		self.setLayout(layout)

	def go(self):
		""" Move everything in the configuration file. """
		# Read the instructions from the file.
		f = open(self.file,'r')
		instructions = f.readlines()
		for instruction in instructions:
			if instruction.startswith('#') or len(instruction) == 0:
				# Ignore it.
				pass
			else:
				instruction = instruction.split(' ')
				if len(instruction) == 2:
					# Get the PV and the value to write.
					pv, value = instruction
					# Write the value to epics and wait for it to complete.
					# epics.caput(pv,float(value),wait=True)
					logging.critical("GO: {} -> {}".format(pv,value))
					# MAKE THIS MULTITHREADED!
		f.close()

	def edit(self):
		""" Edit the file. """
		self.textedit = FileEditor(self.file)
		self.textedit.show()
		self.textedit.raise_()
		self.textedit.activateWindow()


class FileEditor(QtWidgets.QWidget):
	def __init__(self,file):
		super().__init__()
		# Save the filename.
		self.file = file
		# Create a layout.
		layout = QtWidgets.QVBoxLayout()
		# Create the editor.
		self.textedit = QtWidgets.QTextEdit()
		# Buttons.
		cancel = QtWidgets.QPushButton("Cancel")
		save = QtWidgets.QPushButton("Save")
		# Sub widget/layout for buttons.
		buttons = QtWidgets.QWidget()
		buttonlayout = QtWidgets.QHBoxLayout()
		buttonlayout.addWidget(cancel)
		buttonlayout.addWidget(save)
		buttons.setLayout(buttonlayout)
		# Add to layout.
		layout.addWidget(self.textedit)
		layout.addWidget(buttons)
		# Connections.
		cancel.clicked.connect(self.close)
		save.clicked.connect(self.save)
		# Set the layout.
		self.setLayout(layout)
		# Write the file contents to the text editor.
		f = open(self.file,'r')
		self.textedit.setText(f.read())
		f.close()
		# Make us always visible on top.
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		# Save and close on keyboard shortcut for save.
		shortcutSave = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self.textedit)
		shortcutSave.activated.connect(self.save)
		shortcutClose = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self.textedit)
		shortcutClose.activated.connect(self.close)

	def save(self):
		# Write the editor contents to the file.
		f = open(self.file,'w')
		f.write(str(self.textedit.toPlainText()))
		f.close()
		# Close the window.
		self.close()