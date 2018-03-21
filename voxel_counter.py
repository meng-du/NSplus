import os
import numpy as np

paths = [folder for folder in os.listdir('.') if folder.startswith('BA')]

for path in paths:
    for filename in os.listdir(path):
        if not filename.endswith('conjunction.csv'):
            continue
        with open(path + '/' + filename, 'r') as infile:
            voxels = np.array(infile.read().splitlines()[2:])
        unique, counts = np.unique(voxels, return_counts=True)
        print path + '/' + filename
        print np.asarray((unique, counts)).T
