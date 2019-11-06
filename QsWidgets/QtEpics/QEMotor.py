import epics
from PyQt5 import QtGui, QtWidgets

class QEMotor(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,parent=None):
		QtWidgets.QWidget.__init__(self,parent)

		# Internal vars: these should be reflected in the CSV file that the motors list is kept in, see class controlsPage().
		self._stage = None
		self._name = None
		self._pv = None

		# PV vars.
		self.pv = {}
		self.pv['RBV'] = False
		self.pv['VAL'] = False
		self.pv['TWV'] = False
		self.pv['TWR'] = False
		self.pv['TWF'] = False
		self.pv['DMOV'] = False

		# Is the motor successfully connected?
		self._connected = True

	def setup(self):
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pvBase = self._pv
		try:
			# Read Back Value
			self.pv['RBV'] = epics.PV(self.pvBase+'.RBV')
		except:
			pass
		try:
			# Is motor moving?
			self.pv['DMOV'] = epics.PV(self.pvBase+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self.pvBase+'.VAL')
		except:
			pass
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self.pvBase+'.TWV')
		except:
			pass
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self.pvBase+'.TWR')
		except:
			pass
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self.pvBase+'.TWF')
		except:
			pass

		# Iterate over all PV's and see if any are disconnected. If one is disconnected, set the state to False.
		# If everything passes, set the state to True.
		state = True
		for key in self.pv:
			if self.pv[key] is False: state = False
		self._connected = state

	def readValue(self,attribute):
		if self._connected is False: return None
		else: return self.pv[attribute].get()

	def writeValue(self,attribute,value=None):
		if self._connected is False: return None
		else: 
			if attribute == 'TWV':
				self.pv[attribute].put(value)
			else:
				while self.pv['DMOV'] == 1:
					pass
				self.pv[attribute].put(value)

	def read(self):
		# Straight up reading where the motor is.
		if self._connected is False: return np.inf 
		else: return self.pv['RBV'].get()

	def write(self,value,mode='absolute'):
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
		else:
			print('Failed to write value ',value,' to motor ',self.movement)

class QEMotorSimple(QEMotor):
	def __init__(self,parent=None):
		super().__init__()

	def setup(self):
		# Once the information has been loaded into the internal vars, setup the motor widget.
		# Set the ui file.
		fp = os.path.join(os.path.dirname(__file__),"QEMotorSimple.ui")
		uic.loadUi(fp,self)
		self.pbReset.setStyleSheet("background-color: red")
		# Connect to the PV's.
		self._connectPVs()
		self.status()
		self.lblName.setText(self._name)

	def status(self):
		if self._connected is False:
			self.pbReset.setStyleSheet("background-color: red")
		elif self._connected is True:
			self.pbReset.setStyleSheet("background-color: green")
		else:
			# Something went wrong, set to False.
			self._connected = False
			self.pbReset.setStyleSheet("background-color: red")

	def reconnect(self):
		# If button is pressed, retry self._connectPVs()
		self._connectPVs()
		self.status()

	def setReadOnly(self,state):
		# Set all items to state = True/False
		self.pbReset.setEnabled(state)
		
class QEMotorNormal(QEMotor):
	def __init__(self,parent=None):
		super().__init__()

	def setup(self):
		# Once the information has been loaded into the internal vars, setup the motor widget.
		# Set the ui file.
		fp = os.path.join(os.path.dirname(__file__),"QEMotorNormal.ui")
		uic.loadUi(fp,self)
		# Connect to the PV's.
		self._connectPVscalen()
		self.lblName.setText(self._name)

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		self.pvBase = self._pv

		try:
			# Read Back Value
			self.pv['RBV'] = epics.PV(self.pvBase+'.RBV',callback=partial(self.updateValue, attribute='RBV') )
			self.guiRBV.setEnabled(True)
			self.guiRBV.setReadOnly(True)
			self.guiRBV.setText(str(self.pv['RBV'].get()))
			self.guiRBV.setValidator(QEFloatValidator)
		except:
			self.guiRBV.setEnabled(False)
		try:
			# Is motor moving?
			self.pv['DMOV'] = epics.PV(self.pvBase+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self.pvBase+'.VAL',callback=partial(self.updateValue, attribute='VAL') )
			self.guiVAL.setValidator(QEFloatValidator())
			self.guiVAL.setEnabled(True)
			self.guiVAL.returnPressed.connect(partial(self.writeValue,attribute='VAL',value=float(self.guiVAL.getText())))
		except:
			self.guiVAL.setEnabled(False)
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self.pvBase+'.TWV',callback=partial(self.updateValue, attribute='TWV') )
			self.guiTWV.setValidator(QEFloatValidator())
			self.guiTWV.setEnabled(True)
			self.guiTWV.returnPressed.connect(partial(self.writeValue,attribute='TWV',value=float(self.guiTWV.getText())))
		except:
			self.guiTWV.setEnabled(False)
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self.pvBase+'.TWR')
			self.guiTWR.setEnabled(True)
			self.guiTWR.clicked.connect(partial(self.writeValue,attribute='TWR',value=1))
		except:
			self.guiTWR.setEnabled(False)
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self.pvBase+'.TWF')
			self.guiTWF.setEnabled(True)
			self.guiTWF.clicked.connect(partial(self.writeValue,attribute='TWF',value=1))
		except:
			self.guiTWF.setEnabled(False)

		# Iterate over all PV's and see if any are disconnected. If one is disconnected, set the state to False.
		# If everything passes, set the state to True.
		state = True
		for key in self.pv:
			if self.pv[key] is False: state = False
		self._connected = state

	def updateValue(self,attribute,pvname=None,value=None,**kw):
		'''Callback function for when the motor value updates.'''
		value = str('{0:.4f}'.format(value))

		if attribute == 'RBV':
			# Not set by user. Set by PV readback.
			self.guiRBV.setText(value)
		elif attribute == 'VAL':
			# Set by user in gui and by PV readback.
			self.guiVAL.setText(value)
		elif attribute == 'TWV':
			# Set by user in gui and by PV readback.
			self.guiTWV.setText(value)
		else:
			pass

	def setReadOnly(self,state):
		# Set all items to state = True/False
		self.guiVAL.setEnabled(state)
		self.guiTWV.setEnabled(state)
		self.guiTWF.setEnabled(state)
		self.guiTWR.setEnabled(state)

class QEMotorComplex(QEMotor):
	def __init__(self,parent=None):
		super().__init__()

# # Detectors
# class QEDetector(QtWidgets.QWidget):
# 	def __init__(self,name,pv,parent=None):
# 		QtWidgets.QWidget.__init__(self,parent)
# 		# fp = os.path.join(os.path.dirname(__file__),"QEDetector.ui")
# 		# uic.loadUi(fp,self)

# 		# # Set text label
# 		# self.name.setText(motor)

# 		# # Record PV root information and connect to motors.
# 		# self.pvBase = pv
# 		# self.pv = {}
# 		# self._connectPV()

# Validators
class QEFloatValidator(QtGui.QDoubleValidator):
	def __init__(self):
		super().__init__()
		self.setDecimals(3)
		self.setBottom(0)