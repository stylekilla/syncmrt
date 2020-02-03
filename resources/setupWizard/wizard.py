from PyQt5 import QtWidgets
from .start import Start
from .markers import Markers
from .detector import Detector
from .resources import Resources
from .finish import Finish
from collections import OrderedDict
from functools import partial
import logging

class Wizard(QtWidgets.QWizard):
	def __init__(self,config,parent=None):
		super().__init__(parent)
		# Save the config file.
		self.config = config
		self.pages = OrderedDict()
		self.showPages = set()

		# Begin the wizard with the start page.
		self.pages['Start'] = Start()
		self.pages['Markers'] = Markers(self.config.data['markers'])
		self.pages['Detector'] = Detector(self.config.data['imager'])
		self.pages['Resources'] = Resources(self.config.data['files'])
		self.pages['Finish'] = Finish()

		for key in self.pages:
			self.pages[key].settingsUpdated.connect(partial(self.updateConfig,key))
			self.addPage(self.pages[key])

		self.pages['Start'].setCheckBoxes(self.pages)

	def updateConfig(self,page):
		data = self.pages[page].getData()
		for key, value in data.items():
			self.config.data[self.pages[page].configSection][key] = value
		logging.critical("Updating config.")
		self.config.save()