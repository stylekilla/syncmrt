import pydicom as dicom
import numpy as np

class rtplan:
	def __init__(self,fp,ds):
		self.fp = fp
		self.ds = ds
		self.outcome = ""

		# If ds has 1 or more files, then read files.
		if len(ds) > 0:
			plan = dicom.read_file(ds[0])

			# Set empty vals.
			self.gantryAngle = np.zeros(len(plan.BeamSequence))

			# Get actual vals.
			for i in range(len(plan.BeamSequence)):
				self.gantryAngle[i] = plan.BeamSequence[i].ControlPointSequence[0].GantryAngle

			self.isoc = plan.BeamSequence[0].ControlPointSequence[0].IsocenterPosition

			self.outcome = "Loaded " + str(len(plan.BeamSequence)) + " treatment port(s)."

		else:
			self.outcome = "No treatment plan files were found."