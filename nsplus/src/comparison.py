from .metaplus import MetaAnalysisPlus
from .analysisinfo import AnalysisInfo
import random
import numpy as np
import pandas as pd
import os


def even_study_set_size(study_sets):
    """
    Reduce the sizes of all study sets to the smallest set in the list by random
    sampling
    :param study_sets: a list of study sets; each set is a list of string study IDs
    :return: a new list of reduced study sets, and a list of size information (strings,
             e.g. '123' if not reduced, or '123/456' if reduced)
    """
    min_size = min(map(len, study_sets))
    reduced_sets = []
    for study_set in study_sets:
        if min_size == len(study_set):
            reduced_sets.append(study_set)
        else:
            reduced_sets.append(random.sample(study_set, min_size))
    return reduced_sets


def compare_expressions(dataset, expr, contrary_expr, exclude_overlap=True,
                        reduce_larger_set=True, num_iterations=500, two_way=True,
                        prior=0.5, fdr=0.01, extra_info=(), image_names=None,
                        save_files=True, outpath='.'):
    """
    Compare two expressions and return a MetaAnalysisPlus object.
    The number of studies found through the two expressions are likely to be
    different, therefore it's suggested to randomly sample the larger study
    set to reduce its size to the smaller one, then do it multiple times and
    average the results in the end. To do this, set reduce_larger_set=True
    and a large num_iterations.

    :param dataset: a neurosynth Dataset instance to get studies from
    :param expr: a string expression to be analyzed
    :param contrary_expr: a string expression in contrast. The meta-analysis will
                          will be performed on the union of studies found with expr
                          and contrast_expr.
    :param exclude_overlap: (boolean) if true, the studies that are associated with
                            both expressions will be excluded from the meta analysis
    :param reduce_larger_set: (boolean) if true, the larger set of studies found
                              with one of the expressions will be randomly sampled
                              (without replacement) so it has the same size as the
                              smaller set
    :param num_iterations: (int) when randomly sampling the larger study set, the
                           number of iterations to run in order to get different
                           samples of the larger study set
    :param two_way: (boolean) if true, analyze both expr and contrast_expr within
                    the set of (expr + contrast_expr) ; otherwise only analyze expr
    :param prior: (float) the prior probability of a term being used in a study
    :param fdr: the FDR threshold to use when correcting for multiple comparisons
    :param extra_info: (list of (key, value) pairs) extra information to be included
                   in the csv output
    :param image_names: the names of images to be included in the output files.
                        If None, all images will be included.
    :param save_files: (boolean) whether to save the results as csv and nifti files
    :param outdir: (string) directory to save the images/csv
    :return: a list of MetaExtension objects
    """
    # 0) error checking
    if num_iterations < 1:
        raise ValueError('Number of iterations must be greater than 0')
    if prior is not None and (prior <= 0 or prior >= 1):
        raise ValueError('prior has to be greater than 0 and less than 1')
    if reduce_larger_set and num_iterations < 2:
        raise ValueError('The larger study set is reduced, but the number of '
                         'iteration is too small')
    if not reduce_larger_set:
        num_iterations = 1

    # get studies
    study_sets = []
    if exclude_overlap:
        expr, contrary_expr = '(%s) &~ (%s)' % (expr, contrary_expr), \
                              '(%s) &~ (%s)' % (contrary_expr, expr)
    for expression in (expr, contrary_expr):
        try:
            studies = dataset.get_studies(expression=expression)
        except AttributeError:  # in case expression somehow doesn't work
            studies = dataset.get_studies(features=expression)
        if len(studies) == 0:
            raise ValueError('No study in the database is associated with "'
                             + expression + '"')
        study_sets.append(studies)

    # get study set sizes
    if reduce_larger_set:
        sizes = []
        min_size = min(map(len, study_sets))
        for study_set in study_sets:
            size = str(len(study_set)) if min_size == len(study_set) else \
                '%d/%d' % (min_size, len(study_set))
            sizes.append(size)
    else:
        sizes = [str(len(study_set)) for study_set in study_sets]

    meta_lists = [[], []] if two_way else [[]]
    for i in range(num_iterations):
        # reduce size
        if reduce_larger_set:
            new_study_sets = even_study_set_size(study_sets)
        else:
            new_study_sets = study_sets

        # meta analysis
        expr_meta = MetaAnalysisPlus(info=[], dataset=dataset,
                                     ids=new_study_sets[0],
                                     ids2=new_study_sets[1],
                                     prior=prior, q=fdr)
        meta_lists[0].append(expr_meta)

        if two_way:
            contrary_expr_meta = MetaAnalysisPlus(info=[], dataset=dataset,
                                                  ids=new_study_sets[1],
                                                  ids2=new_study_sets[0],
                                                  prior=prior, q=fdr)
            meta_lists[1].append(contrary_expr_meta)

    # get mean images
    mean_metas = [MetaAnalysisPlus.mean(meta_list) for meta_list in meta_lists]

    # add info
    mean_metas[0].info = MetaAnalysisPlus.Info(
        [('expression', expr),
         ('number of studies (expression)', sizes[0]),
         ('contrary expression', contrary_expr),
         ('number of studies (contrary expression)', sizes[1]),
         ('number of iterations', num_iterations)] + list(extra_info))
    if two_way:
        mean_metas[1].info = MetaAnalysisPlus.Info(
            [('expression', contrary_expr),
             ('number of studies (expression)', sizes[1]),
             ('contrary expression', expr),
             ('number of studies (contrary expression)', sizes[0]),
             ('number of iterations', num_iterations)] + list(extra_info))

    # save results
    if save_files:
        outdir = MetaAnalysisPlus.make_result_dir(outpath, mean_metas[0].info.name)
        for mean_meta in mean_metas:
            filename = mean_meta.info.name + '.csv'
            mean_meta.save_csv(os.path.join(outdir, filename),
                               image_names=image_names)
            mean_meta.save_images(outpath=outdir)

    return mean_metas if two_way else mean_metas[0]


def compare_multiple(dataset, expr_list, image_name, lower_thr=None, upper_thr=None,
                     extra_info=(), save_files=True, outpath='.', **kwargs):
    """
    (Battle Royale) Do all possible pairwise comparison within the given term group,
    and then create a winning map.
    See compare_expressions and MetaAnalysisPlus.winnings for more info.
    If there's any conflict between the prior and fdr in image_name and kwargs, info
    in image_name will be used.

    :param kwargs: anything else passed to the pairwise compare_expressions function
    :return: a dictionary {expression: MetaAnalysisPlus winning map}
    """
    # result name & path
    name = '_'.join([AnalysisInfo.shorten_expr(expr) for expr in expr_list])
    outpath = MetaAnalysisPlus.make_result_dir(outpath, name)
    pair_outpath = os.path.join(outpath, 'pairwise_comparisons')
    os.mkdir(pair_outpath)

    # pairwise comparisons
    img_info = AnalysisInfo.get_num_from_name(image_name)
    kwargs.update(img_info)
    pair_metas = {}
    for expr in expr_list:
        pair_metas[expr] = []
        for contra_expr in expr_list:
            if expr == contra_expr:
                continue
            meta = compare_expressions(dataset, expr, contra_expr, two_way=False,
                                       extra_info=extra_info, save_files=save_files,
                                       outpath=pair_outpath, **kwargs)
            pair_metas[expr].append(meta)

    # winning maps
    win_metas = {}
    for expr in pair_metas:
        # info
        info = [('expression', expr)]
        info += [('contrary expression %d' % (i + 1),
                  pair_metas[expr][i].info['contrary expression'])
                 for i in range(len(expr_list) - 1)]
        info += extra_info
        # winnings
        meta = MetaAnalysisPlus.winnings(pair_metas[expr], image_name, lower_thr,
                                         upper_thr, expression=expr, extra_info=info)
        win_metas[expr] = meta

    # counts of winnings
    from datetime import datetime
    print(datetime.now())
    win_meta_imgs = np.array([meta.images['winnings'] for meta in win_metas.values()])
    print(datetime.now())
    win_counts = np.apply_along_axis(lambda x: np.bincount(x, minlength=len(expr_list)),
                                     axis=0, arr=win_meta_imgs).astype(np.int32)
    win_counts_meta_imgs = {str(col): win_counts[col] for col in range(len(expr_list))}
    print(datetime.now())
    win_counts_info = [('expressions', ', '.join(expr_list))] + extra_info
    win_counts_info.append(('description',
                            'This file and corresponding NIFTI images show how many '
                            'winning maps have each possible value at each voxel. '
                            'For example, in column "0" and image "winning_counts_0.nii.gz", '
                            'the value at each voxel is the number of winning maps '
                            'that shows a "0" at this voxel. So in this column/image, '
                            'if a voxel value equals %d, it means all of the winning '
                            'maps show a "0", i.e., no term wins at this voxel. '
                            'This column/image can be used to identify non-selective '
                            'voxels.' % len(expr_list)))
    win_counts_meta = MetaAnalysisPlus(win_counts_info, dataset, images=win_counts_meta_imgs)
    print(datetime.now())

    # save images & csv
    if save_files:
        # winnings
        for win_meta in win_metas.values():
            filename = win_meta.info.name + '.csv'
            win_meta.save_csv(os.path.join(outpath, filename))
            win_meta.save_images(outpath=outpath)
            print('x', datetime.now())
        # counts
        win_counts_meta.save_csv(os.path.join(outpath, name + '_winning_counts.csv'))
        print(datetime.now())
        win_counts_meta.save_images(prefix=name + '_winning_counts', outpath=outpath)
        print(datetime.now())

    return win_metas
