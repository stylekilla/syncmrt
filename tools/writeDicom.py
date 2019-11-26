# write_new.py
"""Simple example of writing a DICOM file from scratch using pydicom.
This example does not produce a DICOM standards compliant file as written,
you will have to change UIDs to valid values and add all required DICOM data
elements
"""
# Copyright (c) 2010-2012 Darcy Mason
# This file is part of pydicom, released under a modified MIT license.
#    See the file license.txt included with this distribution, also
#    available at https://github.com/darcymason/pydicom

from __future__ import print_function

import sys
import datetime
import os.path
import pydicom
from pydicom.dataset import Dataset, FileDataset
import pydicom.uid

if __name__ == "__main__":
    print("---------------------------- ")
    print("write_new.py example program")
    print("----------------------------")
    print("Demonstration of writing a DICOM file using pydicom")
    print("NOTE: this is only a demo. Writing a DICOM standards compliant file")
    print("would require official UIDs, and checking the DICOM standard to ensure")
    print("that all required data elements were present.")
    print()

    if sys.platform.lower().startswith("win"):
        filename = r"c:\temp\test.dcm"
        filename2 = r"c:\temp\test-explBig.dcm"
    else:
        homedir = os.path.expanduser("~")
        filename = os.path.join(homedir, "test.dcm")
        filename2 = os.path.join(homedir, "test-explBig.dcm")

    print("Setting file meta information...")
    # Populate required values for file meta information
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"  # !! Need valid UID here for real work
    file_meta.ImplementationClassUID = "1.2.3.4"  # !!! Need valid UIDs here

    print("Setting dataset values...")

    # Create the FileDataset instance (initially no data elements, but file_meta supplied)
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)

    # Add the data elements -- not trying to set all required here. Check DICOM standard
    ds.PatientName = "Test^Firstname"
    ds.PatientID = "123456"

    # Set the transfer syntax
    ds.is_little_endian = True
    ds.is_implicit_VR = True

    # Set creation date/time
    dt = datetime.datetime.now()
    ds.ContentDate = dt.strftime('%Y%m%d')
    timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
    ds.ContentTime = timeStr

    print("Writing test file", filename)
    ds.save_as(filename)
    print("File saved.")

    # Write as a different transfer syntax
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRBigEndian  # XXX shouldn't need this but pydicom 0.9.5 bug not recognizing transfer syntax
    ds.is_little_endian = False
    ds.is_implicit_VR = False

    print("Writing test file as Big Endian Explicit VR", filename2)
    ds.save_as(filename2)



    '''
    import dicom, dicom.UID
from dicom.dataset import Dataset, FileDataset
import numpy as np
import datetime, time

def write_dicom(pixel_array,filename):
    """
    INPUTS:
    pixel_array: 2D numpy ndarray.  If pixel_array is larger than 2D, errors.
    filename: string name for the output file.
    """

    ## This code block was taken from the output of a MATLAB secondary
    ## capture.  I do not know what the long dotted UIDs mean, but
    ## this code works.
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
    file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
    file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'
    ds = FileDataset(filename, {},file_meta = file_meta,preamble="\0"*128)
    ds.Modality = 'WSD'
    ds.ContentDate = str(datetime.date.today()).replace('-','')
    ds.ContentTime = str(time.time()) #milliseconds since the epoch
    ds.StudyInstanceUID =  '1.3.6.1.4.1.9590.100.1.1.124313977412360175234271287472804872093'
    ds.SeriesInstanceUID = '1.3.6.1.4.1.9590.100.1.1.369231118011061003403421859172643143649'
    ds.SOPInstanceUID =    '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
    ds.SOPClassUID = 'Secondary Capture Image Storage'
    ds.SecondaryCaptureDeviceManufctur = 'Python 2.7.3'

    ## These are the necessary imaging components of the FileDataset object.
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.HighBit = 15
    ds.BitsStored = 16
    ds.BitsAllocated = 16
    ds.SmallestImagePixelValue = '\\x00\\x00'
    ds.LargestImagePixelValue = '\\xff\\xff'
    ds.Columns = pixel_array.shape[0]
    ds.Rows = pixel_array.shape[1]
    if pixel_array.dtype != np.uint16:
        pixel_array = pixel_array.astype(np.uint16)
    ds.PixelData = pixel_array.tostring()

    ds.save_as(filename)
    return



if __name__ == "__main__":
#    pixel_array = np.arange(256*256).reshape(256,256)
#    pixel_array = np.tile(np.arange(256).reshape(16,16),(16,16))
    x = np.arange(16).reshape(16,1)
    pixel_array = (x + x.T) * 32
    pixel_array = np.tile(pixel_array,(16,16))
    write_dicom(pixel_array,'pretty.dcm')
'''