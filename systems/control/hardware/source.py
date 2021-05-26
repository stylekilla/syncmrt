from PyQt5 import QtCore
from systems.control.backend import epics as backend
import logging

class source(QtCore.QObject):
	# Beam signals.
	on = QtCore.pyqtSignal()
	off = QtCore.pyqtSignal()
	state = QtCore.pyqtSignal(bool)
	# Shutter signals.
	shutterOpen = QtCore.pyqtSignal()
	shutterClosed = QtCore.pyqtSignal()
	shutterState = QtCore.pyqtSignal(bool)

	def __init__(self,name,config):
		super().__init__()
		# Set the name.
		self.name = str(name)
		self._controller = backend.source(name,config.SOURCE_PVS)
		# Signals passthrough.
		self._controller.on.connect(self.on.emit)
		self._controller.off.connect(self.off.emit)
		self._controller.state.connect(self.state.emit)
		self._controller.shutterOpen.connect(self.shutterOpen.emit)
		self._controller.shutterClosed.connect(self.shutterClosed.emit)
		self._controller.shutterState.connect(self.shutterState.emit)

	def turnOn(self):
		""" Turn the beam on. """
		self._controller.turnOn()

	def turnOff(self):
		""" Turn the beam off. """
		self._controller.turnOff()

	def openShutter(self):
		""" Open the shutter. """
		self._controller.openShutter()

	def closeShutter(self):
		""" Close the shutter. """
		self._controller.closeShutter()