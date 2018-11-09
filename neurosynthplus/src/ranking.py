import numpy as np
import pandas as pd
from scipy.stats import rankdata
from .singleterm import analyze_all_terms
from .analysisinfo import AnalysisInfo


def sort_and_save(metas, means, img_names, rank_by='pFgA_given_pF=0.50', ascending=False,
                  csv_name=None, extra_info_df=None):
    """
    :return: a pandas dataframe of ordered terms and corresponding voxel values
    """
    matrix_as_list = [[metas[i].info['expression'], metas[i].info['number of studies']] +
                      [mean for mean in means[i]]
                      for i in range(len(metas))]
    df = pd.DataFrame(matrix_as_list, columns=['term', '# studies'] + img_names)
    if 'pA' in df.columns:
        df = df.drop(columns='pA')
    df = df.sort_values(rank_by, ascending=ascending)
    df.insert(loc=0, column='rank', value=range(1, df.shape[0] + 1))
    if csv_name:
        csv_df = pd.DataFrame(np.vstack([df.columns, df]))
        pd.concat([extra_info_df, csv_df]).to_csv(csv_name, header=False, index=False)
    return df


def _rank_helper(imgs, voxel, ascending, ties):
    if ascending:
        return rankdata(imgs[:, voxel], method=ties)
    # descending
    if ties == 'max':
        ties = 'min'
    if ties == 'min':
        ties = 'max'
    return imgs.shape[0] + 1 - rankdata(imgs[:, voxel], method=ties)


def rank_terms(dataset, rank_by='pFgA_given_pF=0.50', extra_expr=(), csv_name=None,
               ascending=False, rank_first=False, ties='average', extra_info=()):
    """
    Rank all of the terms in NeuroSynth by the voxel values in specified image (rank_by).

    :param dataset: a NeuroSynth Dataset instance masked by an ROI
    :param rank_by: (string) an image name to get voxel values from. Available images are:
                    'pAgF', 'pFgA', 'pAgF_given_pF=0.50', 'pFgA_given_pF=0.50',
                    'consistency_z', 'specificity_z', 'pAgF_z_FDR_<fdr>', 'pFgA_z_FDR_<fdr>'
    :param extra_expr: (list of strings) a list of extra expressions to be analyzed and
                       included in the results
    :param csv_name: (string) output file name, or None if not saving a file
    :param ascending: (boolean) if True, terms with with the smallest voxel values will have
                      the smallest ranks
    :param rank_first: (boolean) if True, terms will be first ranked at each voxel, and
                       then their ranks will be averaged across the ROI; otherwise, voxel
                       values for each term will be first averaged across the ROI, and then
                       the terms are ranked accordingly
    :param ties: (string) the method used to assign ranks to tied elements, only useful
                 when rank_first=True. The options are 'average', 'min', 'max', 'dense'
                 and 'ordinal'. See scipy.stats.rankdata for details
    :param extra_info: (list of tuples) extra information to put at the top of csv
    :return: an NsInfo object and a pandas data frame of the rank
    """
    img_info = AnalysisInfo.get_num_from_img_name(rank_by)
    metas = analyze_all_terms(dataset, extra_expr, **img_info)
    img_names = list(metas[0].images.keys())
    img_means = [np.mean([meta.images[img] for img in img_names], axis=1) for meta in metas]
    if rank_first:
        imgs = np.array([np.array(meta.images[rank_by]) for meta in metas])
        rank_means = np.array([np.mean([_rank_helper(imgs, voxel, ascending, ties)
                                        for voxel in range(len(imgs[0]))],
                                       axis=0)]).T
        img_means = np.hstack((rank_means, img_means))
        img_names = [rank_by + '_rank'] + img_names
        rank_by += '_rank'
    ascending = True if rank_first else ascending

    info = extra_info + [('ranked by', rank_by),
                         ('data type', 'average rank' if rank_first else 'average value')]
    if len(extra_expr) > 0:
        info.append(('extra terms', ', '.join(extra_expr)))
    if rank_first:
        info.append(('tie resolution', ties))
    info = AnalysisInfo(info).as_pandas_df()
    rank = sort_and_save(metas, img_means, img_names, rank_by, ascending, csv_name, info)

    return info, rank
