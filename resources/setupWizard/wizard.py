from PyQt5 import QtWidgets
from .start import Start
from .markers import Markers
from .detector import Detector
from .resources import Resources
from .finish import Finish
from collections import OrderedDict
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
		# self.pages['Finish'].finished.connect(self.updateConfig)

		for key in self.pages:
			self.addPage(self.pages[key])

		self.pages['Start'].setCheckBoxes(self.pages)

	# def all_field_names(self):
		# return {s for page_id in self.pageIds() for s in self.page(page_id).field_names}