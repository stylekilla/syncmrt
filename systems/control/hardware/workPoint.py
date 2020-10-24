from systems.control.backend import epics as backend
from PyQt5 import QtCore
import numpy as np
import logging

"""
Motor should run on it's own QThread.
Motor will emit finished signal after move is completed.
Should only use motor.read() and motor.write() methods.
"""

class workPoint(QtCore.QObject):
	connected = QtCore.pyqtSignal()
	disconnected = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()

	def __init__(self,
				pv,
				backendThread=None,
			):
		super().__init__()
		# PV Base.
		self.pv = pv
		# Backend Controller.
		self._controller = backend.tcp(self.pv)
		# Move to thread if specified.
		if backendThread is not None:
			self._controller.moveToThread(backendThread)
		# Signals.
		self._controller.connected.connect(self.connected.emit)
		self._controller.disconnected.connect(self.disconnected.emit)
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

	def reconnectControls(self):
		try:
			self._controller.reconnect()
		except:
			self.error.emit()