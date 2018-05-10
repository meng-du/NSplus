import numpy as np
import csv
from scipy.stats import rankdata
from metaext import get_image_means, analyze_all_terms


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
