from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

class Start(QtWidgets.QWizardPage):
	"""
	The first wizard page the user sees.
	As pages are created, checkboxes should be added.
	"""
	addPage = QtCore.pyqtSignal(str,bool)
	def __init__(self):
		super().__init__()
		self.setTitle("Select the wizards to run through.")
		self.name = "Start"
		self.description = ""
		self.enabled = True
		self._nextId = 1
		self.data = {}
		self.isPopulated = False

	def setCheckBoxes(self,wizardPages):
		""" Don't add the first or last one as they are nominally
		Start and Finish. """
		if self.isPopulated: 
			# Return if already populated, otherwise do so.
			return
		self.wizardPages = wizardPages
		# Create the widgets.
		checkboxes = []
		for item in list(wizardPages.values())[1:-1]:
			checkboxes.append(QtWidgets.QCheckBox(item.description))
			checkboxes[-1].setChecked(True)
			checkboxes[-1].stateChanged.connect(partial(self.setState,item.name))
		# Create a layout.
		layout = QtWidgets.QHBoxLayout()
		# Add the widgets.
		for widget in checkboxes:
			layout.addWidget(widget)
		# Set the layout.
		self.setLayout(layout)
		# Save that we have populated it.
		self.isPopulated = True

	def setState(self,name,state):
		""" Emit whether we add the page to the wizard or not. """
		# Every time a checkbox is clicked on or off, change the state in a dict accordingly.
		logging.critical("Setting state of {} to {}".format(name,bool(state)))
		self.wizardPages[name].enabled = bool(state)

		# Always update the flow or do it when the next button is clicked?
		self.updateFlow()

	def updateFlow(self):
		# Iterate over all the pages and set the nextId to the next True page.
		logging.critical("Updating flow for wizard.")
		pages = list(self.wizardPages.values())
		logging.critical("Pages: \n {}".format(pages))
		# Iterate over each page in the page list.
		for page in pages:
			# If the page is enabled, find the one that comes after it.
			if page.enabled:
				current_idx = pages.index(page)
				# Check each page after the current page index for the one that is next enabled.
				for i in range(current_idx+1,len(pages)):
					if pages[i].enabled:
						logging.critical("Setting {} nextId to {}".format(page,i))
						page.setNextId(i)
						# No need to search any further.
						break

	def setNextId(self,idx):
		self._nextId = idx

	def nextId(self):
		return self._nextId