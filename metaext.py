import neurosynth as ns
import random
import numpy as np
import csv
from collections import OrderedDict
from scipy.stats import rankdata


class MetaExtension(object):
    # TODO inherit meta?
    def __init__(self, info=(), meta_analysis=None, images=None, name='', filenamer_func=None, mask=None):
        # TODO assign a name to each MetaExtension rather than using a function
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
        self.name = name
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
    def _save_computed_image(cls, metaext_list, computed_img, comparison_name, computation_type, save_files, image_name,
                             image_info=None, file_prefix=None):
        """
        :param image_info: an extra string containing information regarding the computed image.
        """
        # TODO change image_info to a dict?
        analysis_names = [(metaext.name if len(metaext.name) > 0 else metaext.get_filename())
                          for metaext in metaext_list]
        if image_info is None:
            info = OrderedDict([('source_images', ', '.join(analysis_names))])
        else:
            info = OrderedDict([('source_images', ', '.join(analysis_names)), ('info', image_info)])
        prefix = file_prefix + '_' if (file_prefix is not None) and len(file_prefix) > 0 else ''
        csv_name = prefix + image_name + comparison_name + '_' + computation_type
        result = cls(info, images={image_name: computed_img}, name=csv_name, mask=metaext_list[0].mask)
        if save_files:
            result.write_images_to_csv(csv_name + '.csv')  # TODO path
            result.save_images(metaext_list[0].mask, prefix, comparison_name + '_' + computation_type)
        return result

    @classmethod
    def get_selectivity_image(cls, metaext_list, thresholds, image_name='pFgA_z', save_files=True, file_prefix=None):
        """
        Given a list of pairwise comparison results featuring one expression, compute a new MetaExtension object with
        one image, where the integer values at a voxel means the level of superiority the featured expression has over
        the compared expressions. For example, given the comparisons (expr0_vs_expr1, expr0_vs_expr2, expr0_vs_expr3),
        and thresholds (0.50, 0.60), a voxel would have 0 if its value < 0.50 in any of the three comparisons; or 1 if
        its value > 0.50 in all of the three comparisons, but < 0.60 in any of them; or 2 if its value > 0.60 in all of
        the three comparisons.
        The maximum value at a voxel in the result image equals the length of the thresholds list.
        :param metaext_list: a list of MetaExtension objects resulted from a pairwise comparison
        :param thresholds: (a list of floats) points that define different levels of superiority
        :param image_name: a string name of the image to create the selectivity map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the selectivity image
        """
        if thresholds is None or len(thresholds) == 0:
            raise ValueError('No threshold specified')
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        selectivity = np.zeros(sourceImgs.shape[1]).astype(np.float64)  # empty array of same length as the source image
        for threshold in thresholds:
            selectivity += np.all(sourceImgs > threshold, axis=0).astype(np.float64)

        info = str(thresholds)[1:-1]
        return cls._save_computed_image(metaext_list, selectivity, '', 'selectivity', save_files, image_name, info,
                                        file_prefix)

    @classmethod
    def get_max_image(cls, metaext_list, image_name='pFgA_z', save_files=True, file_prefix=None):
        """
        Given a MetaExtension list, compute a new MetaExtension object with one image, where the value at each voxel is
        the maximum value at that voxel in the given list
        """
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        maximum = np.amax(sourceImgs, axis=0)
        return cls._save_computed_image(metaext_list, maximum, '', 'maximum', save_files, image_name, None, file_prefix)

    @classmethod
    def _get_conjunction_array(cls, metaext_list, lower_threshold=None, upper_threshold=None, image_name='pFgA_z'):
        """
        Helper function
        :return: the conjunction image as an nd array, and a string describing the conjunction criterion
        """
        if lower_threshold is None and upper_threshold is None:
            raise ValueError('No threshold specified')
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        if upper_threshold is None:
            conjunction = np.sum(sourceImgs > lower_threshold, axis=0).astype(np.float64)
            comparison_name = '>' + str(lower_threshold)
        elif lower_threshold is None:
            conjunction = np.sum(sourceImgs < upper_threshold, axis=0).astype(np.float64)
            comparison_name = '<' + str(upper_threshold)
        else:
            if lower_threshold < upper_threshold:
                conjunction = np.sum((sourceImgs > lower_threshold) & (sourceImgs < upper_threshold), axis=0) \
                              .astype(np.float64)
                comparison_name = str(lower_threshold) + '-' + str(upper_threshold)
            elif lower_threshold > upper_threshold:
                conjunction = np.sum((lower_threshold < sourceImgs or sourceImgs < upper_threshold), axis=0) \
                              .astype(np.float64)
                comparison_name = '>' + str(lower_threshold) + 'or' + '<' + str(upper_threshold)
            else:
                raise ValueError('Lower and upper thresholds must be different values')

        return conjunction, comparison_name

    @classmethod
    def get_conjunction_image(cls, metaext_list, lower_threshold=None, upper_threshold=None, image_name='pFgA_z',
                              save_files=True, file_prefix=None):  # TODO change file_prefix to a info dict?
        """
        From images with the specified image_name in the given list, compute a new MetaExtension object with one image,
        where the value at a voxel is the number of images in which this voxel value passes the given threshold
        criterion.
        If both lower_threshold and upper_threshold are specified, and lower_threshold > upper_threshold, the voxels
        that are EITHER greater than the lower_threshold OR less the upper_threshold will be counted; otherwise if
        lower_threshold < upper_threshold, the voxels that are BOTH greater than the lower_threshold AND less the
        upper_threshold will be counted.
        MetaExtension objects must have the same mask.
        :param metaext_list: a list of MetaExtension objects
        :param upper_threshold: a float value criterion for voxels
        :param lower_threshold: a float value criterion for voxels
        :param image_name: a string name of the image to create the conjunction map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the conjunction image
        """
        conjunction, comparison_name = cls._get_conjunction_array(metaext_list, lower_threshold, upper_threshold,
                                                                  image_name)
        return \
            cls._save_computed_image(metaext_list, conjunction, comparison_name, 'conjunction', save_files, image_name,
                                     file_prefix=file_prefix)

    @classmethod
    def get_conjunction_image_with_separate_criteria(cls, metaext_list, thresholds, binary=False, image_name='pFgA_z',
                                                     save_files=True, file_prefix=None):
        """
        From images with the specified image_name in the given list, create a new MetaExtension object with one image,
        where the value at a voxel is the number of images in which this voxel value passes the given threshold criterion.
        If both lower_threshold and upper_threshold are specified, and lower_threshold > upper_threshold, the voxels
        that are EITHER greater than the lower_threshold OR less the upper_threshold will be counted; otherwise if
        lower_threshold < upper_threshold, the voxels that are BOTH greater than the lower_threshold AND less the
        upper_threshold will be counted.
        MetaExtension objects must have the same mask.
        :param metaext_list: a list of MetaExtension objects
        :param thresholds: a list of tuples [(lower_threshold_1, upper_threshold_1), (lower_threshold_2,
                           upper_threshold_2), ...]. Its length should be the same as metaext_list
        :param binary: if True, any voxel with value == number_of_images will be substituted with a 1, and other voxel
                       values will be substituted with 0s
        :param image_name: a string name of the image to create the conjunction map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the conjunction image
        """
        individual_conjs = []
        info = ''
        for metaext, threshold in zip(metaext_list, thresholds):
            individual_conj, comparison_name = cls._get_conjunction_array([metaext], threshold[0], threshold[1],
                                                                          image_name)
            individual_conjs.append(individual_conj)
            info += comparison_name + ', '
        info = info[:-2]
        conjunction = np.sum(individual_conjs, axis=0)
        if binary:
            conjunction = (conjunction == len(individual_conjs)).astype(np.float64)
        return cls._save_computed_image(metaext_list, conjunction, '', 'conjunction', save_files, image_name, info,
                                        file_prefix)

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
            if len(file_postfix) > 0 and file_postfix[0] != '_':
                file_postfix = '_' + file_postfix
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
    # TODO assign a name to each MetaExtension rather than a function
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
    # if word == 'episodic':
    #     word = 'episodic' if 'autobiographical' in expression else 'episodic_without_autobio'
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


def process_image_names(image_names, prior, fdr):
    """
    Just appending priors to 'pFgA_given_pF', and fdr to 'pFgA_z_FDR'
    """
    if image_names is None:
        return
    # prior
    if ('pFgA_given_pF' in image_names) and (('pFgA_given_pF=%0.2f' % prior) not in image_names):
        image_names.append('pFgA_given_pF=%0.2f' % prior)
    if ('pAgF_given_pF' in image_names) and (('pAgF_given_pF=%0.2f' % prior) not in image_names):
        image_names.append('pAgF_given_pF=%0.2f' % prior)
    # fdr
    if ('pFgA_z_FDR' in image_names) and (('pFgA_z_FDR_%s' % fdr) not in image_names):
        image_names.append('pFgA_z_FDR_%s' % fdr)
    if ('pAgF_z_FDR' in image_names) and (('pAgF_z_FDR_%s' % fdr) not in image_names):
        image_names.append('pAgF_z_FDR_%s' % fdr)


def analyze_expression(dataset, expression, prior=0.5, fdr=0.01, image_names=None, save_files=True):
    # TODO mask
    # TODO parameter += customized study ids, as an alternative to dataset.get_studies
    """
    Analyze a single expression, output a set of .nii.gz image files and a csv file containing voxel values in images
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expression: a string expression to be analyzed
    :param priors: a list of float priors to be used when calculating conditional probabilities
                   The real prior will always be calculated and added to this list
    :param fdr: the FDR threshold to use when correcting for multiple comparisons
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
    :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
    :return: an MetaExtension object
    """
    # get studies
    print expression
    try:
        studySet = dataset.get_studies(expression=expression)
    except AttributeError:
        studySet = dataset.get_studies(features=expression)  # in case expression doesn't work

    process_image_names(image_names, prior, fdr)
    # analyze
    meta = ns.meta.MetaAnalysis(dataset, studySet, prior=prior, q=fdr)
    metaExt = MetaExtension(info=create_info_dict(expression, len(studySet)), meta_analysis=meta,
                            filenamer_func=filenamer)
    # output
    if save_files:
        metaExt.write_images_to_csv(get_shorthand_expression(expression) + '_output.csv', image_names=image_names)
        metaExt.save_images(dataset.masker)
    return metaExt


def compare_expressions(dataset, expressions, evenStudySetSize=True, numIterations=1, prior=0.5, fdr=0.01,
                        two_way=True, image_names=None, save_files=True):
    # TODO mask
    """
    Compare each expression to all the other expressions in the given list and return MetaAnalysis objects
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expressions: a list of string expressions to be compared to one another
    :param evenStudySetSize: if true, the larger study set will be randomly sampled to the size of the smaller set
    :param numIterations: (int) when study set sizes are evened, iterate more than once to sample multiple times
    :param prior: (float) the prior to use when calculating conditional probabilities, i.e., the prior probability of
                  a term being used in a study
    :param fdr: the FDR threshold to use when correcting for multiple comparisons
    :param two_way: compare both expression1 vs expression2 and expression2 vs expression1 if true, otherwise only
                    compare expression1 vs expression2
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx' or 'pFgA_z_FDR=0.xx', specifying 'pFgA_given_pF' or
                        'pFgA_z_FDR' will include all of them.
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
        try:
            studies = dataset.get_studies(expression=expression)
        except AttributeError:
            studies = dataset.get_studies(features=expression)  # in case expression doesn't work
        if len(studies) == 0:
            print 'No data associated with "' + expression + '"'
            return
        studySets.append(studies)

    process_image_names(image_names, prior, fdr)
    metaExtLists = []  # stores lists of MetaExtension (one list per iteration)
    for i in range(numIterations):
        # 2) reduce sizes
        newStudySets = even_study_set_size(studySets) if evenStudySetSize else studySets

        # 3) get meta analysis results for each study set vs union of all other study sets
        studySetsToCompare = get_list_unions(newStudySets)
        metaExtLists.append([])
        for j in range(len(newStudySets)):
            # neurosynth meta analysis
            meta1VsOthers = ns.meta.MetaAnalysis(dataset, newStudySets[j], studySetsToCompare[j], prior=prior, q=fdr)
            metaOthersVs1 = ns.meta.MetaAnalysis(dataset, studySetsToCompare[j], newStudySets[j], prior=prior, q=fdr)

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


def compare_term_pairs(dataset, termList1, termList2, evenStudySetSize=True, numIterations=500, prior=0.5, fdr=0.01,
                       image_names=None, save_files=True):
    # TODO combine with the next two / feed results from this to next two rather than calling this func from there?
    """
    :return: a list of lists of MetaExtensions, e.g. [[term1A vs term2A, term1A vs term2B]]
    """
    expressions = [get_expressions_one_to_one(term1, termList2) for term1 in termList1]
    results = []
    for i, exprGroup in enumerate(expressions):
        results.append([])
        for exprTuple in exprGroup:
            print exprTuple
            result = compare_expressions(dataset, exprTuple, evenStudySetSize, numIterations, prior, fdr, False,
                                         image_names, save_files)  # should be a list of length 1
            results[i].append(result[0])
    return results


def compare_term_pairs_with_conjunction_map(dataset, termList1, termList2, conjunctions, evenStudySetSize=True,
                                            numIterations=500, prior=0.5, fdr=0.01, image_names=None, save_files=True):
    """
    Create conjunction maps for term1A (from list 1) vs term2A/term2B/term2C/... (from list 2), term1B vs term2A/term2B/
    term2C/..., etc.
    :param conjunctions: a list of tuples [(image_name_1, lower_threshold_1, upper_threshold_1),
                                           (image_name_2, lower_threshold_2, upper_threshold_2),
                                           ...]
    """
    results = compare_term_pairs(dataset, termList1, termList2, evenStudySetSize, numIterations, prior, fdr,
                                 image_names, save_files)  # TODO separate this save_files and the one below
    conj_results = []
    for metaExts in results:
        prefix = get_shorthand_expression(metaExts[0].info['expr'])
        for request in conjunctions:
            conjunction = MetaExtension.get_conjunction_image(metaext_list=metaExts, lower_threshold=request[1],
                                                              upper_threshold=request[2], image_name=request[0],
                                                              save_files=save_files, file_prefix=prefix)
            conj_results.append(conjunction)
    return conj_results


def compare_term_pairs_with_selectivity_map(dataset, termList1, termList2, selectivity, evenStudySetSize=True,
                                            numIterations=500, prior=0.5, image_names=None, save_files=True):
    """
    Create selectivity maps for term1A (from list 1) vs term2A/term2B/term2C/... (from list 2),
                                term1B vs term2A/term2B/term2C/..., etc.
    :param selectivity: a list of tuples [(image_name_1, (threshold_1_a, threshold_1_b, ...)),
                                          (image_name_2, (threshold_2_a, threshold_2_b, ...)),
                                          ...]
    :return [selectivity_map for s in selectivity]
    """
    # TODO the above comment...
    results = compare_term_pairs(dataset, termList1, termList2, evenStudySetSize, numIterations, prior, image_names,
                                 save_files)
    select_results = [[] for i in range(len(selectivity))]
    for metaExts in results:
        prefix = get_shorthand_expression(metaExts[0].info['expr'])
        for i, request in enumerate(selectivity):
            result = MetaExtension.get_selectivity_image(metaext_list=metaExts, thresholds=request[1],
                                                         image_name=request[0], save_files=save_files,
                                                         file_prefix=prefix)
            select_results[i].append(result)
    return select_results


def compare_term_group(dataset, termList, evenStudySetSize=True, numIterations=1, prior=0.5, image_names=None,
                       save_files=True):
    expressions = []
    for term in termList:
        expressions.append(get_expression_one_to_all(term, termList))
    return compare_expressions(dataset, expressions, evenStudySetSize, numIterations, prior, image_names, save_files)


def analyze_all_terms(dataset, extra_expr=()):
    """
    Generate a MetaExtension object for each term/expression in the dataset and the given extra expression list
    :return: a tuple (a list of MetaExtensions, a list of sorted image names)
    """
    metaexts = [analyze_expression(dataset, term, priors=[0.5], save_files=False)
                for term in dataset.get_feature_names() if not term[0].isdigit()]
    for extra in extra_expr:
        metaexts.append(analyze_expression(dataset, extra, priors=[0.5], save_files=False))

    img_names = metaexts[0].images.keys()
    img_names.sort()
    return metaexts, img_names


def get_image_means(metaexts, img_names, mask=None):
    """
    Get a mean for all of the voxel values in each image
    """
    if mask is not None:
        return [np.mean([np.array(metaext.images[img])[mask] for img in img_names], axis=1) for metaext in metaexts]
    else:
        return [np.mean([metaext.images[img] for img in img_names], axis=1) for metaext in metaexts]


def _sort_and_save(metaexts, means, img_names, rank_by='pFgA_given_pF=0.50', descending=True, csv_file=None):
    """
    :return: a numpy array of ordered terms and corresponding average voxel values
             ([term1, term2, ...],
              [avg_image_A_1, avg_image_A_2, ...],
              [avg_image_B_1, avg_image_B_2, ...], ...)
    """
    term_list = [metaext.info['expr'] for metaext in metaexts]
    matrix_as_list = [tuple([term_list[i]] + [mean for mean in means[i]]) for i in range(len(term_list))]
    matrix = np.array(matrix_as_list, dtype=[('term', '|S64')] + [(img, 'float64') for img in img_names])
    matrix.sort(order=rank_by, axis=0)
    if descending:
        matrix = matrix[::-1]
    # save/return results
    if csv_file:
        with open(csv_file, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerow(matrix.dtype.names)  # header
            # content
            for row in matrix:
                writer.writerow(row)
    return matrix


def rank_avg_voxel(dataset, rank_by='pFgA_given_pF=0.50', extra_expr=(), descending=True, csv_file=None, mask=None):
    # TODO use neurosynth mask?
    """
    Rank all terms in the dataset by the average voxel value in a given image
    :param dataset: a neurosynth Dataset instance
    :param rank_by: a string image name to get an average value from
    :param extra_expr: a list of string extra expressions
    :param descending: (boolean) if True, voxels with larger values will appear at the top
    :param csv_file: a string file name, or None if not save as a file
    :param mask: an numpy array of booleans, which has the same length as the images in the dataset
    """
    metaexts, img_names = analyze_all_terms(dataset, extra_expr)
    # make a result matrix
    img_means = get_image_means(metaexts, img_names, mask)
    return _sort_and_save(metaexts, img_means, img_names, rank_by, descending, csv_file)


def _rankdata_helper(imgs, voxel, descending, ties):
    if descending:
        if ties == 'max':
            ties = 'min'
        if ties == 'min':
            ties = 'max'
        return imgs.shape[0] + 1 - rankdata(imgs[:, voxel], method=ties)
    # ascending
    return rankdata(imgs[:, voxel], method=ties)


def rank_avg_rank(dataset, rank_by='pFgA_given_pF=0.50', extra_expr=(), descending=True, ties='average', csv_file=None,
                  mask=None):
    # TODO use neurosynth mask?
    """
    For the specified image (rank_by), get a rank order for the values in each voxel, and then average the ranks
    across all voxels
    :param descending: (boolean) if True, voxels with larger values will have smaller ranks
    :param ties: (string) the method used to assign ranks to tied elements. The options are 'average', 'min', 'max',
                 'dense' and 'ordinal'. See scipy.stats.rankdata for details.
    """
    metaexts, img_names = analyze_all_terms(dataset, extra_expr)
    img_means = get_image_means(metaexts, img_names)
    if mask is not None:
        imgs = np.array([np.array(metaext.images[rank_by])[mask] for metaext in metaexts])
    else:
        imgs = np.array([np.array(metaext.images[rank_by]) for metaext in metaexts])
    rank_means = np.array([np.mean([_rankdata_helper(imgs, voxel, descending, ties) for voxel in range(len(imgs[0]))],
                                   axis=0)]).T
    img_names = [rank_by + '_rank'] + img_names
    return _sort_and_save(metaexts, np.hstack((rank_means, img_means)), img_names, rank_by + '_rank', False, csv_file)
