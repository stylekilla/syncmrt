# -*- mode: python -*-

block_cipher = None

dataFiles = [
	('./resources','resources')
]

a = Analysis(
	['mrt_app.py'],
	pathex=[
		'/home/imbl/Documents/Software/syncmrt',
		'/home/imbl/.local/lib/python3.6/site-packages',
		'/usr/local/lib/python3.6/dist-packages'
	],
	binaries=[],
	datas=dataFiles,
	hiddenimports=[],
	hookspath=['./_hooks'],
	runtime_hooks=[],
	excludes=['PyQt4'],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False
)
pyz = PYZ(
	a.pure,
	a.zipped_data,
	cipher=block_cipher
)
exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	name='SyncMRT',
	debug=False,
	strip=False,
	upx=True,
	runtime_tmpdir=None,
	console=True
)