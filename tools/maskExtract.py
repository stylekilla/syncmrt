'''
Extract masks from RTPLAN and export as *.DWG for fabrication.
'''
import dicom
import numpy as np
from dxfwrite import DXFEngine as dxf

class mask:
	def __init__(self,fpRtplan):
		self.rtplan = dicom.read_file(fpRtplan)
		self.mask = []
		self.maskSize = [40,40]

	def extract(self):
		'''Extract block data from RTPLAN.'''
		for i in range(int(self.rtplan.FractionGroupSequence[0].NumberOfBeams)):
			self.mask.append(self.rtplan.BeamSequence[i].BlockSequence[0].BlockData)

	def export(self):
		for i in range(len(self.mask)):
			self.drawmask(i)
			
	def drawmask(self,index):
		numberOfPoints = int(len(self.mask[index])/2)

		# Pair points as x,y.
		points = []
		for i in range(numberOfPoints):
			x = self.mask[index][i*2]
			y = self.mask[index][i*2+1]
			points.append([x,y])
		points.append(points[0])

		# NEED TO ROTATE POINTS BY 90 CCW

		# Create dwg and add lines.
		fn = 'BeamPort'+str(index)+'.dxf'
		dwg = dxf.drawing(fn)
		dwg.add(dxf.polyline(points))
		dwg.add(dxf.rectangle([-self.maskSize[0]/2,-self.maskSize[1]/2],
			self.maskSize[0],self.maskSize[1]))
		dwg.save()