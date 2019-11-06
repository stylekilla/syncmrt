# Remove files in folder.
# os.remove(fol)
import shutil
import os
# folder = '/path/to/folder'

cache_path = '/home/imbl/Documents/Data/XR/cache/'
set_path = '/home/imbl/Documents/Data/XR/set/'

print('Clearing cache...')
for the_file in os.listdir(cache_path):
	file_path = os.path.join(cache_path, the_file)
	try:
		if os.path.isfile(file_path):
			os.unlink(file_path)
		#elif os.path.isdir(file_path): shutil.rmtree(file_path)
	except Exception as e:
		print(e)

print('Clearing set...')
for the_file in os.listdir(set_path):
	file_path = os.path.join(set_path, the_file)
	try:
		if os.path.isfile(file_path):
			os.unlink(file_path)
		#elif os.path.isdir(file_path): shutil.rmtree(file_path)
	except Exception as e:
		print(e)

print('Done!')