import dicom
import os

path = '/Users/micahbarnes/Desktop/SyncFebRatCT/'
# path = '/Users/micahbarnes/Desktop/'

dataset = []
for root, dirs, files in os.walk(path):
	for fn in files:
		if fn.endswith('.dcm'): 
			# print(fn)
			# dataset[fn] = os.sep.join([dirpath, fn])
			fn = path+fn
			# print(fn)
			dataset.append(fn)

for i in range(len(dataset)):
	# Read file.
	temp = dicom.read_file(dataset[i])
	# new file name.
	fn = path+'/ct_'+str(int(temp.AcquisitionNumber))+'.dcm'
	# rename file
	os.rename(dataset[i],fn)



# def find(filename, path):
#   for root, dirs, files in os.walk(path):
#     if filename in files:
#       print(os.path.join(root, filename))