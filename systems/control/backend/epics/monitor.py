import epics
from PyQt5 import QtCore
import logging

__all__ = ['EpicsMonitor']

class EpicsMonitor(QtCore.QObject):
	pvUpdated = QtCore.pyqtSignal(str,float)

	def __init__(self):
		super().__init__()
		# Create a dict of things to monitor.
		self.pvs = {}

	def addPV(self,pvName,displayName):
		# Set the display name for the pv.
		if displayName is not '':
			name = str(displayName)
		else:
			name = str(pvName)

		# Store the pvname and monitoring function.
		self.pvs[name] = epics.PV(str(pvName),auto_monitor=True,callback=self.update)
		logging.info("Monitoring PV {}".format(pvName))

	def removePV(self,pvName):
		# Remove the PV and disconnect all callbacks.
		self.pvs[pvName].disconnect()
		# Remove from the dict.
		del self.pvs[pvName]

	def update(self,*args,**kwargs):
		# Emit the signal with the pvname and updated value.
		try:
			self.pvUpdated.emit(kwargs['pvname'],kwargs['value'])
		except:
			logging.critical("Failed to emit updated pv value with: {}, {}".format(args,kwargs))

		# Would be good to include alarm limits.


# https://cars9.uchicago.edu/software/python/pyepics3/pv.html#pv-callbacks-label
# pvname: the name of the pv
# value: the latest value
# char_value: string representation of value
# count: the number of data elements
# ftype: the numerical CA type indicating the data type
# type: the python type for the data
# status: the status of the PV (1 for OK)
# precision: number of decimal places of precision for floating point values
# units: string for PV units
# severity: PV severity
# timestamp: timestamp from CA server.
# read_access: read access (True/False)
# write_access: write access (True/False)
# access: string description of read- and write-access
# host: host machine and CA port serving PV
# enum_strs: the list of enumeration strings
# upper_disp_limit: upper display limit
# lower_disp_limit: lower display limit
# upper_alarm_limit: upper alarm limit
# lower_alarm_limit: lower alarm limit
# upper_warning_limit: upper warning limit
# lower_warning_limit: lower warning limit
# upper_ctrl_limit: upper control limit
# lower_ctrl_limit: lower control limit
# chid: integer channel ID
# cb_info: (index, self) tuple containing callback ID