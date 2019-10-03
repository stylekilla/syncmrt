def populate(mb):
	""" Populate the menubar (mb). """
	items = {}
	# FILE MENU
	file = mb.addMenu("File")
	file_new = file.addMenu("New")
	items['new_xray'] = file_new.addAction("X-Ray File")
	items['new_xray'].setShortcut('Ctrl+N')
	file_load = file.addMenu("Load")
	items['load_xray'] = file_load.addAction("X-Ray")
	items['load_ct'] = file_load.addAction("CT")
	items['load_rtplan'] = file_load.addAction("RT Plan")
	items['load_syncplan'] = file_load.addAction("Synchrotron Treatment Plan")
	file_load.addSeparator()
	items['load_folder'] = file_load.addAction("Folder")
	items['load_folder'].setShortcut('Ctrl+L')

	return items