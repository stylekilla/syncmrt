class ProgramManager:
	def __init__(self):
		self.workspace = None
		self.sidebarLeft = None
		self.sidebarRight = None
		self.sidebarBottom = None

	def set(self,manager,widget):
		# Add a widget to the manager.
		if manager == 'workspace': 
			self.workspace = widget
			self.workspace.workspaceChanged.connect()
		elif manager == 'sidebarLeft': self.sidebarLeft = widget
		elif manager == 'sidebarRight': self.sidebarRight = widget
		elif manager == 'sidebarBottom': self.sidebarBottom = widget
		else: pass

	# def setSidebarLeft(self,:
	# on workspace change, set correesponding sidebar widget.