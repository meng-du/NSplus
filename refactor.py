from neurosynth import Dataset, meta
from neurosynth.base import imageutils
import random
import numpy as np
import csv


class MetaAnalysisInfo(object):
    def __init__(self, expression, studySetSize, contraryExpression, contraryStudySetSize,
                 metaAnalysis=None, images=None):
        self.expression = expression
        self.studySetSize = studySetSize
        self.contraryExpression = contraryExpression
        self.contraryStudySetSize = contraryStudySetSize
        self.metaAnalysis = metaAnalysis
        self.images = images
        if images is None and metaAnalysis is not None:
            self.images = self.metaAnalysis.images

    @classmethod
    def with_mean_images(cls, metaAnalysis, meanImages):
        return cls(metaAnalysis.expression, metaAnalysis.contraryExpression, metaAnalysis.studySetSize,
                   metaAnalysis.contraryStudySetSize, images=meanImages)

    def print_info(self):
        print [self.expression, self.studySetSize, self.contraryExpression, self.contraryStudySetSize]

    def write_images_to_file(self, outfile, delimiter='\t'):
        if self.images is None:
            raise RuntimeError('Images not initialized')
        writer = csv.writer(outfile, delimiter=delimiter)
        for imageName in self.images.keys():
            imageAsList = self.images[imageName].tolist()
            prefix = [self.expression, self.studySetSize, self.contraryExpression, self.contraryStudySetSize, imageName]
            print '?? ', prefix
            print '?! ', len(self.images[imageName])
            print '!! ', imageAsList[0]
            print '!? ', len(imageAsList)
            # writer.writerow(prefix + imageAsList)

    def save_images(self):
        if self.images is None:
            raise RuntimeError('Images not initialized')
        # TODO


def write_metaanalysisinfo_list_to_csv(metaAnalysisInfoList, outfilename):
    with open(outfilename, 'w') as outfile:
        for metaAnalysisInfo in metaAnalysisInfoList:
            metaAnalysisInfo.write_images_to_file(outfile)


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
    return Dataset.load(filePath)  # TODO


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
    metaAnalysis1Vs2 = meta.MetaAnalysis(dataset, studySet1, studySet2, prior=prior1)
    metaAnalysis2Vs1 = meta.MetaAnalysis(dataset, studySet2, studySet1, prior=prior2)

    return metaAnalysis1Vs2, metaAnalysis2Vs1


def get_mean_images(metaInfoLists):
    """

    :param metaInfoLists:
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
                meanImages[imgName] = np.mean([metaInfo.images[imgName] for metaInfo in metaInfos], axis=0)  # TODO test
            meanMetaInfoList.append(MetaAnalysisInfo.with_mean_images(metaInfos[0].metaAnalysis, meanImages))
    return meanMetaInfoList


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
    # algorithm adapted from stackoverflow.com/a/2680697
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


def compare_expressions(dataset, expressions, evenStudySetSize=True, numIterations=1, prior=None):
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
        if evenStudySetSize:
            studySets = even_study_set_size(studySets)

        # 3) get meta analysis results for each study set vs union of all other study sets
        studySetsToCompare = get_list_unions(studySets)
        metaInfoLists.append([])
        for i in range(len(studySets)):
            meta1VsOthers, metaOthersVs1 = compare_two_study_sets(dataset, studySets[i], studySetsToCompare[i], prior)
            metaInfo1VsOthers = MetaAnalysisInfo(expressions[i], len(studySets[i]),
                                                 '', len(studySetsToCompare[i]),  # TODO
                                                 metaAnalysis=meta1VsOthers)
            metaInfoOthersVs1 = MetaAnalysisInfo('', len(studySetsToCompare[i]),  # TODO
                                                 expressions[i], len(studySets[i]),
                                                 metaAnalysis=metaOthersVs1)
            metaInfoLists[i].append(metaInfo1VsOthers)
            metaInfoLists[i].append(metaInfoOthersVs1)
            if len(studySets) == 2:
                break  # no need to repeat if there are only 2 study sets to compare
    # 4) get average image
    meanMetaResult = get_mean_images(metaInfoLists)

    # TODO test

    # 5) save results
    write_metaanalysisinfo_list_to_csv(meanMetaResult, 'test.out')
    # imageutils.save_img(img, outpath, masker)


def compare_term_pairs(dataset, termList1, termList2, evenStudySetSize=True, numIterations=1, prior=None):
    expressions = []
    for term1 in termList1:
        expressions += get_expressions_one_to_one(term1, termList2)
    for exprTuple in expressions:
        compare_expressions(dataset, exprTuple, evenStudySetSize, numIterations, prior)
    # TODO


def compare_terms_group(dataset, termList, evenStudySetSize=True, numIterations=1, prior=None):
    expressions = []
    for term in termList:
        expressions.append(get_expression_one_to_all(term, termList))
    compare_expressions(dataset, expressions, evenStudySetSize, numIterations, prior)
    # TODO


if __name__ == '__main__':
    filePath = 'current_data/dataset.pkl'
    dataset = read_pkl_data(filePath, maskerPath=None)
    compare_term_pairs(dataset, ['emotion'], ['pain'], evenStudySetSize=False)

# Nomenclature for variables below: p = probability, F = feature present, g = given,
# U = unselected, A = activation. So, e.g., pAgF = p(A|F) = probability of activation
# in a voxel if we know that the feature is present in a study.
