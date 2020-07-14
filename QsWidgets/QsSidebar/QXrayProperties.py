from PyQt5 import QtWidgets, QtCore
from functools import partial
import logging

class QXrayProperties(QtWidgets.QWidget):
	toggleOverlay = QtCore.pyqtSignal(int,bool)
	isocenterUpdated = QtCore.pyqtSignal(float,float,float)
	pickIsocenter = QtCore.pyqtSignal()
	align = QtCore.pyqtSignal(int)

	def __init__(self,parent=None):
		super().__init__()
		# self.parent = parent
		self.widget = {}
		self.group = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 2: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbBeamIsoc'] = QtWidgets.QCheckBox('Beam Isocenter')
		self.widget['cbBeamIsoc'].setToolTip("Shows the synchrotron beam centre.")
		self.widget['cbBeamOverlay'] = QtWidgets.QCheckBox('Beam Overlay')
		self.widget['cbBeamOverlay'].setToolTip("Shows the area to be irradiated.")
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbPatIsoc'].setToolTip("Shows the tumour centre.")
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		self.widget['cbCentroid'].setToolTip("Shows the centre of mass of all selected points.")
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbBeamIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbBeamOverlay'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['cbBeamIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbBeamIsoc'))
		self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
		self.widget['cbBeamOverlay'].stateChanged.connect(partial(self.emitToggleOverlay,'cbBeamOverlay'))
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 2: Editable Isocenter.
		self.widget['isocenter'] = {}
		self.group['isocenter'] = QtWidgets.QGroupBox()
		self.group['isocenter'].setTitle('Tumour Isocenter')
		lytIsocenter = QtWidgets.QVBoxLayout()
		# Add toggle checkbox.
		self.widget['isocenter']['cbCustomIsoc'] = QtWidgets.QCheckBox('Set Custom Isocenter')
		self.widget['isocenter']['cbCustomIsoc'].setToolTip("If enabled, allows the user to set a custom target position.")
		self.widget['isocenter']['cbCustomIsoc'].stateChanged.connect(self._toggleCustomIsocenter)
		# Create an isocenter widget with XYZ toggles in it.
		self.widget['isocenter']['editIso'] = QtWidgets.QWidget()
		label1 = QtWidgets.QLabel('Isocenter (mm)')
		label2 = QtWidgets.QLabel('Horizontal 1: ')
		self.widget['isocenter']['editIsoX'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('Vertical: ')
		self.widget['isocenter']['editIsoY'] = QtWidgets.QLineEdit()
		label4 = QtWidgets.QLabel('Horizontal 2: ')
		self.widget['isocenter']['editIsoZ'] = QtWidgets.QLineEdit()
		self.widget['isocenter']['pick'] = QtWidgets.QPushButton("Pick")
		self.widget['isocenter']['align'] = QtWidgets.QPushButton("Align")
		# Signals.
		self.widget['isocenter']['pick'].clicked.connect(self.pickIsocenter.emit)
		# Layout
		lytEditIsocenter = QtWidgets.QFormLayout()
		lytEditIsocenter.setContentsMargins(0,0,0,0)
		lytEditIsocenter.addRow(label1,self.widget['isocenter']['pick'])
		lytEditIsocenter.addRow(label2,self.widget['isocenter']['editIsoX'])
		lytEditIsocenter.addRow(label3,self.widget['isocenter']['editIsoY'])
		lytEditIsocenter.addRow(label4,self.widget['isocenter']['editIsoZ'])
		self.widget['isocenter']['editIso'].setLayout(lytEditIsocenter)
		# Validators.
		doubleValidator = QtGui.QDoubleValidator()
		doubleValidator.setDecimals(3)
		self.widget['isocenter']['editIsoX'].setText('0')
		self.widget['isocenter']['editIsoY'].setText('0')
		self.widget['isocenter']['editIsoZ'].setText('0')
		self.widget['isocenter']['editIsoX'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoY'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoZ'].setValidator(doubleValidator)
		# Defaults
		self.widget['isocenter']['editIso'].setEnabled(False)
		self.widget['isocenter']['editIso'].setVisible(False)
		self.widget['isocenter']['align'].setEnabled(False)
		self.widget['isocenter']['align'].setVisible(False)
		# Signals and Slots
		self.widget['isocenter']['editIsoX'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoY'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoZ'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['align'].clicked.connect(partial(self.align.emit,-1))
		# Set the layout of group.
		lytIsocenter.addWidget(self.widget['isocenter']['cbCustomIsoc'])
		lytIsocenter.addWidget(self.widget['isocenter']['editIso'])
		lytIsocenter.addWidget(self.widget['isocenter']['align'])
		self.group['isocenter'].setLayout(lytIsocenter)
		# Add group to sidebar layout.
		self.layout.addWidget(self.group['isocenter'])

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('X-ray Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		self.window['layout'].setContentsMargins(0,0,0,0)
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def _toggleCustomIsocenter(self,state):
		""" Toggles the manual setting of the isocenter on and off. """
		self.widget['isocenter']['editIso'].setEnabled(bool(state))
		self.widget['isocenter']['editIso'].setVisible(bool(state))
		self.widget['isocenter']['align'].setEnabled(bool(state))
		self.widget['isocenter']['align'].setVisible(bool(state))

	def setIsocenter(self,x,y,z):
		""" Set the isocenter from an external source. """
		self.blockSignals(True)
		self.widget['isocenter']['editIsoX'].setText("{:.2f}".format(x))
		self.widget['isocenter']['editIsoY'].setText("{:.2f}".format(y))
		self.widget['isocenter']['editIsoZ'].setText("{:.2f}".format(z))
		self.blockSignals(False)

	def _updateIsocenter(self):
		""" Send a signal with updated x,y coordinates. """
		_x = float(self.widget['isocenter']['editIsoX'].text())
		_y = float(self.widget['isocenter']['editIsoY'].text())
		_z = float(self.widget['isocenter']['editIsoZ'].text())
		self.isocenterUpdated.emit(_x,_y,_z)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().setParent(None)
		# New widgets.
		for i in range(len(widget)):
			widget[i].setMaximumHeight(200)
			layout.addWidget(widget[i])

	def emitToggleOverlay(self,button,state):
		setState = False
		# Identify true or false.
		if state == 0: setState = False
		elif state == 2: setState = True
		# Send the signal.
		if button == 'cbCentroid': self.toggleOverlay.emit(0,setState)
		elif button == 'cbBeamIsoc': self.toggleOverlay.emit(1,setState)
		elif button == 'cbPatIsoc': self.toggleOverlay.emit(2,setState)
		elif button == 'cbBeamOverlay': self.toggleOverlay.emit(3,setState)

	def refreshOverlays(self):
		for item in ['cbBeamIsoc','cbPatIsoc','cbCentroid','cbBeamOverlay']:
			# Toggle them on and off to refresh them.
			self.widget[item].toggle()
			self.widget[item].toggle()
