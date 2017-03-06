import neurosynth as ns
import random
import numpy as np
import csv
from collections import OrderedDict


class MetaExtension(object):
    def __init__(self, info=(), meta_analysis=None, images=None, filenamer_func=None, mask=None):
        # TODO remove meta_analysis
        """
        Create a MetaExtension instance
        :param info: an OrderedDict of information related to this meta analysis
        :param meta_analysis: a neurosynth MetaAnalysis object
        :param images: a dictionary of {image_name: image}, same as neurosynth.MetaAnalysis.images
        :param filenamer_func: a function that takes the info dictionary (i.e. the first parameter) and return a string
                               to be prefixed to image names when saving the images
        """
        self.info = info
        self.mask = meta_analysis.dataset.masker if meta_analysis is not None else mask
        self.images = images
        self.filenamer = filenamer_func
        if images is None and meta_analysis is not None:
            self.images = meta_analysis.images

    def get_filename(self):
        # TODO change func name to descriptor
        return '' if self.filenamer is None else self.filenamer(self.info)

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
            prefix = self.info.values()
            prefix.append(imageName)
            result.append(prefix + imageAsList)
        return result

    @classmethod
    def get_mean_images(cls, metaext_lists):
        # TODO test when length != 1
        """
        :param metaext_lists: a list of lists of MetaExtension to be averaged
        :return: a list of MetaExtension
        """
        if len(metaext_lists) == 1:
            mean_meta_ext_list = metaext_lists[0]
        else:
            mean_meta_ext_list = []
            # calculate means for each comparison across all iterations
            for metaExts in zip(*metaext_lists):  # iterating through columns
                # find intersection of image names
                allImgNames = [metaExt.images.keys() for metaExt in metaExts]
                imgNames = set(allImgNames[0]).intersection(*allImgNames)
                # calculate means
                meanImages = {}
                for imgName in imgNames:
                    meanImages[imgName] = np.mean([metaExt.images[imgName] for metaExt in metaExts], axis=0)
                mean_meta_ext_list.append(MetaExtension(info=metaExts[0].info, images=meanImages,
                                                        filenamer_func=metaExts[0].filenamer, mask=metaExts[0].mask))
        return mean_meta_ext_list

    @classmethod
    def get_conjunction_image(cls, metaext_list, threshold, image_name='pFgA_z', save_files=True, file_prefix=None):
        """
        From images with the specified name in the given list, create a new MetaExtension object with one image, where
        the value at a voxel is the number of images in which this voxel value passes (>=) the given threshold.
        MetaExtension objects must have the same mask.
        :param metaext_list: a list of MetaExtension objects
        :param threshold: a float number criterion for voxel values
        :param image_name: a string name of the image to create conjunction map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz file names
        :return: a MetaExtension object with the conjunction image
        """
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        conjunction = np.sum(sourceImgs > threshold, axis=0).astype(np.float64)
        analysis_names = [metaext.get_filename() for metaext in metaext_list]
        info = OrderedDict([('source_images', ', '.join(analysis_names))])
        result = cls(info, images={image_name: conjunction})
        if save_files:
            filename = file_prefix + '_' if file_prefix is not None else ''
            result.write_images_to_csv(filename + image_name + '>' + str(threshold) + '_conjunction.csv')
            result.save_images(metaext_list[0].mask, filename, '>' + str(threshold) + '_conjunction')
        return result

    def write_images_to_csv(self, filename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        data = np.array(self.get_images_as_list(image_names)).T
        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for row in data:
                writer.writerow(row)

    @classmethod
    def write_ext_list_to_csv(cls, metaext_list, outfilename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        results = [meta_ext.get_images_as_list(image_names) for meta_ext in metaext_list]
        results = np.concatenate(results).T  # concatenate and transpose
        with open(outfilename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for result in results:
                writer.writerow(result)

    def save_images(self, mask=None, file_prefix=None, file_postfix=''):
        # TODO create a new directory
        if self.images is None:
            raise RuntimeError('Images not initialized')
        for imageName in self.images.keys():
            filename = file_prefix if file_prefix is not None else self.get_filename()
            if len(filename) > 0 and filename[len(filename) - 1] != '_':
                filename += '_'
            filename += imageName + file_postfix + '.nii.gz'
            mask = mask if mask is not None else self.mask
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
    filename = get_shorthand_expression(info_dict['expr'])
    if 'contrary_expr' in info_dict:
        filename += '_vs_' + get_shorthand_expression(info_dict['contrary_expr'])
    return filename


def get_shorthand_expression(expression):
    word = expression.split(' ', 1)[0]
    if word[0] == '(':
        word = word[1:]
    if expression.startswith('(emotion &~ (emotional faces | emotional stimuli | * face | face* | *perception))'):
        word = 'emotion_experience'
    if expression.startswith('(emotion & (emotional faces | emotional stimuli | * face | face* | *perception))'):
        word = 'emotion_perception'
    if word == 'episodic':
        word = 'episodic' if 'autobiographical' in expression else 'episodic_without_autobio'
    # if (word == 'value') and (' choice' in expression):
    #     word = 'value_choice'
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
    :return: two neurosynth MetaAnalysis objects (studySet1 vs studySet2, studySet2 vs studySet1)
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
    if image_names is None:
        return
    for prior in priors:
        if ('pFgA_given_pF' in image_names) and (('pFgA_given_pF=%0.2f' % prior) not in image_names):
            image_names.append('pFgA_given_pF=%0.2f' % prior)
        if ('pAgF_given_pF' in image_names) and (('pAgF_given_pF=%0.2f' % prior) not in image_names):
            image_names.append('pAgF_given_pF=%0.2f' % prior)


def analyze_expression(dataset, expression, priors=(), dataset_size=None, image_names=None, save_files=True):
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
    :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
    :return: an MetaExtension object
    """
    # get studies
    studySet = dataset.get_studies(expression=expression)
    # add real prior
    if dataset_size is None:
        dataset_size = len(dataset.get_studies(expression='*'))  # 11405
    priors.append(1.0 * len(studySet) / dataset_size)
    process_image_names(image_names, priors)
    # analyze
    metaExt = None
    for prior in priors:
        meta = ns.meta.MetaAnalysis(dataset, studySet, prior=prior)
        if metaExt is None:
            metaExt = MetaExtension(info=create_info_dict(expression,  len(studySet)), meta_analysis=meta,
                                    filenamer_func=filenamer)
        else:
            for imgName in meta.images.keys():
                if imgName not in metaExt.images.keys():
                    metaExt.images[imgName] = meta.images[imgName]  # add new image
    # output
    if save_files:
        metaExt.write_images_to_csv(get_shorthand_expression(expression) + '_output.csv', image_names=image_names)
        metaExt.save_images(dataset.masker)
    return metaExt


def compare_expressions(dataset, expressions, evenStudySetSize=True, numIterations=1, prior=None, two_way=True,
                        image_names=None, save_files=True):
    """
    Compare each expression to all the other expressions in the given list and return MetaAnalysis objects
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expressions: a list of string expressions to be compared to one another
    :param evenStudySetSize: if true, the larger study set will be randomly sampled to the size of the smaller set
    :param numIterations: (int) when study set sizes are evened, iterate more than once to sample multiple times
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study; if None, the empirically estimated p(term) will be used
                  (calculated as number_of_studies_with_term  / total_number_of_studies)
    :param two_way: compare both expression1 vs expression2 and expression2 vs expression1 if true, otherwise only
                    compare expression1 vs expression2
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
    :param save_files: (boolean) save the results as .csv and .nii.gz files
    :return: a list of MetaExtension objects
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

    metaExtLists = []  # stores lists of MetaExtension (one list per iteration)
    for i in range(numIterations):
        # 2) reduce sizes
        newStudySets = even_study_set_size(studySets) if evenStudySetSize else studySets

        # 3) get meta analysis results for each study set vs union of all other study sets
        studySetsToCompare = get_list_unions(newStudySets)
        metaExtLists.append([])
        for j in range(len(newStudySets)):
            meta1VsOthers, metaOthersVs1 = compare_two_study_sets(dataset, newStudySets[j], studySetsToCompare[j],
                                                                  prior, image_names)
            if len(newStudySets) == 2:
                otherExpression = expressions[1 - j]
            else:
                otherExpression = 'union of "' + '", "'.join(expressions[:j] + expressions[(j + 1):]) + '"'
            metaExt1VsOthers = MetaExtension(info=create_info_dict(expressions[j], len(newStudySets[j]),
                                                                   otherExpression, len(studySetsToCompare[j])),
                                             meta_analysis=meta1VsOthers,
                                             filenamer_func=filenamer)
            metaExtLists[i].append(metaExt1VsOthers)
            if two_way:
                metaExtOthersVs1 = MetaExtension(info=create_info_dict(otherExpression, len(studySetsToCompare[j]),
                                                                       expressions[j], len(newStudySets[j])),
                                                 meta_analysis=metaOthersVs1,
                                                 filenamer_func=filenamer)
                metaExtLists[i].append(metaExtOthersVs1)
            if len(newStudySets) == 2:  # no need to repeat if there are only 2 study sets to compare
                break
    # 4) get average image
    meanMetaResult = MetaExtension.get_mean_images(metaExtLists)

    # 5) save results
    if save_files is True:
        if len(expressions) == 2:
            filename = filenamer(meanMetaResult[0].info)
        else:
            filename = 'group'
        MetaExtension.write_ext_list_to_csv(meanMetaResult, filename + '_output.csv', image_names=image_names)
        for metaExt in meanMetaResult:
            metaExt.save_images(dataset.masker)
    return meanMetaResult


def compare_term_pairs(dataset, termList1, termList2, evenStudySetSize=True, numIterations=100, prior=None,
                       image_names=None, save_files=True):
    """
    :return: a list of lists of MetaExtensions, e.g. [[term1A vs term2A, term1A vs term2B]]
    """
    expressions = [get_expressions_one_to_one(term1, termList2) for term1 in termList1]
    results = []
    for i, exprGroup in enumerate(expressions):
        results.append([])
        for exprTuple in exprGroup:
            print exprTuple
            result = compare_expressions(dataset, exprTuple, evenStudySetSize, numIterations, prior, False,
                                         image_names, save_files)  # should be a list of length 1
            results[i].append(result[0])
    return results


def compare_term_pairs_with_conjunction_map(dataset, termList1, termList2, conjunction_images, evenStudySetSize=True,
                                            numIterations=100, prior=None, image_names=None, save_files=True):
    """
    Create conjunction maps for term1A (from list 1) vs term2A/term2B/term2C/... (from list 2), term1B vs term2A/term2B/
    term2C/..., etc.
    :param conjunction_images: a list of tuples [(image_name_1, threshold_1), (image_name_2, threshold_2), ...]
    """
    results = compare_term_pairs(dataset, termList1, termList2, evenStudySetSize, numIterations, prior, image_names,
                                 save_files)
    conjunctions = []
    for metaExts in results:
        prefix = get_shorthand_expression(metaExts[0].info['expr'])
        for image in conjunction_images:
            conjunction = MetaExtension.get_conjunction_image(metaExts, threshold=image[1], image_name=image[0],
                                                              file_prefix=prefix, save_files=save_files)
            conjunctions.append(conjunction)
    return conjunctions


def compare_term_group(dataset, termList, evenStudySetSize=True, numIterations=1, prior=None, image_names=None,
                       save_files=True):
    expressions = []
    for term in termList:
        expressions.append(get_expression_one_to_all(term, termList))
    return compare_expressions(dataset, expressions, evenStudySetSize, numIterations, prior, image_names, save_files)
