# Sitepackages imports.
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import csv

__all__ = ['QsAdHocTreatmentPlan']

class QsAdHocTreatmentPlan(QtWidgets.QWidget):
	"""
	A basic module that allows one to create an ad-hoc treatment plan on.
	"""
	# Send a string containing the path location to the new file.
	newTreatmentPlan = QtCore.pyqtSignal(str)

	def __init__(self,parent):
		# Initialise the main window.
		super().__init__(parent,QtCore.Qt.Window)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setWindowTitle('Create Ad-Hoc Treatment Plan')
		self.setFixedSize(640,480)
		# Get the size of the primary display.
		# screen = QtWidgets.QDesktopWidget().screenGeometry(0)
		# screen.height*0.5
		# screen.width*0.5

		# Create a new layout.
		_layout = QtWidgets.QVBoxLayout()

		# Create the model/view.
		self.tableModel = TreatmentTableModel()
		self.tableView = QtWidgets.QTableView()
		# Connect the view and model together.
		self.tableView.setModel(self.tableModel)
		# Do some setup.
		self.tableView.horizontalHeader().setStretchLastSection(True)

		# Add some buttons.
		addRow = QtWidgets.QPushButton("Add Field")
		removeRow = QtWidgets.QPushButton("Remove Field")
		save = QtWidgets.QPushButton("Save")
		# Set up their signals.
		addRow.clicked.connect(self.tableModel.addRow)
		removeRow.clicked.connect(self.tableModel.removeRow)
		save.clicked.connect(self.save)
		# Create a bottom bar.
		bottomBar = QtWidgets.QWidget()
		bottomBar_layout = QtWidgets.QHBoxLayout()
		bottomBar_layout.addStretch()
		bottomBar_layout.addWidget(addRow)
		bottomBar_layout.addWidget(removeRow)
		bottomBar_layout.addWidget(save)
		bottomBar.setLayout(bottomBar_layout)

		# Add things to the layout.
		_layout.addWidget(self.tableView)
		_layout.addWidget(bottomBar)

		# Add the central widget.
		self.setLayout(_layout)
		# Show the window.
		# self.setWindowModality(QtCore.Qt.WindowModal)
		self.raise_()
		self.show()

	def save(self):
		""" Save the info in the table to a csv file. """
		# Get the items from the table.
		data = self.tableModel.getItems()
		if data != False:
			# Create a file save dialog.
			fileFormat = 'CSV (*.csv)'
			fileDialogue = QtWidgets.QFileDialog()
			file, dtype = fileDialogue.getSaveFileName(self, "Save new synchrotron treatment plan", "", fileFormat)
			# Create the new xray file.
			if file.endswith('.csv') is False:
				file += '.csv'

			# With file open, save stuff.
			with open(file,'w',newline='') as csvFile:
				writer = csv.writer(csvFile,delimiter=',')
				for row in data:
					writer.writerow(row)

			# Emit new treatment plan.
			self.newTreatmentPlan.emit(file)

	def onClose(self):
		""" Closing routine. """
		# Disconnect all signals.
		self.newTreatmentPlan.disconnect()
		# Close the window.
		self.close()

class TreatmentTableModel(QtGui.QStandardItemModel):
	"""
	Table model for creating a treatment plan.
	"""

	def __init__(self):
		# Initialise the model.
		super().__init__()
		# Create label headers.
		headers = ['Field ID','Mask Size (mm)','Speed (mms<sup>-1</sup>)','Relative Position from Isocenter']
		# Setup the model.
		self.setColumnCount(len(headers))
		self.setRowCount(1)
		self.setHorizontalHeaderLabels(headers)
		# Add initial data.
		fieldId = QtGui.QStandardItem()
		fieldId.setData("01",QtCore.Qt.DisplayRole)
		maskSize = QtGui.QStandardItem()
		maskSize.setData(20,QtCore.Qt.DisplayRole)
		speed = QtGui.QStandardItem()
		speed.setData(10.0,QtCore.Qt.DisplayRole)
		position = QtGui.QStandardItem()
		position.setData("[0,0,0,0,0,0]",QtCore.Qt.DisplayRole)
		self.setItem(0,0,fieldId)
		self.setItem(0,1,maskSize)
		self.setItem(0,2,speed)
		self.setItem(0,3,position)

	def addRow(self):
		""" Add a row to the table. """
		self.setRowCount(self.rowCount()+1)

	def removeRow(self):
		""" Remove a row from the table. """
		self.setRowCount(self.rowCount()-1)

	def getItems(self):
		""" Retrieve a list of all the items in the table. """
		items = []
		# Iterate over each row and collect the data.
		for row in range(self.rowCount()):
			# CHECK 1: Check for null returns from Qt.
			data = []
			if self.item(row,0) == None:
				data = None
			elif self.item(row,1) == None:
				data = None
			elif self.item(row,2) == None:
				data = None
			elif self.item(row,3) == None:
				data = None
			else:
				pass

			if data is None:
				self.showFailMessage()
				return False

			# Get data.
			fieldId = self.item(row,0).text()
			maskSize = self.item(row,1).text()
			speed = self.item(row,2).text()
			position = self.item(row,3).text()

			# CHECK 2: Find empty data strings.
			if fieldId == '':
				data = None
			elif maskSize == '':
				data = None
			elif speed == '':
				data = None
			elif position == '':
				data = None
			else:
				pass

			if data is None:
				self.showFailMessage()
				return False

			# CHECK 3: Check for incorrect data strings.
			try:
				maskSize = float(maskSize)
			except:
				data = None
			try:
				speed = float(speed)
			except:
				data = None
			position = list(map(float,position[1:-1].split(',')))
			if len(position) != 6:
				data = None

			if data is None:
				self.showFailMessage()
				return False

			# All is well, collect and append the data.
			data.append(fieldId)
			data.append(maskSize)
			data.append(speed)
			data.append(position)
			items.append(data)

		return items

	def showFailMessage(self):
		# Tell the user it failed.
		QtWidgets.QMessageBox.warning(None,"Creating treatment plan","Could not save file as not all fields are complete.")