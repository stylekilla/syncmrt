from PyQt5 import QtWidgets, QtGui, QtCore
from functools import partial
import QsWidgets
import logging

class QCtProperties(QtWidgets.QWidget):
	# Qt signals.
	align = QtCore.pyqtSignal(int)
	pickIsocenter = QtCore.pyqtSignal()
	isocenterUpdated = QtCore.pyqtSignal(float,float,float)
	toggleOverlay = QtCore.pyqtSignal(int,bool)
	updateCtView = QtCore.pyqtSignal(str,tuple,str,int)

	"""
	The structure of information held in this class is as follows:
		1.	self.group['groupname']
		2.	self.widget['groupname']['widgetname']
	"""

	def __init__(self):
		super().__init__()
		# Continue with sub-class initialisation.
		self.group = {}
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Overlays.
		self.widget['overlays'] = {}
		self.group['overlays'] = QtWidgets.QGroupBox()
		self.group['overlays'].setTitle('Plot Overlays')
		self.widget['overlays']['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['overlays']['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		lytOverlays = QtWidgets.QVBoxLayout()
		lytOverlays.addWidget(self.widget['overlays']['cbPatIsoc'])
		lytOverlays.addWidget(self.widget['overlays']['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['overlays']['cbPatIsoc'].stateChanged.connect(partial(self._emitToggleOverlay,'cbPatIsoc'))
		self.widget['overlays']['cbCentroid'].stateChanged.connect(partial(self._emitToggleOverlay,'cbCentroid'))
		# Group inclusion to page
		self.group['overlays'].setLayout(lytOverlays)
		self.layout.addWidget(self.group['overlays'])

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
		self.widget['isocenter']['editIsoH1'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('Vertical: ')
		self.widget['isocenter']['editIsoV'] = QtWidgets.QLineEdit()
		label4 = QtWidgets.QLabel('Horizontal 2: ')
		self.widget['isocenter']['editIsoH2'] = QtWidgets.QLineEdit()
		self.widget['isocenter']['pick'] = QtWidgets.QPushButton("Pick")
		# Signals.
		self.widget['isocenter']['pick'].clicked.connect(self.pickIsocenter.emit)
		# Layout
		lytEditIsocenter = QtWidgets.QFormLayout()
		lytEditIsocenter.setContentsMargins(0,0,0,0)
		lytEditIsocenter.addRow(label1,self.widget['isocenter']['pick'])
		lytEditIsocenter.addRow(label2,self.widget['isocenter']['editIsoH1'])
		lytEditIsocenter.addRow(label3,self.widget['isocenter']['editIsoV'])
		lytEditIsocenter.addRow(label4,self.widget['isocenter']['editIsoH2'])
		self.widget['isocenter']['editIso'].setLayout(lytEditIsocenter)
		# Validators.
		doubleValidator = QtGui.QDoubleValidator()
		doubleValidator.setDecimals(3)
		self.widget['isocenter']['editIsoH1'].setText('0')
		self.widget['isocenter']['editIsoH2'].setText('0')
		self.widget['isocenter']['editIsoV'].setText('0')
		self.widget['isocenter']['editIsoH1'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoH2'].setValidator(doubleValidator)
		self.widget['isocenter']['editIsoV'].setValidator(doubleValidator)
		# Defaults
		self.widget['isocenter']['editIso'].setEnabled(False)
		self.widget['isocenter']['editIso'].setVisible(False)
		# Signals and Slots
		self.widget['isocenter']['editIsoH1'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoH2'].editingFinished.connect(self._updateIsocenter)
		self.widget['isocenter']['editIsoV'].editingFinished.connect(self._updateIsocenter)
		# Set the layout of group.
		lytIsocenter.addWidget(self.widget['isocenter']['cbCustomIsoc'])
		lytIsocenter.addWidget(self.widget['isocenter']['editIso'])
		self.group['isocenter'].setLayout(lytIsocenter)
		# Add group to sidebar layout.
		self.layout.addWidget(self.group['isocenter'])

		# Group: View.
		self.group['view'] = QtWidgets.QGroupBox()
		self.group['view'].setTitle('CT View')
		view = QtWidgets.QLabel('Primary View:')
		# Combo box selection.
		self.widget['view'] = {}
		self.widget['view']['2D'] = QtWidgets.QRadioButton('2D')
		self.widget['view']['3D'] = QtWidgets.QRadioButton('3D')
		viewOptions = QtWidgets.QWidget()
		viewOptionsLayout = QtWidgets.QHBoxLayout()
		viewOptionsLayout.addWidget(self.widget['view']['2D'])
		viewOptionsLayout.addWidget(self.widget['view']['3D'])
		viewOptions.setLayout(viewOptionsLayout)
		self.widget['view']['select'] = QtWidgets.QComboBox()
		self.widget['view']['select'].addItem("Coronal (AP)")
		self.widget['view']['select'].addItem("Coronal (PA)")
		# Range slider.
		self.widget['view']['xrange'] = QsWidgets.QRangeList('Horizontal 1:')
		self.widget['view']['yrange'] = QsWidgets.QRangeList('Vertical:')
		self.widget['view']['zrange'] = QsWidgets.QRangeList('Horizontal 2:')
		# Flattening options.
		self.widget['view']['sum'] = QtWidgets.QRadioButton('Sum')
		self.widget['view']['max'] = QtWidgets.QRadioButton('Max')
		flatteningOptions = QtWidgets.QWidget()
		flatteningOptionsLayout = QtWidgets.QHBoxLayout()
		flatteningOptionsLayout.addWidget(self.widget['view']['sum'])
		flatteningOptionsLayout.addWidget(self.widget['view']['max'])
		flatteningOptions.setLayout(flatteningOptionsLayout)
		self.widget['view']['sum'].setChecked(True)
		self.widget['view']['3D'].setChecked(True)
		self.widget['view']['apply'] = QtWidgets.QPushButton('Apply')
		self.widget['view']['apply'].clicked.connect(self._emitUpdateCtView)
		# Layout
		viewGroupLayout = QtWidgets.QVBoxLayout()
		viewGroupLayout.addWidget(view)
		viewGroupLayout.addWidget(self.widget['view']['select'])
		viewGroupLayout.addWidget(viewOptions)
		viewGroupLayout.addWidget(QtWidgets.QLabel("CT ROI (DICOM):"))
		viewGroupLayout.addWidget(self.widget['view']['xrange'])
		viewGroupLayout.addWidget(self.widget['view']['yrange'])
		viewGroupLayout.addWidget(self.widget['view']['zrange'])
		viewGroupLayout.addWidget(flatteningOptions)
		viewGroupLayout.addWidget(self.widget['view']['apply'])
		# Defaults
		self.group['view'].setEnabled(False)
		self.widget['view']['select'].setCurrentIndex(0)
		# Signals and Slots
		# self.widget['view']['select'].currentIndexChanged.connect(self._emitUpdateCtView)
		# Group inclusion to page
		self.group['view'].setLayout(viewGroupLayout)
		self.layout.addWidget(self.group['view'])

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
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

	def setIsocenter(self,h1,h2,v):
		""" Set the isocenter from an external source. """
		self.blockSignals(True)
		self.widget['isocenter']['editIsoH1'].setText("{:.2f}".format(h1))
		self.widget['isocenter']['editIsoH2'].setText("{:.2f}".format(h2))
		self.widget['isocenter']['editIsoV'].setText("{:.2f}".format(v))
		self.blockSignals(False)
		# Turn the overlays on.
		self.widget['overlays']['cbPatIsoc'].setChecked(True)

	def _updateIsocenter(self):
		""" Send a signal with updated x,y coordinates. """
		h1 = float(self.widget['isocenter']['editIsoH1'].text())
		h2 = float(self.widget['isocenter']['editIsoH2'].text())
		v = float(self.widget['isocenter']['editIsoV'].text())
		self.isocenterUpdated.emit(h1,h2,v)
		# Turn the overlays on.
		self.widget['overlays']['cbPatIsoc'].setChecked(True)
		
	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in reversed(range(layout.count())): 
			layout.itemAt(i).widget().setParent(None)
		# New widgets.
		for i in range(len(widget)):
			widget[i].setMaximumHeight(200)
			layout.addWidget(widget[i])

	def _emitUpdateCtView(self):
		# Get the CT ROI values.
		_x = self.widget['view']['xrange'].getRange()
		_y = self.widget['view']['yrange'].getRange()
		_z = self.widget['view']['zrange'].getRange()
		roi = _x+_y+_z
		# If a None value is returned then do not send the signal.
		if None in roi: return
		# Get the view.
		view = self.widget['view']['select'].currentText()[-3:-1]
		# Get the mode.
		if self.widget['view']['sum'].isChecked(): mode = 'sum'
		elif self.widget['view']['max'].isChecked(): mode = 'max'
		# Get the mode.
		if self.widget['view']['2D'].isChecked(): projections = 1
		elif self.widget['view']['3D'].isChecked(): projections = 2
		# Send the signal.
		self.updateCtView.emit(view,roi,mode,projections)

	def _emitToggleOverlay(self,button,state):
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

	def setCtRoi(self,extent):
		""" Use an array shape to set the sliders XYZ. """
		self.widget['view']['xrange'].setRange([extent[0],extent[1]])
		self.widget['view']['yrange'].setRange([extent[2],extent[3]])
		self.widget['view']['zrange'].setRange([extent[4],extent[5]])
