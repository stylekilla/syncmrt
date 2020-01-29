import yaml
from yaml import Loader, Dumper

class Config:
	def __init__(self,file):
		# Save the file.
		self.file = file
		# Get the file stream.
		stream = open(self.file,'r')
		# Load the data.
		self.data = yaml.load(stream.read(),Loader=Loader)

	def save(self):
		# Dump the config contents into a string.
		string = yaml.dump(self.data,Dumper=Dumper)
		with open(self.file,'w') as file:
			file.write(string)
		# Close the file.
		file.close()

	def __del__(self):
		# Save the file on object destruction.
		self.save()