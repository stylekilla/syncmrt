from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

class QTreatment(QtWidgets.QWidget):
	calculate = QtCore.pyqtSignal(int)
	align = QtCore.pyqtSignal(int)
	deliver = QtCore.pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Treatment Settings
		settingsGroup = QtWidgets.QGroupBox()
		settingsGroup.setTitle('Description')
		label1 = QtWidgets.QLabel('Number of beams: ')
		self.widget['quantity'] = QtWidgets.QLabel()
		# Layout
		settingsGroupLayout = QtWidgets.QFormLayout()
		settingsGroupLayout.addRow(label1,self.widget['quantity'])
		settingsGroup.setLayout(settingsGroupLayout)
		self.layout.addWidget(settingsGroup)
		# Defaults
		self.widget['quantity'].setText(str(0))
		# Signals and Slots

		# Group 2: Deliver Treatment
		# Dict for beam plan group widgets.
		self.widget['beamGroup'] = QtWidgets.QGroupBox()
		self.widget['beamGroup'].setVisible(False)
		self.widget['beamGroup'].setTitle('Beam Sequence')
		# Empty Layout, start by saying no RTPLAN loaded.
		self.widget['beamSequence'] = QtWidgets.QFormLayout()
		self.widget['noTreatment'] = QtWidgets.QLabel('No Treatment Plan loaded.')
		self.widget['beamSequence'].addRow(self.widget['noTreatment'])
		self.widget['beamGroup'].setLayout(self.widget['beamSequence'])
		self.layout.addWidget(self.widget['beamGroup'])
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)

	def populateTreatments(self):
		""" Once treatment plan is loaded, add the treatments to the workflow. """
		# Remove the no treatment widget.
		self.widget['noTreatment'].deleteLater()
		del self.widget['noTreatment']
		# Enable the group widget again.
		self.widget['beamGroup'].setVisible(True)
		self.widget['beam'] = [None]*int(self.widget['quantity'].text())
		# sequenceLayout = QtWidgets.QFormLayout()
		# For each beam specified in the count, add a set of buttons.
		for i in range(int(self.widget['quantity'].text())):
			self.widget['beam'][i] = {}
			label = QtWidgets.QLabel(str('Beam %i'%(i+1)))
			# sequenceGroup = QtWidgets.QGroupBox()

			self.widget['beam'][i]['calculate'] = QtWidgets.QPushButton('Calculate')
			self.widget['beam'][i]['align'] = QtWidgets.QPushButton('Align')
			# self.widget['beam'][i]['hline'] = QHLine()
			self.widget['beam'][i]['interlock'] = QtWidgets.QCheckBox('Interlock')
			self.widget['beam'][i]['deliver'] = QtWidgets.QPushButton('Deliver')
			# Layout
			self.widget['beamSequence'].addRow(label)
			self.widget['beamSequence'].addRow(self.widget['beam'][i]['calculate'],self.widget['beam'][i]['align'])
			self.widget['beamSequence'].addRow(QHLine())
			self.widget['beamSequence'].addRow(self.widget['beam'][i]['interlock'],self.widget['beam'][i]['deliver'])
			# Defaults
			self.widget['beam'][i]['alignmentComplete'] = False
			self.widget['beam'][i]['interlock'].setChecked(True)
			self.widget['beam'][i]['interlock'].setEnabled(False)
			self.widget['beam'][i]['deliver'].setEnabled(False)
			# Signals and Slots
			self.widget['beam'][i]['calculate'].clicked.connect(partial(self._emitCalculate,i))
			self.widget['beam'][i]['align'].clicked.connect(partial(self._emitAlign,i))
			self.widget['beam'][i]['interlock'].stateChanged.connect(partial(self.treatmentInterlock,i))
			self.widget['beam'][i]['deliver'].clicked.connect(partial(self._disableTreatmentDelivery,i))

	def _emitCalculate(self,_id):
		self.calculate.emit(_id)

	def _emitAlign(self,_id):
		self.align.emit(_id)

	def treatmentInterlock(self,index):
		'''Treatment interlock stops treatment from occuring. Requires alignment to be done first.'''
		# Enable interlock button.
		if self.widget['beam'][index]['alignmentComplete'] == True:
			self.widget['beam'][index]['interlock'].setEnabled(True)

		# Enable widget delivery button.
		if self.widget['beam'][index]['interlock'].isChecked():
			self.widget['beam'][index]['deliver'].setEnabled(False)
		else:
			self.widget['beam'][index]['deliver'].setEnabled(True)

	def _disableTreatmentDelivery(self, i):
		self.widget['beam'][i]['interlock'].setEnabled(False)
		self.widget['beam'][i]['deliver'].setEnabled(False)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout
