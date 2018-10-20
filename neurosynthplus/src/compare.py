import random
from collections import OrderedDict
import neurosynth as ns
from .metaplus import MetaAnalysisPlus


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
            metaExt1VsOthers = MetaAnalysisPlus(info=create_info_dict(expressions[j], len(newStudySets[j]),
                                                                   otherExpression, len(studySetsToCompare[j])),
                                             meta_analysis=meta1VsOthers,
                                             filenamer_func=filenamer)
            metaExtLists[i].append(metaExt1VsOthers)
            if two_way:
                metaExtOthersVs1 = MetaAnalysisPlus(info=create_info_dict(otherExpression, len(studySetsToCompare[j]),
                                                                       expressions[j], len(newStudySets[j])),
                                                 meta_analysis=metaOthersVs1,
                                                 filenamer_func=filenamer)
                metaExtLists[i].append(metaExtOthersVs1)
            if len(newStudySets) == 2:  # no need to repeat if there are only 2 study sets to compare
                break
    # 4) get average image
    meanMetaResult = MetaAnalysisPlus.get_mean_images(metaExtLists)

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
            conjunction = MetaAnalysisPlus.get_conjunction_image(metaext_list=metaExts, lower_threshold=request[1],
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
            result = MetaAnalysisPlus.get_selectivity_image(metaext_list=metaExts, thresholds=request[1],
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

