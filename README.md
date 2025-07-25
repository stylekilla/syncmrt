# SynchrotronMRT
A python/qt application for Synchrotron Radiotherapy (Python3.5 + Qt5.9).
This was born out of a need for image guidance protocols on the Imaging and Medical Beamline (IMBL) at the Australian Synchrotron.
However it is slowly turning into a fully equipped IGRT program that covers dosimetry, treatment planning (basic functionality in the program or import a clinical treatment plan), image guidance and treatment delivery.

Requirements:
- Python 3.5+
- Qt 5.9+
- Everything in the requirements.txt file

Notes: 
- The master branch is the most out-of-date branch, but I expect this to change once I have finished updating some features.
- If you would like more detailed descriptions, hassle me for them! I'll do them eventually - I promise :) 
- Most of the helpful notes exist as comments in the python files themselves.
- Read the Docs is something I've investigated but haven't had the time to implement properly just yet.

Setup Virtualenv
python -m venv /path/to/virtual/envs/location/and/name/of/this/new/virtualenv/eg/syncmrtenv
source /path/to/virtual/envs/location/and/name/of/this/new/virtualenv/eg/syncmrtenv/bin-or-Scripts/activate.sh
pip install -r requirements.txt

Activate Virtualenv
source /path/to/virtual/envs/location/and/name/of/this/new/virtualenv/eg/syncmrtenv/bin-or-Scripts/activate.sh

Set default values
in resources/config.py

Run Syncmrt
python main.py

--------------------------------
How to calibrate Hama/SpectrumLogic (SL)

Mono beam or 1.4T-AlCu or dimmer pink beam.
2B RUBY in beam and in-focus, ballbearing phantom on dynMRT stage, 1mm bda or greater (2mm preferable)
move sampleV to get ballbearing in beam
run scripts->setup-rotationIsocentre.py - closing popup windows as you go.
This should end with ballbearing in COR - spin through live image to see if it moves at all.
Adjust Mask motor positions such that each edge of the mask meets at centreline of ballbearing
Adjust SampleV such that motion of maskSize/2 and opposite wedgeZ places ballbearing centreline at top/bottom mask edge

RUBY CALIB DONE - DO NOT MOVE PHANTOM ON STAGE UNTIL ISOCENTRE VARIABLE IN CONFIG.PY HAS BEEN UPDATED.

Set dynTable to correct height, move RUBY out of the way, take and save image of ballbearing at COR with hama/SL.
Open Fiji, transform flip image horizontally and vertically according to same paramaters in resources/config.py: imager class - flipud, fliplr (default true both)
find pixel value of ballbearing X and Y - edit config.imager.isocenter  [X,Y]

Move H1, H2, and SampleV a little, then do test alignment and irradiate to determine ballbearing placement in field.


---------------------------------------------
QsWidgets/QSidebar/QImaging - spinny camera tab
QsWidgets/QSidebar/QSettings - contents of Gear settings tab

main - self.envXray is in QsWorkspace
QsWidgets/QsWorkspace - contains QPlot instance
QsWidgets/QsMpl/QPlot - the displayed HDF5 file
	when image clicked with pickiso tool - calls '\_updateiso' funciton. 
	self.patientIsocenter list is updated, then emitted via self.newIsocenter.emit()
then in QsWorkspace
	self.plot.newIsocenter.connect(self.\_updateIsocenterFromPlot)
	.....
	self.patientIsocenter = np.array(isocenter)
	# Emit the signal telling the world we have a new isocenter.
	# This signal is designed to send out the (h1,h2,v) coordinate.
	h1,h2,v = self.plot.patientIsocenter
	self.newIsocenter.emit(h1,h2,v)
then in main
	self.envXray.newIsocenter.connect(widget.setIsocenter)
	widget is QXRayProperties instance
QsWidgets/QSidebar/QXRayProperties - slidy dial tab (ImageProperties)
	can updat isocentre and emit to update position elsewhere via self.isocenterUpdated.emit(h1,h2,v)
	[in main createworkenvironmentxray: widget.isocenterUpdated.connect(self.envXray.updateIsocenter), passes back down to plot]

	self.widget['isocenter']['align'].clicked.connect(partial(self.align.emit,-1)) align button signal
	passed back to main: widget.align.connect(self.patientApplyAlignment)

in main patientApplyAlignment. PatientCalculateAlignment(-1).
isocenter = self.envXray.getIsocenter() [gets position from envXray, which is QXrayProperties]
self.system.solver.setInputs(PatientIsoc) -> system.solver.solve 
system = systems.thebrain
	system.solver = systems.imageGuidance.solver
	self.\_patientIsocenter = np.array(patientIsoc)
	translation = -patientisocentre
	solution = hstack of translation and rotation matrices
system calculate alignment -> self.patientSupport.calculateMotion i <10????????????? WTF
patientSupport = control.hardware.patientSupport

system.applyalignment
uses patientSupport.\_motion, which is not updated if calls to calculate motion are >10??????

properties = QsWidgets.QsSidebar.QPropertyManager()