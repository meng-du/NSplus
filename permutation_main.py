from metaext import *
import random
import csv


CONJUNCTION = ('pFgA_given_pF=0.50', 0.60, None)
PAIR_IMGS = ['pFgA_given_pF', 'pFgA_z']  # pairwise

MASK_FILE = 'mPFC_masks_20170207/BA9_BA10_BA11_d1_mid.nii'

NUM_RAND_TERMS = 5

OUTPUT_FILE = 'conjunction_permutation.csv'


def main():
    # dataset = ns.Dataset(filename='current_data/database.txt', masker=MASK_FILE)
    # dataset.add_features('current_data/features.txt')
    # dataset.save('BA9_BA10_BA11_d1_mid_dataset.pkl')
    dataset = ns.Dataset.load('BA9_BA10_BA11_d1_mid_dataset.pkl')
    all_terms = [term for term in dataset.get_feature_names() if not term[0].isdigit()]
    print 'dataset loaded'

    # with open(OUTPUT_FILE, 'w') as outfile:
    #     writer = csv.writer(outfile, delimiter=',')
    #     writer.writerow(['target term', 'other terms'] + ['' for _ in range(NUM_RAND_TERMS - 2)] + ['voxels'])

    for _ in range(100):
        # terms = ['(social | mentalizing)'] + random.sample(all_terms, NUM_RAND_TERMS - 1)
        terms = ['(social | mentalizing)', 'appropriate', 'neurodegenerative', 'hyperactivity', 'group healthy']
        print terms
        try:
            result = compare_term_pairs_with_conjunction_map(dataset, terms, terms, [CONJUNCTION],
                                                             image_names=PAIR_IMGS)
            for i, conjunction in enumerate(result):
                num_voxels = dict(zip(*np.unique(conjunction.images.values()[0], return_counts=True)))
                print terms[i], num_voxels
                row = [terms[i]] + terms[:i] + terms[i+1:] + [num_voxels[float(NUM_RAND_TERMS - 1)]]

                with open(OUTPUT_FILE, 'a') as outfile:
                    writer = csv.writer(outfile, delimiter=',')
                    writer.writerow(row)

        except Exception as e:
            print terms, e
            pass


if __name__ == '__main__':
    main()
