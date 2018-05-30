import numpy as np
import csv
from scipy.stats import rankdata
from analyze import analyze_all_terms

# TODO: reuires numpy>1.7.0


def _sort_and_save(metas, means, img_names, rank_by='pFgA_given_pF=0.50', reverse=True,
                   csv_name=None):
    """
    :return: a numpy array of ordered terms and corresponding average voxel values
             ([term1, term2, ...],
              [avg_image_A_1, avg_image_A_2, ...],
              [avg_image_B_1, avg_image_B_2, ...], ...)
    """
    term_list = [meta.info['expr'] for meta in metas]
    matrix_as_list = [tuple([term_list[i]] + [mean for mean in means[i]])
                      for i in range(len(term_list))]
    matrix = np.array(matrix_as_list, dtype=[('term', '|S64')] +
                                            [(img, 'float64')for img in img_names])
    matrix.sort(order=rank_by, axis=0)
    if reverse:
        matrix = matrix[::-1]
    # save/return results
    if csv_name:
        np.savetxt(csv_name, matrix, delimiter=',', header=','.join(matrix.dtype.names))
        # with open(csv_name, 'w') as outfile:
        #     writer = csv.writer(outfile, delimiter=',')
        #     writer.writerow(matrix.dtype.names)  # header
        #     writer.writerows(matrix)  # content
    return matrix


def _rank_helper(imgs, voxel, descending, ties):
    if descending:
        if ties == 'max':
            ties = 'min'
        if ties == 'min':
            ties = 'max'
        return imgs.shape[0] + 1 - rankdata(imgs[:, voxel], method=ties)
    # ascending
    return rankdata(imgs[:, voxel], method=ties)


def rank(dataset, rank_by='pFgA_given_pF=0.50', extra_expr=(), csv_name=None,
         descending=True, rank_first=False, ties='average'):
    """
    Rank all of the terms in NeuroSynth by the voxel values in specified image (rank_by).
    :param dataset: a NeuroSynth Dataset instance masked by an ROI
    :param rank_by: (string) an image name to get voxel values from
    :param extra_expr: (list of strings) a list of extra expressions to be analyzed and
                       included in the results
    :param csv_name: (string) output file name, or None if not saving a file
    :param descending: (boolean) if True, terms with with larger voxel values will have
                       smaller ranks
    :param rank_first: (boolean) if True, terms will be first ranked at each voxel, and
                       then their ranks will be averaged across the ROI; otherwise, voxel
                       values for each term will be first averaged across the ROI, and then
                       the terms are ranked accordingly
    :param ties: (string) the method used to assign ranks to tied elements, only useful
                 when rank_first=True. The options are 'average', 'min', 'max', 'dense'
                 and 'ordinal'. See scipy.stats.rankdata for details
    """
    metas = analyze_all_terms(dataset, extra_expr)
    img_names = metas[0].images.keys()
    img_means = [np.mean([meta.images[img] for img in img_names], axis=1) for meta in metas]
    if rank_first:
        imgs = np.array([np.array(meta.images[rank_by]) for meta in metas])
        rank_means = np.array([np.mean([_rank_helper(imgs, voxel, descending, ties)
                                        for voxel in range(len(imgs[0]))],
                                       axis=0)]).T
        img_means = np.hstack((rank_means, img_means))
        img_names = [rank_by + '_rank'] + img_names
        rank_by += '_rank'
    reverse = False if rank_first else descending
    return _sort_and_save(metas, img_means, img_names, rank_by, reverse, csv_name)
