from metaext import *
import os


if __name__ == '__main__':
    MASK_FOLDER = 'mPFC_masks_20170207'
    TERMS = [
        '(social | mentalizing)',
        'self',
        '(value | reward | incentive)',
        '(choice | decision making)',
        '(value | reward | incentive | choice | decision making)',
        'emotion*',
        '(episodic | future | past | autobiographical | retrieval | prospective | memory retrieval)',
        '(episodic | future | past | retrieval | prospective | memory retrieval)',
        'autobiographical',
        '(scene | semantic knowledge | semantic memory | construction | imagine*)'
    ]
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
        images = ['pFgA_given_pF', 'pFgA_z']
        # for term in TERMS:
        #     print term
        #     analyze_expression(dataset, term, priors=[0.5], dataset_size=11405, image_names=images)
        compare_term_pairs(dataset, TERMS, TERMS, evenStudySetSize=True, numIterations=500, image_names=images)
        # compare_terms_group(dataset, TERMS, evenStudySetSize=True, numIterations=100)
        ### ANALYSIS ###

        output = [filename for filename in os.listdir('.') if ('.nii.gz' in filename or 'output.csv' in filename)]
        for filename in output:
            os.rename(filename, dirname + '/' + filename)

'''
only keep voxels that pass the .60 threshold for each test, if >=.60 for all four of these it gets a 1:
social_vs_emotion__pFgA_given_pF=0.50.nii
social_vs_episodic_pFgA_given_pF=0.50.nii
social_vs_self_pFgA_given_pF=0.50.nii
social_vs_value_pFgA_given_pF=0.50.nii

setting the threshold for each file to 1.96:
social_vs_emotion__pFgA_z.nii.gz
social_vs_scene_pFgA_z.nii.gz
social_vs_self_pFgA_z.nii.gz
social_vs_value_pFgA_z.nii.gz

just BA11 ROI, number > .60 (2 overlap vs. all three overlap).:
social_pFgA_given_pF=0.50.nii.gz
episodic_pFgA_given_pF=0.50.nii.gz
scene_pFgA_given_pF=0.50.nii.gz


social_vs_emotion__pFgA_z.nii.gz
social_vs_scene_pFgA_z.nii.gz
social_vs_self_pFgA_z.nii.gz
social_vs_value_pFgA_z.nii.gz

'''