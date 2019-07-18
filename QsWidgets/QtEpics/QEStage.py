from PyQt5 import QtWidgets, QtCore

class controlsPage:
	def __init__(self,level='simple',parent=None,stages='motorList.csv',detectors='detectorList.txt'):
		self.layout = QtWidgets.QGridLayout()
		parent.setLayout(self.layout)
		# Motor and detector lists.
		self.motorList = importMotorListCSV(stages)
		self.detectorList = importDetectorList(detectors)
		# Make a list of the stages.
		self.stageList = set()
		for motor in self.motorList:
			self.stageList.add(motor['Stage'])
		# Current list of selected motors.
		self.currentList = []
		# Current list of selected motors' widgets.
		self.currentWidgetList = []
		# Level changes from simple, normal to complex modes.
		self.level = level

		# Set amount of columns in grid layout.
		self.columns = 3
		# Set top left aligment for layout.
		self.layout.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)

		# Patient controls
		# Default for no control is None.
		# When a control is set, it should be a QEMotor() class.
		self.patient = {}
		self.patient['tx'] = None
		self.patient['ty'] = None
		self.patient['tz'] = None
		self.patient['rx'] = None
		self.patient['ry'] = None
		self.patient['rz'] = None

	def addMotors(self,group,name=None):
		# Search self.motorList and add a motor widget to the page if it exists.
		# If name is specified, add the single motor.
		# If the name is not specified, add the whole group.
		for motor in self.motorList:
			# Search the list.
			if motor['Stage'] == group:
				# Find motors that match the group.
				if name is None:
					# If no name is specified, add the motor.
					self.addMotorWidget(motor)
				elif self.motor['Name'] == name:
					# Else, check that the motor meets the name requirement.
					# Add the motor.
					self.addMotorWidget(motor)
				else:
					# Do Nothing.
					pass

	def addMotorWidget(self,motor,update=False):
		if motor['PV'] == 'None':
			# If no PV is specified, do not create the widget.
			return
		# Create a new motor widget.
		if self.level == 'simple': motorWidget = QEMotorSimple()
		elif self.level == 'normal': motorWidget = QEMotorNormal()
		elif self.level == 'complex': motorWidget = QEMotorComplex()
		# Add motor vars.
		motorWidget._stage = motor['Stage']
		motorWidget._movement = motor['Movement']
		motorWidget._dependentOn = motor['Dependencies']
		motorWidget._name = motor['Name']
		motorWidget._pv = motor['PV']
		motorWidget._order = motor['Order']
		motorWidget._accuracy = motor['Accuracy']
		motorWidget._cor = motor['CoR']
		# Call motor setup function in light of new vars.
		motorWidget.setup()
		# Add motor to layout.
		self.layout.addWidget(motorWidget)
		# Add motor to current list of motors selected.
		if update is False:
			# If we are not updating the existing motors complexity, add it to the current list.
			self.currentList.append(motor)
		# Add motor widget to current list of motor widgets.
		self.currentWidgetList.append(motorWidget)

		# Add motor to patient movement if required.
		if motor['Movement'] in self.patient:
			# Essentially if the motor is 'tx', look for 'tx' in patient and assign it the QEMotor(), tx.
			self.patient[motor['Movement']] = motorWidget

	def setStage(self,group):
		# Remove all existing widgets.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []
		self.currentList = []

		# Reset linked motors to None.
		self.patient['tx'] = None
		self.patient['ty'] = None
		self.patient['tz'] = None
		self.patient['rx'] = None
		self.patient['ry'] = None
		self.patient['rz'] = None

		# Add group motors.
		self.addMotors(group)

	def setLevel(self,level):
		self.level = level

		# Remove all widgets and re-add them in level required.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []

		# Add back new ones.
		for motor in self.currentList:
			self.addMotorWidget(motor,update=True)

	def setDetector(self,detector):
		pass

	def setReadOnly(self,state):
		for motorWidget in self.currentWidgetList:
			motorWidget.setReadOnly(state)
