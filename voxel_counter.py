import os
import numpy as np

masks = [folder for folder in os.listdir('results_v8_z_conj') if folder.startswith('BA')]

for mask in masks:
    path = 'results_v8_z_conj/' + mask + '/'
    for filename in sorted(os.listdir(path)):
        if not filename.endswith('conjunction.csv'):
            continue
        with open(path + filename, 'r') as infile:
            voxels = np.array(infile.read().splitlines()[2:])
        unique, counts = np.unique(voxels, return_counts=True)
        print mask + ' - ' + filename
        for val, count in zip(unique, counts):
            print '  "%s": %d' % (val[0], count)
