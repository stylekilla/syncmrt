from PyQt5 import QtWidgets,QtCore,QtGui
import epics
import threading
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
		# Parse the config file.
		config = parseConfigFile(self.file)
		for group in config:
			if len(group) == 1:
				# Get the PV and the value to write.
				pv, value = group[0]
				# Write the value to epics and wait for it to complete.
				# epics.caput(pv,float(value),wait=True)
				print("SINGLE {} = {}".format(pv,value))
			else:
				# Create a thread tracker.
				threads = []
				# Assume a group of commands.
				for command in group:
					# Seperate the PV and value data.
					pv,value = command
					# Do the epics processing on a seperate thread.
					threads.append(threading.Thread(target=epics_threadsafe,args=[pv,float(value)]))
					threads[-1].start()
				# Wait until all the threads are finished before we continue.
				while True:
					if len(threads) > 0:
						for thread in threads:
							try:
								# Once the thread has finished, remove it.
								thread.join()
								threads.remove(thread)
							except:
								pass	
					else:
						break

		logging.info("Configuration is set.")

	def edit(self):
		""" Edit the file. """
		self.textedit = FileEditor(self.file)
		self.textedit.show()
		self.textedit.raise_()
		self.textedit.activateWindow()

def parseConfigFile(file):
	""" 
	Parse the config file.
	Single commands shall be executed in order.
	Grouped commands shall be executed simulatenously in threads.
	"""
	groups = []
	commands = []

	# Read the instructions from the file.
	f = open(file,'r')
	instructions = f.readlines()
	f.close()

	# Iterate over the instructions...
	for instruction in instructions:
		if instruction.startswith('#') or len(instruction) == 0:
			# Ignore it.
			pass
		elif instruction == '{':
			# Reset the commands list for the new group.
			commands = []
		elif instruction == '}':
			# If we have any previous commands, add them as a group.
			if len(commands) > 0:
				groups.append(commands)
		elif instruction.startswith('\t'):
			# Remove the whitespace.
			instruction = instruction.strip().split(' ')
			# Add if there are only two values (assumes PV + Value).
			if len(instruction) == 2:
				if not instruction[0].startswith('#'):
					commands.append(instruction)
		else:
			# Assume it's a single line, not in a group.
			instruction = instruction.split(' ')
			if len(instruction) == 2:
				groups.append([instruction])

	return groups


def epics_threadsafe(pv,value):
	""" An epics ca.put() function that will wait until it has finished. """
	try:
		logging.info("Setting: {} -> {}".format(pv,value))
		print("THREAD {} = {}".format(pv,value))
		# epics.caput(pv,value,wait=True)
	except:
		logging.warning("Could not set PV {} to {}.".format(pv,value))


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