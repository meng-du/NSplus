import neurosynth as ns
import random
import numpy as np
import csv
import os
from study_ids import *


class MetaAnalysisInfo(object):
    def __init__(self, expression, studySetSize, contraryExpression='', contraryStudySetSize=-1,
                 metaAnalysis=None, images=None):
        self.expression = expression
        self.studySetSize = studySetSize
        self.contraryExpression = contraryExpression
        self.contraryStudySetSize = contraryStudySetSize
        self.metaAnalysis = metaAnalysis
        self.images = images
        if images is None and metaAnalysis is not None:
            self.images = self.metaAnalysis.images

    def init_with_mean_images(self, meanImages):
        return MetaAnalysisInfo(self.expression, self.studySetSize, self.contraryExpression, self.contraryStudySetSize,
                                images=meanImages)

    def print_info(self):
        print [self.expression, self.studySetSize, self.contraryExpression, self.contraryStudySetSize]

    def get_images_as_list(self, image_names=None):
        """
        Get a list of images prefixed with information
        :param image_names: the names of images to be included in the result. If None, all images will be returned.
        :return: a list of images (a list of lists of strings)
        """
        if self.images is None:
            raise RuntimeError('Images not initialized')
        result = []
        # Note: the length of image arrays exceeds the maximum number of columns of MS Excel
        for imageName in self.images.keys():
            if (image_names is not None) and (imageName not in image_names):
                continue
            imageAsList = self.images[imageName].tolist()
            if self.contraryStudySetSize == -1:
                prefix = [self.expression, self.studySetSize, imageName]
            else:
                prefix = [self.expression, self.studySetSize, self.contraryExpression, self.contraryStudySetSize,
                          imageName]
            result.append(prefix + imageAsList)
        return result

    def write_images_to_csv(self, filename, delimiter=',', image_names=None):
        data = np.array(self.get_images_as_list(image_names)).T
        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for row in data:
                writer.writerow(row)

    def save_images(self, mask):
        if self.images is None:
            raise RuntimeError('Images not initialized')
        for imageName in self.images.keys():
            filename = get_first_word_in_expression(self.expression)
            if self.contraryStudySetSize != -1:
                filename += '_vs_' + get_first_word_in_expression(self.contraryExpression)
            filename += '_' + imageName + '.nii.gz'
            ns.imageutils.save_img(self.images[imageName], filename=filename, masker=mask)

    @classmethod
    def get_mean_images(cls, metaInfoLists):
        """
        :param metaInfoLists: a list of lists of MetaAnalysisInfo to be averaged
        :return: a list of MetaAnalysisInfo
        """
        if len(metaInfoLists) == 1:
            meanMetaInfoList = metaInfoLists[0]
        else:
            meanMetaInfoList = []
            # calculate means for each comparison across all iterations
            for metaInfos in zip(*metaInfoLists):  # iterating through columns
                # find intersection of image names  # TODO change names to common ones instead of finding them?
                allImgNames = [metaInfo.metaAnalysis.images.keys() for metaInfo in metaInfos]
                imgNames = set(allImgNames[0]).intersection(*allImgNames)
                # calculate means
                meanImages = {}
                for imgName in imgNames:
                    meanImages[imgName] = np.mean([metaInfo.images[imgName] for metaInfo in metaInfos], axis=0)
                meanMetaInfoList.append(metaInfos[0].init_with_mean_images(meanImages))
        return meanMetaInfoList

    @classmethod
    def write_info_list_to_csv(cls, metaAnalysisInfoList, outfilename, delimiter=','):
        results = np.concatenate([metaAnalysisInfo.get_images_as_list() for metaAnalysisInfo in metaAnalysisInfoList])
        results = results.T  # transpose
        with open(outfilename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for result in results:
                writer.writerow(result)


def get_first_word_in_expression(expression):
    word = expression.split(' ', 1)[0]
    if word[0] == '(':
        word = word[1:]
    if word == 'episodic':
        word = 'episodic_with_autobio' if 'autobiographical' in expression else 'episodic_without_autobio'
    if ('value' in expression) and ('choice' in expression):
        word = 'value_choice'
    return word


def get_expressions_one_to_one(term, termList):
    """
    Generate all the possible permutations of expression 'term &~ termInList' or 'termInList &~ term'

    :param term: a term string to compare
    :param termList: a string list containing the other terms to be compared to
    :return: a list of tuples (term &~ termInList, termInList &~ term) containing the result expressions
    """
    expressions = []
    for otherTerm in termList:
        if term != otherTerm:
            expressions.append((term + ' &~ ' + otherTerm, otherTerm + ' &~ ' + term))
    return expressions


def get_expression_one_to_all(term, termList):
    """
    Return expression 'term &~ (termInListA | termInListB | ...)', i.e. term and not other terms in the list
    """
    otherTerms = '(' + ' | '.join([otherTerm for otherTerm in termList if otherTerm != term]) + ')'
    return term + ' &~ ' + otherTerms


def read_pkl_data(filePath, maskerPath=None):
    """
    :param filePath: a string path to a pickled dataset file (.pkl)
    :param maskerPath: a string path to a .nii.gz masker file
    :return: a neurosynth Dataset object
    """
    dataset = ns.Dataset.load(filePath)
    if maskerPath is not None:
        dataset.masker = ns.mask.Masker(maskerPath)
    return dataset


def compare_two_study_sets(dataset, studySet1, studySet2, prior=None):
    """
    :param dataset: a neurosynth Dataset instance
    :param studySet1, studySet2: two lists of study ids to compare
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study; if None, the empirically estimated p(term) will be used
                  (calculated as number_of_studies_with_term  / total_number_of_studies)
    :return: two neurosynth MetaAnalysis objects (studySet1 vs studySet2, and studySet2 vs studySet1)
    """
    # get priors
    if prior:
        prior1 = prior
        prior2 = prior
    else:
        totalNum = len(studySet1) + len(studySet2)
        prior1 = 1.0 * len(studySet1) / totalNum
        prior2 = 1.0 * len(studySet2) / totalNum

    # meta analysis
    metaAnalysis1Vs2 = ns.meta.MetaAnalysis(dataset, studySet1, studySet2, prior=prior1)
    metaAnalysis2Vs1 = ns.meta.MetaAnalysis(dataset, studySet2, studySet1, prior=prior2)

    return metaAnalysis1Vs2, metaAnalysis2Vs1


def even_study_set_size(studySets):
    """
    Reduce the sizes of all study sets to the smallest study set in that list, by random sampling
    :param studySets: a list of study sets, where a study set is a list of string study IDs
    :return: a new list of reduced study sets
    """
    minSize = min(map(len, studySets))
    reducedStudySets = []
    for studySet in studySets:
        reducedStudySets.append(random.sample(studySet, minSize))
    return reducedStudySets


def get_list_unions(lists):
    """
    Given a 2-D list of lists, return a list of unions of all other lists.
    For example, given [['1'], ['2'], ['3', '4']], return [['3', '4', '2'], ['1', '3', '4'], ['1', '2']].
    Cost O(n) time, O(n) space.
    :param lists: a list of lists of strings (study IDs)
    :return: a list of unions of all other lists
    """
    # adapted from stackoverflow.com/a/2680697
    result = []
    temp = []
    for i in range(len(lists)):
        result.append(list(temp))
        temp += lists[i]
    temp = []
    for i in range(len(lists) - 1, -1, -1):  # reverse traversal
        result[i] += list(temp)
        temp += lists[i]
    return result


def analyze_expression(dataset, expression, priors=(), dataset_size=None, image_names=None):
    """
    Analyze a single expression, output a csv file and a set of .nii.gz image files
    :param dataset:
    :param expression:
    :param priors:
    :param dataset_size:
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
    :return:
    """
    # get studies
    if expression == '(topic72_multitasking | dual)':
        studySet = multitask_studies
    elif expression == 'topic59_default_network':
        studySet = topic59_studies
    else:
        studySet = dataset.get_studies(expression=expression)
    # add real prior
    if dataset_size is None:
        dataset_size = len(dataset.get_studies(expression='*'))  # 11405
    priors.append(1.0 * len(studySet) / dataset_size)
    # analyze
    metaInfo = None
    for prior in priors:
        if 'pFgA_given_pF' in image_names:
            image_names.append('pFgA_given_pF=%0.2f' % prior)
        if 'pAgF_given_pF' in image_names:
            image_names.append('pAgF_given_pF=%0.2f' % prior)
        meta = ns.meta.MetaAnalysis(dataset, studySet, prior=prior)
        if metaInfo is None:
            metaInfo = MetaAnalysisInfo(expression, len(studySet), metaAnalysis=meta)
        else:
            for imgName in meta.images.keys():
                if imgName not in metaInfo.images.keys():
                    metaInfo.images[imgName] = meta.images[imgName]  # add new image
    # output
    metaInfo.write_images_to_csv(get_first_word_in_expression(expression) + '_output.csv', image_names=image_names)
    metaInfo.save_images(dataset.masker)


def compare_expressions(dataset, expressions, evenStudySetSize=True, numIterations=1, prior=None, filename=''):
    """
    Compare each expression to all the other expressions in the given list and return MetaAnalysis objects
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expressions: a list of string expressions to be compared to one another
    :param evenStudySetSize: if true, the larger study set will be randomly sampled to the size of the smaller set
    :param numIterations: (int) when study set sizes are evened, iterate more than once to sample multiple times
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study; if None, the empirically estimated p(term) will be used
                  (calculated as number_of_studies_with_term  / total_number_of_studies)
    :return: a dictionary where keys are 'expressionX vs expressionY' and values are corresponding neurosynth
             MetaAnalysis objects
    """
    # 0) error checking
    if len(expressions) < 2:
        raise ValueError('Must provide more than one expressions')
    if numIterations < 1:
        raise ValueError('Number of iterations must be greater than 0')
    if (not evenStudySetSize) and numIterations > 1:
        raise ValueError('Should not iterate more than once when sizes of study sets are not evened')
    if prior is not None and (prior <= 0 or prior >= 1):
        raise ValueError('prior has to be greater than 0 and less than 1')

    # 1) get studies
    studySets = []
    for expression in expressions:
        studySets.append(dataset.get_studies(expression=expression))

    metaInfoLists = []  # stores lists of MetaAnalysisInfo (one list per iteration)
    for i in range(numIterations):
        # 2) reduce sizes
        newStudySets = even_study_set_size(studySets) if evenStudySetSize else studySets

        # 3) get meta analysis results for each study set vs union of all other study sets
        studySetsToCompare = get_list_unions(newStudySets)
        metaInfoLists.append([])
        for j in range(len(newStudySets)):
            meta1VsOthers, metaOthersVs1 = compare_two_study_sets(dataset, newStudySets[j], studySetsToCompare[j], prior)
            if len(newStudySets) == 2:
                otherExpression = expressions[1 - j]
            else:
                otherExpression = 'union of "' + '", "'.join(expressions[:j] + expressions[(j + 1):]) + '"'
            metaInfo1VsOthers = MetaAnalysisInfo(expressions[j], len(newStudySets[j]),
                                                 otherExpression, len(studySetsToCompare[j]),
                                                 metaAnalysis=meta1VsOthers)
            metaInfoOthersVs1 = MetaAnalysisInfo(otherExpression, len(studySetsToCompare[j]),
                                                 expressions[j], len(newStudySets[j]),
                                                 metaAnalysis=metaOthersVs1)
            metaInfoLists[i].append(metaInfo1VsOthers)
            metaInfoLists[i].append(metaInfoOthersVs1)
            if len(newStudySets) == 2:  # no need to repeat if there are only 2 study sets to compare
                break
    # 4) get average image
    meanMetaResult = MetaAnalysisInfo.get_mean_images(metaInfoLists)

    # 5) save results TODO put this outside?
    MetaAnalysisInfo.write_info_list_to_csv(meanMetaResult, filename + '_output.csv')
    for meta in meanMetaResult:
        meta.save_images(dataset.masker)


def compare_term_pairs(dataset, termList1, termList2, evenStudySetSize=True, numIterations=1, prior=None):
    expressions = []
    for term1 in termList1:
        expressions += get_expressions_one_to_one(term1, termList2)
    for exprTuple in expressions:
        print exprTuple
        filename = get_first_word_in_expression(exprTuple[0]) + '_vs_' + get_first_word_in_expression(exprTuple[1])
        compare_expressions(dataset, exprTuple, evenStudySetSize, numIterations, prior, filename)


def compare_terms_group(dataset, termList, evenStudySetSize=True, numIterations=1, prior=None):
    expressions = []
    for term in termList:
        expressions.append(get_expression_one_to_all(term, termList))
    compare_expressions(dataset, expressions, evenStudySetSize, numIterations, prior, filename='group')


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
        '(scene | semantic knowledge | semantic memory | construction | imagine*)',
        '(topic72_multitasking | dual)',
        'topic59_default_network'
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
        for term in TERMS:
            print term
            images = ['pA', 'pAgF_z', 'pAgF', 'pFgA_given_pF', 'pFgA_z']
            analyze_expression(dataset, term, priors=[0.5], dataset_size=11405, image_names=images)
        # compare_term_pairs(dataset, TERMS, TERMS, evenStudySetSize=True, numIterations=100)
        # compare_terms_group(dataset, TERMS, evenStudySetSize=True, numIterations=100)
        ### ANALYSIS ###

        output = [filename for filename in os.listdir('.') if ('.nii.gz' in filename or 'output.csv' in filename)]
        for filename in output:
            os.rename(filename, dirname + '/' + filename)
