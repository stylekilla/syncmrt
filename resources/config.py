class general:
	""" General application settings. These should be updateable in GUI... somehow. """
	# Imaging configs.
	numberOfXrays = 1
	defaultImagingAngles = [0,0]
	imagingThetaRange = [-90,90]
	imagingZRange = [-10,10]
	imagingMaximumZRange = [-200,200]
	imagingVelocity = 0

class markers:
	""" Marker settings for fiducials. """
	quantity = 6
	size = 2.00
 
class files:
	""" Relative file locations. """
	patientSupports = '/database/patientSupports.csv'
	detectors = '/database/detectors.csv'

class treatmentBeam:
	""" Treatment beam properties. """
	# Choose a backend.
	backend = 'epics'
	# Basic properties. If irrelevant, set to 0. Units are in mm.
	width = 55.0
	height = 1.0
	
	# Operating conditions for this beam.
	CONDITIONS = {
		'Beamline Enabled': ['SR08ID01PSS01:BL_ENABLE_STS','Enabled'],
		'Shutter Mode': ['SR08ID01PSS01:SHUTTER_MODE','White mode'],
	}
	# 'SR08ID01PSS01:SHUTTER_MODE' == 'Mono mode'
	# If a dict of values is provided, it uses those specific values to determine the state.
	# Use None if does not exist or irrelevant.

	# Beam on/off isn't strictly correct for synchrotrons... but we will use this terminology of
	# turning the beam "on" and "off" in place of "shutter open" and "shutter closed" since we can
	# still have other shutters (i.e. imaging shutters for fast MRT shutters).
	SOURCE_PVS = {
		'On': "SR08ID01PSS01:FE_SHUTTER_OPEN_CMD",
		'Off': "SR08ID01PSS01:FE_SHUTTER_CLOSE_CMD",
		'Status': "SR08ID01PSS01:FE_SHUTTER_STS",
		'ShutterOpen': "SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD",
		'ShutterClose': "SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD",
		'ShutterStatus': "SR08ID01PSS01:HU01A_SF_SHUTTER_STS",
	}

class imagingBeam:
	""" Imaging beam properties. """
	# Choose a backend.
	backend = 'epics'
	# Basic properties. If irrelevant, set to 0. Units are in mm.
	width = 76.0
	height = 0.5

	# Connections.
	# Should be a list: [access, value].
	# If a dict of values is provided, it uses those specific values to determine the state.
	# Use None if does not exist or irrelevant.

	# Beam on/off isn't strictly correct for synchrotrons... but we will use this terminology of
	# turning the beam "on" and "off" in place of "shutter open" and "shutter closed" since we can
	# still have other shutters (i.e. imaging shutters for fast MRT shutters).
	SOURCE_PVS = {
		'On': "SR08ID01PSS01:FE_SHUTTER_OPEN_CMD",
		'Off': "SR08ID01PSS01:FE_SHUTTER_CLOSE_CMD",
		'Status': "SR08ID01PSS01:FE_SHUTTER_STS",
		'ShutterOpen': "SR08ID01PSS01:HU01A_BL_SHUTTER_OPEN_CMD",
		'ShutterClose': "SR08ID01PSS01:HU01A_BL_SHUTTER_CLOSE_CMD",
		'ShutterStatus': "SR08ID01PSS01:HU01A_SF_SHUTTER_STS",
	}

class imager:
	""" Settings for the imager configuration. """
	# Choose a backend.
	backend = 'epics'
	# Orientation of detector image.
	flipud = True
	fliplr = True
	# Geometric configuration of imager/source.
	# sad = 1.2
	# sid = 1.5 
	# magnification = sad/sid
	# pixelSize = [0.1*magnification,0.1*magnification]		# Pixel size is 0.1 mm for HamaMama.
	pixelSize = [0.081,0.081]
	# Pixel size of image in mm for (col,row) (otherwise known as horiz,vertical; x,y).
	# Isocenter specified as (col,row) (otherwise known as horiz,vertical; x,y).
	isocenter = [606.812,663.812]#[616.406,664.438] # Updated at 11am on 22/04/22 by Micah.
	# Offset between the primary beam and the imager.
	#offset = [0,0,0,0,0,0]			# No change (default).
	#offset = [0,0,20,0,0,0]			# Monochromatic beam (+20 mm in Z)
	offset = [0,0,0,0,0,-32.7]		# 2B X-Ray Source (-32.7 deg about Z)
	
	name = 'HamaMamma'
	# Specify an access port.
	port = 'SR08ID01DETIOC08'
	# Paths to objects.
	roiPort = 'pcoEdge.cam'
	iocpath = ''
	localpath = ''
	attributesfile = ''
	# Detector PV's to use.
	DETECTOR_PVS = {
		'Acquire': 'CAM:Acquire',
		'AcquireTime': 'CAM:AcquireTime',
		'AcquirePeriod': 'CAM:AcquirePeriod',
		'ArrayCounter': 'CAM:ArrayCounter',
		'NumberOfImages': 'CAM:NumImages',
		'ImageMode': 'CAM:ImageMode',
		'AutoSave': 'TIFF:AutoSave',
		'DataType': 'IMAGE:DataType_RBV',
		'ArraySizeX': 'CAM:ArraySizeX_RBV',
		'ArraySizeY': 'CAM:ArraySizeY_RBV',
		'ArrayData': 'IMAGE:ArrayData',
		'RoiData': 'ROI1:IMAGE:ArrayData',
		'HDFenable': 'HDF:EnableCallbacks',
		'HDFcapture': 'HDF:Capture',
		'HDFfilePath': 'HDF:FilePath',
		'HDFfileName': 'HDF:FileName',
		'HDFautosave': 'HDF:AutoSave',
		'HDFfileWriteMode': 'HDF:FileWriteMode',
		'HDFnumberOfImages': 'HDF:NumCapture',
		'HDFautoIncrement': 'HDF:AutoIncrement',
		'HDFarrayPort': 'HDF:NDArrayPort',
		'HDFattributes': 'HDF:NDAttributesFile',
		'TIFFenable': 'TIFF:EnableCallbacks',
		'TIFFautosave': 'TIFF:AutoSave',
		'RoiSizeX': 'HDF:ArraySize0_RBV',
		'RoiSizeY': 'HDF:ArraySize1_RBV',
		'ArrayCounterRBV': 'CAM:ArrayCounter_RBV',
		# Need to link imaging shutter...?
	}

class motor:
	def __init__(self,axis,order,port,description):
		self.axis = axis
		self.order = order
		self.port = port
		self.description = description

class patientSupport:
	""" Settings for the patientSupport system. """
	# Choose a backend.
	backend = 'epics'
	# Name it.
	name = 'DynMRT'
	# Motors.
	MOTOR_CONTROLLERS = [
		motor(0,3,'SR08ID01SST25:SAMPLEH1',		'X Translation'),
		motor(1,2,'SR08ID01SST25:SAMPLEH2',		'Y Translation'),
		motor(2,0,'SR08ID01SST25:SAMPLEV',		'Z Translation'),
		motor(5,1,'SR08ID01SST25:ROTATION',	'Rotation'),
	]
	# Do we need the moves to happen one after the other or can they happen simulatenously?
	simulatenousCommands = True
	# The workpoint is a settable point to tell the patient support to move around (i.e. a Robot TCP).
	workpoint = False
	WORKPOINT_CONTROLLER = {
	}
	# How is the speed controlled, per axis or globally? 
	# Options are: axis/global
	velocityMode = None
	VELOCITY_CONTROLLER = None
	velocityRange = None
	accelerationRange = None
	# Specify imaging, treating, and general motion [velocity,acceleration].
	defaultVelocity = None
	# Define the config for the vertical translation for imaging and treatment.
	VERTICALMOTION_CONTROLLER = None

class machine:
	""" A configuration for the machine - can be used to preconfigure things for Hutch 2B or Hutch 3B etc. """
	# Imaging mode: (dynamic/static/step).
	imagingMode = 'static'
	# The following can be set as strings, as long as they have a configuration file stored in the database folder.
	imager = 'HamaMama'
	imagingBeam = None
	treatmentBeam = None
	patientSupport = 'DynMRT'

"""
Automated Class Configs
-----------------------
These are updated based on the above configurations.
"""
class imagingSidebar:
	""" Imaging sidebar defaults. """
	numberOfXrays = general.numberOfXrays
	defaultImagingAngles = general.defaultImagingAngles
	imagingThetaRange = general.imagingThetaRange
	imagingZRange = general.imagingZRange
	imagingMaximumZRange = general.imagingMaximumZRange
	velocityMode = patientSupport.velocityMode
	velocity = general.imagingVelocity
	velocityRange = patientSupport.velocityRange