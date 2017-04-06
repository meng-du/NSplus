from metaext import *
import os


def quick_test():
    dataset = ns.Dataset.load('current_data/dataset.pkl')
    TERMS = ['emotion*', 'self', 'autobiographical']
    # for term in TERMS:
    #     print term
    #     analyze_expression(dataset, term, priors=[0.5], dataset_size=11405)
    # print 'pairs'
    # compare_term_pairs(dataset, TERMS, TERMS, evenStudySetSize=False)
    print 'conjunction'
    compare_term_pairs_with_conjunction_map(dataset, TERMS, TERMS, conjunctions=[('pFgA_z', 1.5)],
                                            numIterations=1, save_files=True)
    # print 'group'
    # compare_term_group(dataset, TERMS, evenStudySetSize=False)


if __name__ == '__main__':
    # quick_test()
    MASK_FOLDER = 'mPFC_masks_20170207'
    TERMS = [
        '(social | mentalizing)',
        'self',
        'emotion*',
        '(value | reward | incentive)',
        '(episodic | future | past | retrieval | prospective | memory retrieval)'
    ]
    analysis_name = 'social_self_emotion*_value_episodic'
    print analysis_name
    # IMAGES = None
    SINGLE_IMGS = ['pA', 'pAgF', 'pAgF_z', 'pFgA_given_pF', 'pFgA_z']  # single
    PAIR_IMGS = ['pFgA_given_pF', 'pFgA_z']  # pairwise
    CONJUNCTION = ('pFgA_given_pF=0.50', 0.60, None)
    SELECTIVITY = [('pFgA_given_pF=0.50', (0.50, 0.60))]
    SINGLE_CONJ = (0.60, None)
    PAIR_CONJ = (0.40, 0.60)
    maskFiles = [mask for mask in os.listdir(MASK_FOLDER) if mask[0] != '.']
    for maskFile in maskFiles:
        # ns.dataset.download(path='.', unpack=True)
        dataset = ns.Dataset(filename='current_data/database.txt', masker=MASK_FOLDER + '/' + maskFile)
        dataset.add_features('current_data/features.txt')
        # dataset = ns.Dataset.load('current_data/dataset.pkl')
        print 'dataset loaded'
        print maskFile
        dirname = maskFile[:-4]
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        ### ANALYSIS ###
        # results = []
        # for term in TERMS:
        #     print term
        #     results.append(analyze_expression(dataset, term, priors=[0.5], dataset_size=11405, image_names=SINGLE_IMGS))
        # results.append(compare_term_pairs(dataset, [TERMS[0]], [TERMS[1]], numIterations=500,
        #                                   image_names=PAIR_IMGS)[0][0])
        # MetaExtension.get_conjunction_image_with_separate_criteria(results, [SINGLE_CONJ, SINGLE_CONJ, PAIR_CONJ],
        #                                                            binary=True, image_name='pFgA_given_pF=0.50',
        #                                                            file_prefix=analysis_name)
        # MetaExtension.get_conjunction_image(metaext_list=results, lower_threshold=CONJUNCTION[1],
        #                                     upper_threshold=CONJUNCTION[2], image_name=CONJUNCTION[0], file_prefix='')
        # compare_term_pairs_with_conjunction_map(dataset, TERMS, TERMS, [CONJUNCTION], image_names=PAIR_IMGS)
        selresults = compare_term_pairs_with_selectivity_map(dataset, TERMS, TERMS, SELECTIVITY, image_names=PAIR_IMGS)
        MetaExtension.get_max_image(selresults[0], image_name=SELECTIVITY[0][0], file_prefix=analysis_name)
        # compare_term_pairs(dataset, TERMS, TERMS, numIterations=500)
        # MetaExtension.get_conjunction_image(results, lower_threshold=0.60, image_name='pFgA_given_pF=0.50')
        # compare_terms_group(dataset, TERMS, evenStudySetSize=True, numIterations=100)
        ### ANALYSIS ###

        # directories
        source_files = [filename for filename in os.listdir('.')
                       if ('.nii.gz' in filename or '.csv' in filename) and ('selectivity' not in filename)]
        if not os.path.exists('source_files'):
            os.makedirs('source_files')
        for filename in source_files:
            os.rename(filename, 'source_files/' + filename)

        output = [filename for filename in os.listdir('.') if ('.nii.gz' in filename or '.csv' in filename)]
        output.append('source_files')
        for filename in output:
            os.rename(filename, dirname + '/' + filename)

    for thing in os.listdir('.'):
        if thing.startswith('BA'):
            if not os.path.exists(analysis_name):
                os.makedirs(analysis_name)
            os.rename(thing, analysis_name + '/' + thing)
