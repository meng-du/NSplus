import neurosynth as ns
import random
import numpy as np
import csv
from collections import OrderedDict


class MetaExtension(object):
    def __init__(self, info=(), metaAnalysis=None, images=None, filenamer_func=None):
        """
        Create a MetaExtension instance
        :param info: an OrderedDict of information related to this meta analysis
        :param metaAnalysis: a neurosynth MetaAnalysis object
        :param images: a dictionary of {image_name: image}, same as neurosynth.MetaAnalysis.images
        :param filenamer_func: a function that takes the info dictionary (i.e. the first parameter) and return a string
                               to be prefixed to image names when saving the images
        """
        self.info = info
        self.metaAnalysis = metaAnalysis  # TODO not very useful?
        self.images = images
        self.filenamer = filenamer_func
        if images is None and metaAnalysis is not None:
            self.images = self.metaAnalysis.images

    def get_images_as_list(self, image_names=None):
        """
        Get a list of images prefixed with information
        :param image_names: the names of images to be included in the result. If None, all images will be returned.
        :return: a list of images (a list of lists of strings)
        """
        if self.images is None:
            raise RuntimeError('Images not initialized')
        result = []
        # Note: the length of image arrays here exceeds the maximum number of columns in MS Excel
        for imageName in self.images.keys():
            if (image_names is not None) and (imageName not in image_names):
                continue
            imageAsList = self.images[imageName].tolist()
            prefix = [self.info.values()] + imageName
            result.append(prefix + imageAsList)
        return result

    @classmethod
    def get_mean_images(cls, metaInfoLists):
        """
        :param metaInfoLists: a list of lists of MetaExtension to be averaged
        :return: a list of MetaExtension
        """
        if len(metaInfoLists) == 1:
            meanMetaInfoList = metaInfoLists[0]
        else:
            meanMetaInfoList = []
            # calculate means for each comparison across all iterations
            for metaInfos in zip(*metaInfoLists):  # iterating through columns
                # find intersection of image names
                allImgNames = [metaInfo.metaAnalysis.images.keys() for metaInfo in metaInfos]
                imgNames = set(allImgNames[0]).intersection(*allImgNames)
                # calculate means
                meanImages = {}
                for imgName in imgNames:
                    meanImages[imgName] = np.mean([metaInfo.images[imgName] for metaInfo in metaInfos], axis=0)
                meanMetaInfoList.append(metaInfos[0].init_with_mean_images(meanImages))
        return meanMetaInfoList

    def write_images_to_csv(self, filename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        data = np.array(self.get_images_as_list(image_names)).T
        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for row in data:
                writer.writerow(row)

    @classmethod
    def write_info_list_to_csv(cls, metaAnalysisInfoList, outfilename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        results = [metaAnalysisInfo.get_images_as_list(image_names) for metaAnalysisInfo in metaAnalysisInfoList]
        results = np.concatenate(results).T  # concatenate and transpose
        with open(outfilename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for result in results:
                writer.writerow(result)

    def save_images(self, mask):
        if self.images is None:
            raise RuntimeError('Images not initialized')
        for imageName in self.images.keys():
            filename = self.filenamer(self.info) + '_' if self.filenamer is not None else ''
            filename += imageName + '.nii.gz'
            ns.imageutils.save_img(self.images[imageName], filename=filename, masker=mask)


def create_info_dict(expression, num_studies, contrary_expr=None, contrary_num_studies=None):
    """
    Goes together with the filenamer below
    """
    if contrary_expr is None:
        return OrderedDict([('expr', expression),
                            ('num_studies', num_studies)])
    return OrderedDict([('expr', expression),
                        ('num_studies', num_studies),
                        ('contrary_expr', contrary_expr),
                        ('contrary_num_studies', contrary_num_studies)])


def filenamer(info_dict):
    """
    Goes together with the info_dict above
    """
    filename = get_first_word_in_expression(info_dict['expr'])
    if 'contrary_expr' in info_dict:
        filename += '_vs_' + get_first_word_in_expression(info_dict['contrary_expr'])
    return filename


def get_first_word_in_expression(expression):
    word = expression.split(' ', 1)[0]
    if word[0] == '(':
        word = word[1:]
    if word == 'episodic':
        word = 'episodic_with_autobio' if 'autobiographical' in expression else 'episodic_without_autobio'
    if (word == 'value') and (' choice' in expression):
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


def compare_two_study_sets(dataset, studySet1, studySet2, prior=None, image_names=None):
    """
    :param dataset: a neurosynth Dataset instance
    :param studySet1, studySet2: two lists of study ids to compare
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study; if None, the empirically estimated p(term) will be used
                  (calculated as number_of_studies_with_term  / total_number_of_studies)
    :param image_names:
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
    if image_names is not None:
        process_image_names(image_names, [prior1, prior2])

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


def process_image_names(image_names, priors):
    for prior in priors:
        if ('pFgA_given_pF' in image_names) and (('pFgA_given_pF=%0.2f' % prior) not in image_names):
            image_names.append('pFgA_given_pF=%0.2f' % prior)
        if ('pAgF_given_pF' in image_names) and (('pAgF_given_pF=%0.2f' % prior) not in image_names):
            image_names.append('pAgF_given_pF=%0.2f' % prior)


def analyze_expression(dataset, expression, priors=(), dataset_size=None, image_names=None):
    # TODO doesn't need dataset_size. should be able to get length of database quickly?
    # TODO don't always add real prior?
    # TODO parameter += customized study ids, as an alternative to dataset.get_studies
    """
    Analyze a single expression, output a set of .nii.gz image files and a csv file containing voxel values in images
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expression: a string expression to be analyzed
    :param priors: a list of float priors to be used when calculating conditional probabilities
                   The real prior will always be calculated and added to this list
    :param dataset_size: number of studies in the dataset. This is used to calculate the real prior.
                         If not specified, the number will be counted, which takes more time.
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
    """
    # get studies
    studySet = dataset.get_studies(expression=expression)
    # add real prior
    if dataset_size is None:
        dataset_size = len(dataset.get_studies(expression='*'))  # 11405
    priors.append(1.0 * len(studySet) / dataset_size)
    process_image_names(image_names, priors)
    # analyze
    metaInfo = None
    for prior in priors:
        meta = ns.meta.MetaAnalysis(dataset, studySet, prior=prior)
        if metaInfo is None:
            metaInfo = MetaExtension(info=create_info_dict(expression,  len(studySet)), metaAnalysis=meta)
        else:
            for imgName in meta.images.keys():
                if imgName not in metaInfo.images.keys():
                    metaInfo.images[imgName] = meta.images[imgName]  # add new image
    # output
    metaInfo.write_images_to_csv(get_first_word_in_expression(expression) + '_output.csv', image_names=image_names)
    metaInfo.save_images(dataset.masker)


def compare_expressions(dataset, expressions, evenStudySetSize=True, numIterations=1, prior=None, image_names=None):
    """
    Compare each expression to all the other expressions in the given list and return MetaAnalysis objects
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expressions: a list of string expressions to be compared to one another
    :param evenStudySetSize: if true, the larger study set will be randomly sampled to the size of the smaller set
    :param numIterations: (int) when study set sizes are evened, iterate more than once to sample multiple times
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study; if None, the empirically estimated p(term) will be used
                  (calculated as number_of_studies_with_term  / total_number_of_studies)
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
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
        studies = dataset.get_studies(expression=expression)
        if len(studies) == 0:
            print 'No data associated with "' + expression + '"'
            return
        studySets.append(studies)

    metaInfoLists = []  # stores lists of MetaExtension (one list per iteration)
    for i in range(numIterations):
        # 2) reduce sizes
        newStudySets = even_study_set_size(studySets) if evenStudySetSize else studySets

        # 3) get meta analysis results for each study set vs union of all other study sets
        studySetsToCompare = get_list_unions(newStudySets)
        metaInfoLists.append([])
        for j in range(len(newStudySets)):
            meta1VsOthers, metaOthersVs1 = compare_two_study_sets(dataset, newStudySets[j], studySetsToCompare[j],
                                                                  prior, image_names)
            if len(newStudySets) == 2:
                otherExpression = expressions[1 - j]
            else:
                otherExpression = 'union of "' + '", "'.join(expressions[:j] + expressions[(j + 1):]) + '"'
            metaInfo1VsOthers = MetaExtension(info=create_info_dict(expressions[j], len(newStudySets[j]),
                                                                    otherExpression, len(studySetsToCompare[j])),
                                              metaAnalysis=meta1VsOthers)
            metaInfoOthersVs1 = MetaExtension(info=create_info_dict(otherExpression, len(studySetsToCompare[j]),
                                                                    expressions[j], len(newStudySets[j])),
                                              metaAnalysis=metaOthersVs1)
            metaInfoLists[i].append(metaInfo1VsOthers)
            metaInfoLists[i].append(metaInfoOthersVs1)
            if len(newStudySets) == 2:  # no need to repeat if there are only 2 study sets to compare
                break
    # 4) get average image
    meanMetaResult = MetaExtension.get_mean_images(metaInfoLists)

    # 5) save results
    if len(expressions) == 2:
        filename = get_first_word_in_expression(expressions[0]) + '_vs_' + get_first_word_in_expression(expressions[1])
    else:
        filename = 'group'
    MetaExtension.write_info_list_to_csv(meanMetaResult, filename + '_output.csv', image_names=image_names)
    for metaInfo in meanMetaResult:
        metaInfo.save_images(dataset.masker)


def compare_term_pairs(dataset, termList1, termList2, evenStudySetSize=True, numIterations=1, prior=None,
                       image_names=None):
    expressions = []
    for term1 in termList1:
        expressions += get_expressions_one_to_one(term1, termList2)
    for exprTuple in expressions:
        print exprTuple
        compare_expressions(dataset, exprTuple, evenStudySetSize, numIterations, prior, image_names)


def compare_terms_group(dataset, termList, evenStudySetSize=True, numIterations=1, prior=None, image_names=None):
    expressions = []
    for term in termList:
        expressions.append(get_expression_one_to_all(term, termList))
    compare_expressions(dataset, expressions, evenStudySetSize, numIterations, prior, image_names)
