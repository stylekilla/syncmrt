"""
Hook for http://pypi.python.org/pypi/epics/
Written by Micah Barnes, Mar 2019.
Version of epics used: 3.3.3
"""

hiddenimports = [
		'epics.clibs',
	]

import epics

binaries = [
	(epics.ca.find_libca(), './'),
	(epics.ca.find_libCom(), './')
]