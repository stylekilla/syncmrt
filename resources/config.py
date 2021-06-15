class general:
	""" General application settings. These should be updateable in GUI... somehow. """
	# Imaging configs.
	numberOfXrays = 1
	defaultImagingAngles = [0,-90]
	imagingThetaRange = [-90,90]
	imagingZRange = [-30,30]
	imagingMaximumZRange = [-200,200]

class markers:
	""" Marker settings for fiducials. """
	quantity = 3
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
	pixelSize = [0.03,0.03]
	# Pixel size of image in mm for (col,row) (otherwise known as horiz,vertical; x,y).
	# Isocenter specified as (col,row) (otherwise known as horiz,vertical; x,y).
	isocenter = [1280,7.5]
	# Offset between the primary beam and the imager.
	# offset = [0,0,0,0,0,0]			# No change (default).
	offset = [0,0,20,0,0,0]			# Monochromatic beam (+20 mm in Z)
	# offset = [0,0,0,0,0,-32.7]		# 2B X-Ray Source (-32.7 deg about Z)
	
	name = 'PCO3-HCL'
	# Specify an access port.
	port = 'SR08ID01DETIOC10'
	# Paths to objects.
	roiPort = 'pcoEdge.cam.roi1'
	iocpath = 'D:\\syncmrt\\'
	localpath = '/mnt/tmp/'
	attributesfile = 'LAPSPositionTracker.xml'
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
	name = 'LAPS'
	# Motors.
	MOTOR_CONTROLLERS = [
		motor(0,0,'SR08ID01ROB01:MOTOR_X',		'X Translation'),
		motor(1,1,'SR08ID01ROB01:MOTOR_Y',		'Y Translation'),
		motor(2,2,'SR08ID01ROB01:MOTOR_Z',		'Z Translation'),
		motor(3,3,'SR08ID01ROB01:MOTOR_XTILT',	'X Rotation'),
		motor(4,4,'SR08ID01ROB01:MOTOR_YTILT',	'Y Rotation'),
		motor(5,5,'SR08ID01ROB01:MOTOR_ZTILT',	'Z Rotation')
	]
	# Do we need the moves to happen one after the other or can they happen simulatenously?
	simulatenousCommands = False
	# The workpoint is a settable point to tell the patient support to move around (i.e. a Robot TCP).
	workpoint = True
	WORKPOINT_CONTROLLER = {
		'TCP_AXIS1': 'SR08ID01ROB01:TCP_AXIS1',
		'TCP_AXIS2': 'SR08ID01ROB01:TCP_AXIS2',
		'TCP_AXIS3': 'SR08ID01ROB01:TCP_AXIS3',
		'TCP_AXIS_RBV1': 'SR08ID01ROB01:TCP_AXIS_RBV1',
		'TCP_AXIS_RBV2': 'SR08ID01ROB01:TCP_AXIS_RBV2',
		'TCP_AXIS_RBV3': 'SR08ID01ROB01:TCP_AXIS_RBV3',
		'TOOL_NO': 'SR08ID01ROB01:TOOL_NO',
		'TOOL_NO_RBV': 'SR08ID01ROB01:TOOL_NO_RBV',
		'READ_TCP': 'SR08ID01ROB01:READ_TCP',
		'SET_TCP': 'SR08ID01ROB01:SET_TCP',
		'ZERO_TOOL': 'SR08ID01ROB01:ZERO_TOOL'
	}
	# How is the speed controlled, per axis or globally? 
	# Options are: axis/global
	velocityMode = 'global'
	VELOCITY_CONTROLLER = {
		'Velocity': 'SR08ID01ROB01:VELOCITY',
		'Acceleration': 'SR08ID01ROB01:ACCELERATION',
	}
	velocity = 5
	velocityRange = [2,50]
	accelerationRange = [2,500]

	# Define the config for the vertical translation for imaging and treatment.
	VERTICALMOTION_CONTROLLER = motor(2,0,'SR08ID01ROB01:MOTOR_Z','Vertical Translation Motor')

class machine:
	""" A configuration for the machine - can be used to preconfigure things for Hutch 2B or Hutch 3B etc. """
	# Imaging mode: (dynamic/static/step).
	imagingMode = 'dynamic'
	# The following can be set as strings, as long as they have a configuration file stored in the database folder.
	imager = 'hamamama'
	imagingBeam = 'monochromatic'
	treatmentBeam = 'polychromatic'
	patientSupport = 'laps'



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
	velocity = patientSupport.velocity
	velocityRange = patientSupport.velocityRange