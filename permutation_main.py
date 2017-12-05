from metaext import *
import os


CONJUNCTION = ('pFgA_given_pF=0.50', 0.60, None)
PAIR_IMGS = ['pFgA_given_pF', 'pFgA_z']  # pairwise

MASK_FILE = 'mPFC_masks_20170207/' + maskFile


def main():
    terms = []  # todo
    dataset = ns.Dataset(filename='current_data/database.txt', masker=MASK_FILE)
    dataset.add_features('current_data/features.txt')
    # dataset = ns.Dataset.load('current_data/dataset.pkl')
    print 'dataset loaded'

    compare_term_pairs_with_conjunction_map(dataset, terms, terms, [CONJUNCTION], image_names=PAIR_IMGS)
