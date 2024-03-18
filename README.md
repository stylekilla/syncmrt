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