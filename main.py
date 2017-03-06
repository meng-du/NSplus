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
    compare_term_pairs_with_conjunction_map(dataset, TERMS, TERMS, conjunction_images=[('pFgA_z', 1.5)],
                                            numIterations=1, save_files=True)
    # print 'group'
    # compare_term_group(dataset, TERMS, evenStudySetSize=False)


if __name__ == '__main__':
    # quick_test()
    MASK_FOLDER = 'mPFC_masks_20170207'
    TERMS = [
        '(emotion &~ (emotional faces | emotional stimuli | * face | face* | *perception))',
        '(choice | decision making)',
        '(episodic | future | past | retrieval | prospective | memory retrieval)',
        '(scene | semantic knowledge | semantic memory | construction | imagine*)',
        'self',
        '(social | mentalizing)',
        '(value | reward | incentive)'
    ]
    # IMAGES = None
    # IMAGES = ['pA', 'pAgF', 'pAgF_z', 'pFgA_given_pF', 'pFgA_z']  # single
    IMAGES = ['pFgA_given_pF', 'pFgA_z']  # pairwise
    CONJUNCTIONS = [('pFgA_given_pF=0.50', 0.50), ('pFgA_given_pF=0.50', 0.55), ('pFgA_given_pF=0.50', 0.60)]
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
        results = []
        # for term in TERMS:
        #     print term
        #     results.append(analyze_expression(dataset, term, priors=[0.5], dataset_size=11405, image_names=IMAGES))
        # MetaExtension.get_conjunction_image(results, CONJUNCTION[0][1], CONJUNCTION[0][0],
        #                                     file_prefix='social_episodic_emotion')
        compare_term_pairs_with_conjunction_map(dataset, TERMS, TERMS, conjunction_images=CONJUNCTIONS,
                                                numIterations=500, image_names=IMAGES)
        # compare_term_pairs(dataset, TERMS, TERMS, numIterations=500)
        # MetaExtension.get_conjunction_image(results, 0.60, image_name='pFgA_given_pF=0.50')
        # compare_terms_group(dataset, TERMS, evenStudySetSize=True, numIterations=100)
        ### ANALYSIS ###

        output = [filename for filename in os.listdir('.') if ('.nii.gz' in filename or '.csv' in filename)]
        for filename in output:
            os.rename(filename, dirname + '/' + filename)
