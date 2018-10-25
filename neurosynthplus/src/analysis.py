from .metaplus import MetaAnalysisPlus
import os
# import concurrent.futures  # requires futures for python 2.x


def analyze_expression(dataset, expression='', study_ids=(), prior=0.5, fdr=0.01,
                       extra_info=(), image_names=None, save_files=True, outdir='.'):
    """
    Analyze a single expression; optionally output the nifti images and a csv file
    containing image info and voxel values.
    At least one of expression or study_ids has to be specified. If both are specified,
    they will be combined and analyzed together.

    :param dataset: a Neurosynth Dataset or DatasetPlus instance to get studies from
    :param expression: a string expression to be analyzed
    :param study_ids: a list of study ids to be analyzed
    :param extra_info: (list of (key, value) pairs) extra information to be included in the
                       csv output file
    :param prior: (float) prior to be used when calculating conditional probabilities
    :param fdr: (float) the FDR threshold to use when correcting for multiple comparisons
    :param image_names: (list of strings) names of images to be included in the output files.
                        If None, all images will be included.
    :param save_files: (boolean) whether to save the results as csv and nifti files
    :param outdir: (string) directory to save the images/csv
    :return: an MetaAnalysisPlus object
    """
    if len(expression) == 0 and len(study_ids) == 0:
        raise ValueError('Nothing specified for analysis')
    if prior is not None and (prior <= 0 or prior >= 1):
        raise ValueError('prior has to be greater than 0 and less than 1')
    if not os.path.isdir(outdir):
        raise IOError('Invalid output directory')

    # get studies
    study_set = dataset.get_studies(expression=expression)
    study_set = list(set(study_set) | set(study_ids))
    if len(study_set) == 0:
        raise ValueError('No study in the database is associated with "'
                         + expression + '"')

    # analyze
    info = [('expression', expression),
            ('number of studies', len(study_set)),
            ('study IDs', '; '.join(study_ids))] \
           + list(extra_info)
    meta = MetaAnalysisPlus(info, dataset=dataset, ids=study_set, prior=prior, q=fdr)

    # output
    if save_files:
        meta.save_csv(os.path.join(outdir, '%s_analysis.csv' % meta.info.name),
                      image_names=image_names)
        meta.save_images(image_names=image_names, outdir=outdir)
    return meta


def analyze_all_terms(dataset, extra_expr=(), prior=0.5, fdr=0.01):
    # TODO with extra lists of study IDs?
    """
    Do a meta-analysis for each term/expression in the dataset or the extra
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
        metas.append(analyze_expression(dataset, expression=expr, prior=prior, fdr=fdr,
                                        save_files=False))
    return metas
