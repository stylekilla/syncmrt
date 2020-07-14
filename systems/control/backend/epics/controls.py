import epics
import numpy as np
import logging
import time

"""
Definitely have a look at: https://cars9.uchicago.edu/software/python/pyepics3/devices.html
Includes Motor and Device class!
"""

class motor:
	def __init__(self,pv):
		# Initialise the thread.
		super().__init__()
		# Base PV.
		self._pv = str(pv)
		# PV vars.
		self.pv = {}
		# self.pv['RBV'] = False # read back value (position)
		# self.pv['VAL'] = False # position at value (absolute)
		# self.pv['TWV'] = False # tweak value (relative )
		# self.pv['TWR'] = False # tweak value reverse (relative backwards)
		# self.pv['TWF'] = False # tweak value forward
		# self.pv['DMOV'] = False # detector moving (1 is 'finished move')
		# self.pv['HLM'] = False # High motor limit
		# self.pv['LLM'] = False # Low motor limit
		# self.pv['BDST'] = False # Backlash distance
		# self.pv['BVEL'] = False # Backlash velocity
		# self.pv['BACC'] = False # Backlash acceleration
		# self.pv['DESC'] = False # Description of the motor (i.e. name)
		# Connection status per motor.
		self._connected = {}
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		# Read Back Value
		self.pv['RBV'] = epics.PV(self._pv+'.RBV',connection_callback=self._updateConnectionStatus)
		# Is motor moving?
		self.pv['DMOV'] = epics.PV(self._pv+'.DMOV',connection_callback=self._updateConnectionStatus)
		# Value to put to moto,wait=Truer
		self.pv['VAL'] = epics.PV(self._pv+'.VAL',connection_callback=self._updateConnectionStatus)
		# Tweak Value
		self.pv['TWV'] = epics.PV(self._pv+'.TWV',connection_callback=self._updateConnectionStatus)
		# Tweak Reverse
		self.pv['TWR'] = epics.PV(self._pv+'.TWR',connection_callback=self._updateConnectionStatus)
		# Tweak Forward
		self.pv['TWF'] = epics.PV(self._pv+'.TWF',connection_callback=self._updateConnectionStatus)
		#High limit of motor range
		self.pv['HLM'] = epics.PV(self._pv+'.HLM',connection_callback=self._updateConnectionStatus)
		#Low limit of motor range
		self.pv['LLM'] = epics.PV(self._pv+'.LLM',connection_callback=self._updateConnectionStatus)
		#Backlash distance
		self.pv['BDST'] = epics.PV(self._pv+'.BDST',connection_callback=self._updateConnectionStatus)
		#Backlash velocity
		self.pv['BVEL'] = epics.PV(self._pv+'.BVEL',connection_callback=self._updateConnectionStatus)
		#Backlash acceleration
		self.pv['BACC'] = epics.PV(self._pv+'.BACC',connection_callback=self._updateConnectionStatus)
		#Name of the pv
		self.pv['DESC'] = epics.PV(self._pv+'.DESC',connection_callback=self._updateConnectionStatus)

		# Connection status per motor. Set to false by default.
		for pv in self.pv.values():
			self._connected[pv.pvname] = False

	def reconnect(self):
		# Reconnect the pv's.
		for pv in self.pv.values():
			pv.reconnect()
		# Return if they are now connected or not.
		connected = self.isConnected()
		return connected

	def _updateConnectionStatus(self,pvname,conn,*args,**kwargs):
		# Update connection status per PV.
		self._connected[pvname] = conn

	def isConnected(self):
		# Return True or False for if all the PV's are connected or not.
		return all(self._connected.values())

	def readValue(self,attribute):
		if self.isConnected():
			return self.pv[attribute].get()
		else:
			return None

	def writeValue(self,attribute,value):
		if self.isConnected(): 
			if attribute == 'TWV':
				self.pv[attribute].put(value,wait=True)
			else:
				while self.pv['DMOV'].get() == 0:
					pass
				self.pv[attribute].put(value,wait=True)
		else: 
			return None

	def read(self):
		# Straight up reading where the motor is.
		if self.isConnected():
			return self.pv['RBV'].get()
		else:
			return -999

	def write(self,value,mode='absolute'):
		# logging.info("Writing {} to {} with mode {}.".format(value,self._pv,mode))
		if not self.isConnected(): 
			return
		# Straight up telling the motor where to go.
		elif mode=='absolute':
			if self.pv['VAL']: 
				oldPosition = self.read()
				predictedPosition = float(value)
				if self.checkAbsLimit(value):
					self.pv['VAL'].put(float(value),wait=True)
				else:
					# logging.error("Cannot move {} to {} - motorlimit will be reached.\nH.Lim:{}\tL.Lim:{}".format(self.pv['DESC'].get(),value,self.pv['HLM'].get(),self.pv['LLM'].get()))
					return

		elif mode=='relative':
			if self.pv['TWV']:
				oldPosition = self.read()
				predictedPosition = oldPosition + float(value)
				if self.checkRelLimit(value):
					# Place tweak value.
					self.pv['TWV'].put(float(np.absolute(value)),wait=True)
					if value < 0:
						# Negative direction
						self.pv['TWR'].put(1,wait=True)
					elif value > 0:
						self.pv['TWF'].put(1,wait=True)
					else:
						# Do nothing.
						pass
				else: 
					logging.error("Cannot move {} by {} - motorlimit will be reached.\nH.Lim:{}\tL.Lim:{}".format(self.pv['DESC'].get(),value,self.pv['HLM'].get(),self.pv['LLM'].get()))
					return

		# Give epics 100ms to get the command to the motor.
		time.sleep(0.2)
		# Stay here while the motor is moving.
		while self.pv['DMOV'].get() == 0:
			pass
		# Finished.

		# Checking that the move occurred.
		newPosition = self.read()
		retryCounter = 0
		maxRetrties = 3
		BDST=self.pv['BDST'].get()

		while (abs(newPosition-predictedPosition) > BDST) and (retryCounter < maxRetrties): 
			logging.error("Motor {} did not move to {}. Retry #{} of {}.".format(self.pv['DESC'].get(), predictedPosition,retryCounter + 1, maxRetrties))
			self.pv['VAL'].put(predictedPosition,wait=True)
			time.sleep(0.2)
			while self.pv['DMOV'].get() == 0:
				pass
			retryCounter+=1
			newPosition=self.read()
		# if (newPosition != predictedPosition) and (retryCounter == maxRetrties):
			# logging.error("Was unable to complete the movement after {} tries.".format(maxRetrties))
		return

	def checkAbsLimit(self,value):
		stillInLimitBool = False
		if float(value) <= float(self.pv['HLM'].get()) and float(value) >= float(self.pv['LLM'].get()):
			stillInLimitBool = True
		return stillInLimitBool

	def checkRelLimit(self,value):
		stillInLimitBool = False
		if (float(value) + float(self.pv['RBV'].get())) >= float(self.pv['LLM'].get()) and (float(value) + float(self.pv['RBV'].get())) <= float(self.pv['HLM'].get()):
				stillInLimitBool=True
		return stillInLimitBool

class detector:
	def __init__(self,pv):
		# Initialise the thread.
		super().__init__()
		# PV Base.
		self._pv = pv
		# PV vars.
		self.pv = {}
		# Connection status per motor.
		self._connected = {}
		self.pv['CAM:Acquire'] = None
		self.pv['CAM:DataType_RBV'] = None
		self.pv['IMAGE:ArrayData'] = None
		self.pv['IMAGE:ArraySize0_RBV'] = None
		self.pv['IMAGE:ArraySize1_RBV'] = None
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pv['CAM:Acquire'] = epics.PV(self._pv+':CAM:Acquire',connection_callback=self._updateConnectionStatus)
		self.pv['CAM:DataType_RBV'] = epics.PV(self._pv+':CAM:DataType_RBV',connection_callback=self._updateConnectionStatus)
		self.pv['IMAGE:ArrayData'] = epics.PV(self._pv+':IMAGE:ArrayData',connection_callback=self._updateConnectionStatus)
		# self.pv['IMAGE:ArraySize0_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize0_RBV',connection_timeout=1)
		# self.pv['IMAGE:ArraySize1_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize1_RBV',connection_timeout=1)

		# Connection status per motor. Set to false by default.
		for pv in self.pv.values():
			self._connected[pv.pvname] = False

	def reconnect(self):
		# Reconnect the pv's.
		for pv in self.pv.values():
			pv.reconnect()
		# Return if they are now connected or not.
		connected = self.isConnected()
		return connected

	def _updateConnectionStatus(self,pvname,conn,*args,**kwargs):
		# Update connection status per PV.
		self._connected[pvname] = conn

	def isConnected(self):
		# Return True or False for if all the PV's are connected or not.
		return all(self._connected.values())

	def readImage(self):
		if self._connected is False:
			return None
		else:
			# Tell the detector to acquire.
			self.pv['CAM:Acquire'].put(1,wait=True)
			# Sleep for the acquisition period.
			image = self.pv['IMAGE:ArrayData'].get()
			# Grab image shape.
			x = self.pv['IMAGE:ArraySize1_RBV'].get()
			y = self.pv['IMAGE:ArraySize0_RBV'].get()
			logging.info("Flipping RUBY images because it is retarded.")
			return np.flipud(image.reshape(x,y))
			# return np.fliplr(np.flipud(image.reshape(x,y)))
