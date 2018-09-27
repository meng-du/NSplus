from .metaplus import MetaAnalysisPlus
# import concurrent.futures  # requires futures for python 2.x


def analyze_expression(dataset, expression='', study_ids=(), prior=0.5, fdr=0.01,
                       image_names=None, save_csv=True, save_images=True):
    """
    Analyze a single expression; output a set of .nii.gz image files and/or
    a csv file containing voxel values in images.
    Either expression or study_ids has to be specified. If both are specified,
    they will be combined and analyzed together.

    :param dataset: a neurosynth Dataset instance to get studies from
    :param expression: a string expression to be analyzed
    :param study_ids: a list of study ids to be analyzed
    :param prior: a float priors to be used when calculating conditional probabilities
    :param fdr: the FDR threshold to use when correcting for multiple comparisons
    :param image_names: (list of strings) names of images to be included in the output files.
                        If None, all images will be included.
    :param save_csv: (boolean) whether results are saved as a csv file
    :param save_images: (boolean) whether results are saved as a csv file
    :return: an MetaAnalysisPlus object
    """
    if len(expression) == 0 and len(study_ids) == 0:
        raise ValueError('No expression specified for src')

    # get studies
    try:
        study_set = dataset.get_studies(expression=expression)
    except AttributeError:
        study_set = dataset.get_studies(features=expression)  # in case expression doesn't work
    study_set = list(set(study_set) | set(study_ids))
    if len(study_set) == 0:
        raise ValueError('No study found for the given expression')

    # analyze
    info = [('expr', expression), ('num_studies', len(study_set))]
    meta = MetaAnalysisPlus(info, dataset=dataset, ids=study_set, prior=prior, q=fdr)

    # output
    if save_csv:
        meta.write_images_to_csv(meta.info.name + '_output.csv', image_names=image_names)
    if save_images:
        meta.save_images()
    return meta

# def _analyze_expression(kwargs):
#     return analyze_expression(**kwargs)


def analyze_all_terms(dataset, extra_expr=(), prior=0.5, fdr=0.01):
    # TODO with extra lists of study IDs?
    """
    Do a meta src for each term/expression in either the dataset or the extra
    expression list
    :return: a list of MetaAnalysisPlus objects
    """
    all_exprs = [term for term in dataset.get_feature_names() if not term[0].isdigit()]
    if len(extra_expr) > 0:
        all_exprs += extra_expr
    all_exprs = set(all_exprs)

    # if multiprocess:  # multiprocessing is slower?
    #     with concurrent.futures.ProcessPoolExecutor() as executor:
    #         args = [dict(dataset=dataset, expression=expr, prior=prior, fdr=fdr,
    #                      save_csv=False, save_images=False) for expr in all_exprs]
    #         metas = executor.map(_analyze_expression, args)
    #     return list(metas)
    metas = []
    for i, expr in enumerate(all_exprs):
        print('Analyzing "%s" (%d/%d)' % (expr, i + 1, len(all_exprs)))
        metas.append(analyze_expression(dataset, expr, prior=prior, fdr=fdr,
                                        save_csv=False, save_images=False))
    return metas
