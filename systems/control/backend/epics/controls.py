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
		# Internal vars.
		self._pv = pv
		# PV vars.
		self.pv = {}
		self.pv['RBV'] = False #read back value (position)
		self.pv['VAL'] = False #position at value (absolute)
		self.pv['TWV'] = False #tweak value (relative )
		self.pv['TWR'] = False #tweak value reverse (relative backwards)
		self.pv['TWF'] = False #tweak value forward
		self.pv['DMOV'] = False #detector moving (1 is 'finished move')
		self.pv['HLM'] = False #High motor limit
		self.pv['LLM'] = False #Low motor limit
		self.pv['BDST'] = False #Backlash distance
		self.pv['BVEL'] = False #Backlash velocity
		self.pv['BACC'] = False #Backlash acceleration
		self.pv['DESC'] = False #Description of the motor (i.e. name)
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
		try:
			#High limit of motor range
			self.pv['HLM'] = epics.PV(self._pv+'.HLM')
		except:
			pass
		try:
			#Low limit of motor range
			self.pv['LLM'] = epics.PV(self._pv+'.LLM')
		except:
			pass
		try:
			#Backlash distance
			self.pv['BDST'] = epics.PV(self._pv+'.BDST')
		except:
			pass
		try:
			#Backlash velocity
			self.pv['BVEL'] = epics.PV(self._pv+'.BVEL')
		except:
			pass
		try:
			#Backlash acceleration
			self.pv['BACC'] = epics.PV(self._pv+'.BACC')
		except:
			pass
		try:
			#Name of the pv
			self.pv['DESC'] = epics.PV(self._pv+'.DESC')
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
			if self.pv['VAL']: 
				oldPosition = self.read()
				predictedPosition = float(value)
				if self.checkAbsLimit(value):
					self.pv['VAL'].put(float(value))
				else:
					logging.error("Cannot move {} to {} - motorlimit will be reached.\nH.Lim:{}\tL.Lim:{}".format(self.pv['DESC'],value,self.pv['HLM'],self.pv['LLM']))
					return
		elif mode=='relative':
			if self.pv['TWV']:
				oldPosition = self.read()
				predictedPosition = oldPosition + float(value)
				if self.checkRelLimit(value):
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
				else: 
					logging.error("Cannot move {} by {} - motorlimit will be reached.\nH.Lim:{}\tL.Lim:{}".format(self.pv['DESC'],value,self.pv['HLM'],self.pv['LLM']))
					return
		# Give epics 100ms to get the command to the motor.
		time.sleep(0.2)
		# Stay here while the motor is moving.
		while self.pv['DMOV'].get() == 0:
			pass
		# Finished.
		#checking that the move occurred
		newPosition = self.read()
		retryCounter = 0
		maxRetrties = 3
		BDST=self.pv['BDST'].get()
		while (abs(newPosition-predictedPosition)>BDST) and (retryCounter<maxRetrties): 
			logging.error("Motor {} did not move to {}. Retry #{} of {}.".format(self.pv['DESC'],predictedPosition,retryCounter+1,maxRetrties))
			self.pv['VAL'].put(predictedPosition)
			time.sleep(0.2)
			while self.pv['DMOV'].get() == 0:
				pass
			retryCounter+=1
			newPosition=self.read()
		if (newPosition != predictedPosition) and (retryCounter==maxRetrties):
			logging.error("Couldn't complete the movement.")
		return

	def checkAbsLimit(self,value):
		stillInLimitBool=False
		if float(value)<=float(self.pv['HLM'].get()) and float(value)>=float(self.pv['LLM'].get()):
			stillInLimitBool=True
		return stillInLimitBool

	def checkRelLimit(self,value):
		stillInLimitBool=False
		if (float(value)+float(self.pv['RBV'].get()))>=float(self.pv['LLM'].get()) \
			and (float(value)+float(self.pv['RBV'].get()))<=float(self.pv['HLM'].get()) :
				stillInLimitBool=True
		return stillInLimitBool

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
		# self.pv['IMAGE:ArraySize0_RBV'] = None
		# self.pv['IMAGE:ArraySize0_RBV'] = None
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pv['CAM:Acquire'] = epics.PV(self._pv+':CAM:Acquire',connection_timeout=1)
		self.pv['CAM:DataType_RBV'] = epics.PV(self._pv+':CAM:DataType_RBV',connection_timeout=1)
		self.pv['IMAGE:ArrayData'] = epics.PV(self._pv+':IMAGE:ArrayData',connection_timeout=1)
		# self.pv['IMAGE:ArraySize0_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize0_RBV',connection_timeout=1)
		# self.pv['IMAGE:ArraySize1_RBV'] = epics.PV(self._pv+':IMAGE:ArraySize1_RBV',connection_timeout=1)
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
			# self.pv['CAM:Acquire'].put(1)
			# im = self.pv['IMAGE:ArrayData'].get()
			# try:
			# 	image = np.array(im,dtype='uint16')
			# except:
			# 	logging.error("Tried to get image from RUBY. Instead got {}".format(im))
			# 	# Try again.
			# 	image = np.array(im,dtype='uint16')
			image = None
			while image is None:
				logging.critical("epics wait=True for hamapapa times out...")
				self.pv['CAM:Acquire'].put(1,wait=False)
				time.sleep(1)
				image = self.pv['IMAGE:ArrayData'].get()

			# x = self.pv['IMAGE:ArraySize1_RBV'].get()
			# y = self.pv['IMAGE:ArraySize0_RBV'].get()
			# logging.info("Flipping RUBY images because it is retarded.")
			# return np.fliplr(np.flipud(image.reshape(x,y)))
			return image.reshape(616,1216)
