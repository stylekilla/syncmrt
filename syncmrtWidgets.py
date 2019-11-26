# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
# For PyInstaller:
import sys, os
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

resourceFilepath = application_path+'/resources/'

# This is specifically for the sidebar....
class QsStackedWidget(QtWidgets.QStackedWidget):
	def __init__(self,parent):
		super().__init__()
		self.parent = parent
		self.setMinimumHeight(500)
		self.setFixedWidth(225)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.parent.setVisible(False)
		# Page in stack.
		self.page = {}

		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,name,widget,before=None,after=None):
		'''Before and after must be names of other pages.'''
		if name in self.page:
			# Do nothing it already exists.
			return

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.page[before]

		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.page[after] + 1
				# index = self.indexOf(self.page[after]) + 1
		else:
			index = self.count()

		# self.insertWidget(index,self.page[name])
		self.insertWidget(index,widget)
		self.page[name] = index

	def removePage(self,name,delete=False):
		'''Remove page from stack, delete from memory if required.'''
		self.removeWidget(self.page[name])
		if delete: del self.page[name]

class QsListWidget(QtWidgets.QListWidget):
	def __init__(self,parent):
		# List initialisation.
		super().__init__()
		self.setMinimumHeight(500)
		self.setFixedWidth(60)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setIconSize(QtCore.QSize(50,50))
		# A list of names in the stacked widget (of pages to show and hide).
		self.page = {}

		# Add self to parent layout.
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,name,before=None,after=None):
		'''Before and after must be names of other pages.'''
		self.page[name] = QtWidgets.QListWidgetItem()
		self.page[name].setText(name)
		self.page[name].setToolTip(name)
		# Add Icon.
		icon = QtGui.QIcon(resourceFilepath+'/images/'+name+'.png')
		icon.pixmap(50,50)
		self.page[name].setIcon(icon)
		self.page[name].setSizeHint(QtCore.QSize(60,60))

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.row(self.page[before]) - 1
		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.row(self.page[after]) + 1
		else:
			index = self.count()

		self.insertItem(index,self.page[name])

	def removePage(self,name,delete=False):
		'''Remove page from list, delete from memory if required.'''
		self.removeItemWidget(self.page[name])

		if delete:
			del self.page[name]