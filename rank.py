from metaext import *
import os

if __name__ == '__main__':
    MASK_FOLDER = 'mPFC_masks_20170207'
    maskFiles = [mask for mask in os.listdir(MASK_FOLDER) if mask[0] != '.']
    log = []
    for maskFile in maskFiles:
        dataset = ns.Dataset(filename='current_data/database.txt', masker=MASK_FOLDER + '/' + maskFile)
        dataset.add_features('current_data/features.txt')
        print 'dataset loaded'
        print maskFile

        maskdir = 'results_v5/pairwise_conjunctions_1/' + maskFile[:-4] + '/'
        maskcsvs = [csvfile for csvfile in os.listdir(maskdir) if csvfile.endswith('csv')]
        for maskcsv in maskcsvs:
            with open(maskdir + maskcsv, 'r') as csvfile:
                content = list(csv.reader(csvfile))[2:]
                mask = np.array([int(row[0][0]) for row in content]) == 4
            print maskcsv
            term = maskcsv[:maskcsv.index('_pFgA_given_pF')]
            print term, mask.sum()
            log.append((term, mask.sum()))

            rank(dataset,
                 rank_by='pFgA_given_pF=0.50',
                 extra_expr=[
                    '(social | mentalizing)',
                    'emotion*',
                    '(value | reward | incentive)',
                    '(episodic | future | past | retrieval | prospective | memory retrieval)'],
                 csv_file=term + '_' + maskFile[:-4] + '_rank.csv',
                 mask=mask)
    import json
    with open('log.json', 'w') as outfile:
        outfile.write(json.dumps(log))
