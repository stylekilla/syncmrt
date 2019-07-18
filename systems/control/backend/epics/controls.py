import epics
import numpy as np
import logging
import time

class motor:
	def __init__(self,pv):
		# Initialise the thread.
		super().__init__()
		# Internal vars.
		self._pv = pv
		# PV vars.
		self.pv = {}
		self.pv['RBV'] = False
		self.pv['VAL'] = False
		self.pv['TWV'] = False
		self.pv['TWR'] = False
		self.pv['TWF'] = False
		self.pv['DMOV'] = False
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		try:
			# Read Back Value
			self.pv['RBV'] = epics.PV(self._pv+'.RBV')
		except:
			pass
		try:
			# Is motor moving?
			self.pv['DMOV'] = epics.PV(self._pv+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self._pv+'.VAL')
		except:
			pass
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self._pv+'.TWV')
		except:
			pass
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self._pv+'.TWR')
		except:
			pass
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self._pv+'.TWF')
		except:
			pass
		# Iterate over all PV's and see if any are disconnected. If any are disconnected, set the state to False.
		# If everything passes, set the state to True.
		state = True
		for key in self.pv:
			if self.pv[key] is False: state = False
		self._connected = state
		logging.info("Current connection status: {}".format(self._connected))

	def reconnect(self):
		self._connectPVs()

	def readValue(self,attribute):
		if self._connected is False:
			return None
		else:
			return self.pv[attribute].get()

	def writeValue(self,attribute,value):
		if self._connected is False: return None
		else: 
			if attribute == 'TWV':
				self.pv[attribute].put(value)
			else:
				while self.pv['DMOV'] == 0:
					pass
				self.pv[attribute].put(value)

	def read(self):
		# Straight up reading where the motor is.
		# if self._connected is False: return np.inf 
		if self._connected is False:
			return 72
		else:
			return self.pv['RBV'].get()

	def write(self,value,mode='absolute'):
		# logging.info("Writing {} to {} with mode {}.".format(value,self._pv,mode))
		if self._connected is False: return
		# Straight up telling the motor where to go.
		elif mode=='absolute':
			if self.pv['VAL']: self.pv['VAL'].put(float(value))
		elif mode=='relative':
			if self.pv['TWV']:
				# Place tweak value.
				self.pv['TWV'].put(float(np.absolute(value)))
				if value < 0:
					# Negative direction
					self.pv['TWR'].put(1)
				elif value > 0:
					self.pv['TWF'].put(1)
				else:
					# Do nothing.
					pass
		# Give epics 100ms to get the command to the motor.
		time.sleep(0.1)
		# Stay here while the motor is moving.
		while self.pv['DMOV'].get() == 0:
			pass
		# Finished.
		return

class detector:
	def __init__(self,pv):
		# Initialise the thread.
		super().__init__()
		# Internal vars.
		self._pv = pv
		# PV vars.
		self.pv = {}
		self.pv['CAM:Acquire'] = None
		self.pv['CAM:DataType_RBV'] = None
		self.pv['IMAGE:ArrayData'] = None
		self.pv['IMAGE:ArraySize0_RBV'] = None
		self.pv['IMAGE:ArraySize0_RBV'] = None
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pv['CAM:Acquire'] = epics.PV(self._pv+':CAM:Acquire',connection_timeout=1)
		self.pv['CAM:DataType_RBV'] = epics.PV(self._pv+':CAM:DataType_RBV',connection_timeout=1)
		self.pv['IMAGE:ArrayData'] = epics.PV(self._pv+':IMAGE:ArrayData',connection_timeout=1)
		self.pv['IMAGE:ArraySize0_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize0_RBV',connection_timeout=1)
		self.pv['IMAGE:ArraySize1_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize1_RBV',connection_timeout=1)
		# Connections.
		state = []
		for key in self.pv.keys():
			state.append(self.pv[key].wait_for_connection(timeout=1))

		if False in state:
			self._connected = False
			logging.critical("Could not connect to all the detector PV's. Refresh the connection.")
		else:
			self._connected = True

	def reconnect(self):
		for key in self.pv.keys():
			self.pv[key].connect(timeout=1)

	def readImage(self):
		if self._connected is False:
			return None
		else:
			self.pv['CAM:Acquire'].put(1)
			image = np.array(self.pv['IMAGE:ArrayData'].get(),dtype='uint16')
			x = self.pv['IMAGE:ArraySize1_RBV'].get()
			y = self.pv['IMAGE:ArraySize0_RBV'].get()

			return np.flipud(image.reshape(x,y))