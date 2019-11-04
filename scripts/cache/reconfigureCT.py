import dicom
import os

path = '/home/imbl/Documents/Data/CT/MBIscans/Lucy/'
# path = '/Users/micahbarnes/Desktop/'

dataset = []
for root, dirs, files in os.walk(path):
	for fn in files:
		if fn.startswith('8'):
			# dataset[fn] = os.sep.join([dirpath, fn])
			fn = path+fn
			# print(fn)
			dataset.append(fn)

print(dataset)

for i in range(len(dataset)):
	# Read file.
	print(dataset[i])
	temp = dicom.read_file(dataset[i])
	# new file name.
	fn = path+'ct_'+str(int(temp.InstanceNumber))+'.dcm'
	# rename file
	print(fn)
	os.rename(dataset[i],fn)



# def find(filename, path):
#   for root, dirs, files in os.walk(path):
#     if filename in files:
#       print(os.path.join(root, filename))