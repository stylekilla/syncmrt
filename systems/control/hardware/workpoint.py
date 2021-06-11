from PyQt5 import QtCore
import numpy as np
import importlib
import logging

"""
Motor should run on it's own QThread.
Motor will emit finished signal after move is completed.
Should only use motor.read() and motor.write() methods.
"""

class workpoint(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	workpointSet = QtCore.pyqtSignal()
	workpointZeroed = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()

	def __init__(self,
				config,
				backend,
				backendThread=None,
			):
		super().__init__()
		# Backend Controller.
		backend = importlib.import_module(f"systems.control.backend.{backend}")
		self._controller = backend.tcp(config)
		# Move to thread if specified.
		if backendThread is not None:
			self._controller.moveToThread(backendThread)
		# Signals.
		self._controller.connected.connect(self.connected.emit)
		self._controller.disconnected.connect(self.disconnected.emit)
		self._controller.workpointSet.connect(self.workpointSet.emit)
		self._controller.workpointZeroed.connect(self.workpointZeroed.emit)
		self._controller.error.connect(self.error.emit)

	def isConnected(self):
		# Return True or False for the connection state of the motor.
		return self._controller.isConnected()

	def offset(self,offset):
		""" Offset the workpoint by an amount. """
		self._controller.offset(offset)

	def set(self,position):
		""" Set the workpoint to a position. """
		self._controller.set(position)

	def zero(self):
		""" Zero the workpoint. """
		self._controller.zero()

	def reconnectControls(self):
		try:
			self._controller.reconnect()
		except:
			self.error.emit()