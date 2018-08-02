"""

This script is used to generate TIFF sequences and videos from .nd2 files.

Required libraries:

ND2Reader (pip install nd2reader)
matplotlib (pip install matplotlib)
Pillow (pip install Pillow)

-------

Inputs: 

- One or more .nd2 files.
- A .CSV file (which can be exported from Excel) that describes which z-slices 
to use for each XY field of view.
- Output folder.

The .CSV file format should be the following ([brackets] denotes example data):

XY, 	Sequence1z, 	Sequence2z, ...	,	SequenceNz              <--- Column headers
[200],	[3],			[2]				,	[3]
...		...				...					...

Where the number of columns should be equal to ([Num .nd2 files provided] + 1).
That is, "N" in "SequenceNz" should be the number of .nd2 files provided to the 
script.

Each row corresponds to a single XY field of view. The "XY" column lists the
field of view number. The remaining columns list the Z-slice index that should
be used for that XY field of view in each supplied .nd2 file. The order of
columns should line up with the order of filenames supplied in this script (i.e.
Sequence1z will describe the z-slices of the first .nd2 file provided to this
script).

-------

Outputs:

For each XY field of view, a folder is created (within the supplied output 
folder path) that contains a sequence of TIFF files, where each TIFF file is 
from the desired z-slice for that XY field of view. If a z-slice was not 
provided for that field of view (i.e. left blank in the .CSV file), that field 
of view will be skipped.

If multiple .nd2 files are provided, the TIFF files generated for each will be
grouped together based on XY field of view (with the z-slices being determined
by each .nd2 file's correspond .CSV file) and ordered in the same manner as the
order of the .nd2 files.

-------

Author: Jonathan Matthews
Date Created: 06/29/2017
Last Modified: 06/29/2017

"""

### Input Parameters

# Full path and name of the CSV file.
csvFilename = "C:\\Users\\brook\\Documents\\Lab\\Python_Scripts\\NIS_File_Organizer.csv"

# Full path to output folder (include slashes at the end)
outputFolder = "D:\\20180122MIS_SOK\\Brightfield\\"

nd2Filenames = []

# Full path and name of the first .ND2 file.
nd2Filenames.append('E:\\20180122_MIS_SOK\\2018122_MIS_SOK003.nd2')
nd2Filenames.append('E:\\20180122_MIS_SOK\\2018122_MIS_SOK004.nd2')
nd2Filenames.append('E:\\20180122_MIS_SOK\\2018122_MIS_SOK005.nd2')
nd2Filenames.append('E:\\20180122_MIS_SOK\\2018122_MIS_SOK006.nd2')
nd2Filenames.append('E:\\20180122_MIS_SOK\\2018122_MIS_SOK007.nd2')
# Copy and paste the above line for each other .ND2 file needed. Remember the
# order should match the columns of the .CSV file.

### SCRIPT BELOW
import sys
print sys.version

from nd2reader import ND2Reader
from PIL import Image
import matplotlib.pyplot as plt
import os
import csv
import numpy
import ntpath

csvFile = open(csvFilename, 'rb')
csvReader = csv.reader(csvFile)

header = csvReader.next()

if (len(nd2Filenames) + 1) != len(header):
	print "Number of .nd2 files (" + str(len(nd2Filenames)) + ") does not match the number of CSV sequence columns (" + str(len(header)) + ")."
	csvFile.close()
	quit()

readers = []
parsers = []
for nd2Filename in nd2Filenames:
	reader = ND2Reader(nd2Filename)
	readers.append(reader)
	parsers.append(reader.parser)

for row in csvReader:
	XY = int(row[0])
	z_slices = row[1:]
	for experiment in range(len(row[1:])):
		z_slice = row[experiment+1]

		if z_slice != '':
			## We should have a good Z
			z_slice = int(z_slice)

			num_times = readers[experiment].metadata['num_frames']
			height = readers[experiment].metadata['height']
			width = readers[experiment].metadata['width']
			for t in range(num_times):
				image_array = parsers[experiment].get_image_by_attributes(t, XY-1, u'BF', z_slice-1, height, width)
				destination_folder = outputFolder + "XY" + str(XY)
				
				if not os.path.exists(destination_folder):
					os.makedirs(destination_folder)


				export_filename = ntpath.basename(nd2Filenames[experiment]).split('.')[0].lower() + "xy%003d" % XY + "t%003d" % (t+1) + "z" + str(z_slice) + ".tiff"

				image_array = image_array.astype(numpy.uint16)

				image = Image.fromarray(image_array)
				image.save(destination_folder + "/" + export_filename)
	

