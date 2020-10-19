from PyQt5 import QtWidgets, QtGui, QtCore
from functools import partial
from resources import config
import numpy as np
import QsWidgets
import logging

class propertyModel(QtGui.QStandardItemModel):
	'''
	Categories (such as Xray/CT/RtPlan) will be parents of their variables.
	Children will be attached with sub children for broken down variables.
	'''
	def __init__(self):
		super().__init__()
		self.setColumnCount(2)
		self.setRowCount(0)
		self.setHorizontalHeaderLabels(['Property','Value'])
		# Section holds Root (top level) items. Index holds index of all sub-items.
		self.section = {}
		# index[name][variable][sub-variable] returns QModelIndex.
		self.index = {}

	def addSection(self,name):
		'''Add new section to model. Model section introduces list of all items inside.'''
		item = QtGui.QStandardItem()
		item.setData(name,QtCore.Qt.DisplayRole)
		self.appendRow(item)
		self.section[name] = item

		# have a custom delegate for styling...
		self.index[name] = {}
		self.index[name]['root'] = self.indexFromItem(item)

	def addVariable(self,name,variable,value):
		'''Takes single and multiple variables, adds to parent item (name).'''
		if type(value) is not str:
			# Convert to 3dec places, assuming it's a number
			value = np.around(value,decimals=3)

		if type(variable) is list:
			# Multiple Entry
			prop = QtGui.QStandardItem()
			prop.setData(variable[0],QtCore.Qt.DisplayRole)
			prop.setEditable(False)

			descr = QtGui.QStandardItem()
			descr.setEditable(False)

			self.section[name].appendRow([prop,descr])
			self.index[name][variable[0]] = {}
			self.index[name][variable[0]][0] = self.indexFromItem(descr)

			string = ''

			for i in range(len(value)):
				var = QtGui.QStandardItem()
				var.setData(variable[i+1],QtCore.Qt.DisplayRole)
				var.setEditable(False)

				val = QtGui.QStandardItem()
				val.setData(str(value[i]),QtCore.Qt.DisplayRole)
				val.setEditable(True)

				prop.appendRow([var,val])

				string += str(value[i])+', '

				self.index[name][variable[0]][variable[i+1]] = self.indexFromItem(val)

			string = string[:-2]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemVariable = QtGui.QStandardItem()
			itemVariable.setData(variable,QtCore.Qt.DisplayRole)
			itemVariable.setEditable(False)

			itemValue = QtGui.QStandardItem()
			itemValue.setData(str(value),QtCore.Qt.DisplayRole)
			itemValue.setEditable(True)

			self.section[name].appendRow([itemVariable,itemValue])
			self.index[name][variable] = self.indexFromItem(itemValue)

	def updateVariable(self,name,variable,value):
		'''Find variable and update value.'''
		if type(value) is not str:
			# Convert to 3dec places, assuming it's a number
			value = np.around(value,decimals=3)

		if type(variable) is list:
			# Multiple Entry
			descr = self.itemFromIndex(self.index[name][variable[0]][0])

			# item description
			string = ''
			for i in range(len(value)):
				val = self.itemFromIndex(self.index[name][variable[0]][variable[i+1]])
				val.setData(str(value[i]),QtCore.Qt.DisplayRole)

				string += str(value[i])+', '

			string = string[:-2]
			descr.setData(string,QtCore.Qt.DisplayRole)

		else:
			# Single Entry
			itemValue = self.itemFromIndex(self.index[name][variable])
			itemValue.setData(str(value),QtCore.Qt.DisplayRole)

class QPropertyManager(QtWidgets.QTreeView):
	'''
	Property manager that stores variable/name for all variables. 
	This is a tree view, the model comes from propertyModel.
	'''
	def __init__(self):
		super().__init__()
		# self.setHorizontalHeader('Property Editor')
		self.setAlternatingRowColors(True)
		self.setRootIsDecorated(True)
		# sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		# self.setSizePolicy(sizePolicy)
		self.setModel(propertyModel())
		self.setMinimumSize(250,100)
		# self.setMaximumWidth(600)
		# self.setIndentation(0)

	def addSection(self,name):
		self.model().addSection(name)
		self.expandAll()

	def addVariable(self,name,variable,value):
		self.model().addVariable(name,variable,value)
		self.expandAll()

	def updateVariable(self,name,variable,value):
		self.model().updateVariable(name,variable,value)