from metaext import *
import os

if __name__ == '__main__':
    MASK_FOLDER = 'mPFC_masks_20170207'
    maskFiles = [mask for mask in os.listdir(MASK_FOLDER) if mask[0] != '.']
    for maskFile in maskFiles:
        dataset = ns.Dataset(filename='current_data/database.txt', masker=MASK_FOLDER + '/' + maskFile)
        dataset.add_features('current_data/features.txt')
        print 'dataset loaded'
        print maskFile

        rank(dataset,
             rank_by='pFgA_given_pF=0.50',
             extra_expr=[
                '(social | mentalizing)',
                'self',
                'emotion*',
                '(value | reward | incentive)',
                '(episodic | future | past | retrieval | prospective | memory retrieval)'],
             csv_file=maskFile[:-4] + '_rank.csv')
