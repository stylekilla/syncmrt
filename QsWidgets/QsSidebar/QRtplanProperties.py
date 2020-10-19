from PyQt5 import QtWidgets, QtCore
from functools import partial
from resources import config
import QsWidgets
import logging

class QRtplanProperties(QtWidgets.QWidget):
	# Qt signals.
	toggleOverlay = QtCore.pyqtSignal(int,bool)

	def __init__(self):
		# Init QObject class.
		super().__init__()
		# Continue with sub-class initialisation.
		self.group = {}
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbMask'] = QtWidgets.QCheckBox('Isocenter Mask')
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbMask'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		self.widget['cbPatIsoc'].stateChanged.connect(partial(self.emitToggleOverlay,'cbPatIsoc'))
		self.widget['cbMask'].stateChanged.connect(partial(self.emitToggleOverlay,'cbMask'))
		self.widget['cbCentroid'].stateChanged.connect(partial(self.emitToggleOverlay,'cbCentroid'))
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		# spacer = QtWidgets.QSpacerItem(0,0)
		# self.layout.addSpacerItem(spacer)
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in range(layout.count()):
			layout.removeItem(i)
		# New widgets.
		for i in range(len(widget)):
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
		elif button == 'cbMask': self.toggleOverlay.emit(3,setState)
		else: logging.critical('Cannot set button '+str(button)+' to state '+str(setState)+'.')
