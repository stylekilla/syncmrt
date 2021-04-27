def populate(mb):
	""" Populate the menubar (mb). """
	items = {}
	"""
	FILE
	"""
	file = mb.addMenu("File")
	# NEW
	file_new = file.addMenu("New")
	items['new_xray'] = file_new.addAction("X-Ray File")
	items['new_xray'].setShortcut('Ctrl+N')
	# LOAD
	file_load = file.addMenu("Load")
	items['load_xray'] = file_load.addAction("&X-Ray")
	items['load_xray'].setShortcut('Ctrl+L')
	items['load_ct'] = file_load.addAction("&CT")
	items['load_rtplan'] = file_load.addAction("RT &Plan")
	items['load_syncplan'] = file_load.addAction("Synchrotron Treatment Plan")
	file_load.addSeparator()
	items['load_folder'] = file_load.addAction("&Folder")

	"""
	TOOLS
	"""
	tools = mb.addMenu("Tools")
	# SCRIPTS
	tools_scripts = tools.addMenu("Scripts")
	# Get all the custom scripts in the scripts folder.
	import os
	from functools import partial
	for item in os.listdir('./scripts/'):
		if item.endswith('.py'):
			# Capitilise the strings.
			scriptName = item[:-3]
			# Add the actions.
			script = tools_scripts.addAction(scriptName)
			# When clicked then run the file in a separate python instance.
			script.triggered.connect(partial(run,item))
	return items

def run(script):
	''' Run a script within the scripts folder. '''
	import os
	os.system('python ./scripts/{}'.format(script))