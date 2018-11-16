import pytest
from numpy.testing import assert_array_almost_equal
from .util import *
from nsplus import MetaAnalysisPlus


def test_init():
    # info
    meta = get_dummy_meta(1)
    assert len(meta.info) == 1
    assert meta.info.name == 'f1'
    meta = get_dummy_meta(1, num_info=4)
    assert len(meta.info) == 4
    assert meta.info.name == 'f1_vs_f'
    assert meta.info['info 3'] == 'f 4'

    # passed images
    meta_list = get_dummy_meta(5)
    print([m.images for m in meta_list])
    assert meta_list[2].images['association-test_z'].dtype == np.float64
    assert_array_almost_equal(meta_list[1].images['association-test_z_FDR_'], [16, 1.2, -8, -0.4, 0])
    assert_array_almost_equal(meta_list[2].images['uniformity-test_z'], [-48, -3.6, 24, 1.2, 0])
    assert_array_almost_equal(meta_list[3].images['pFgA_given_pF='], [16, 1.2, -8, -0.4, 0])
    assert_array_almost_equal(meta_list[4].images['association-test_z'], [0, 0, 0, 0, 0])

    # constructed images TODO


def test_conjunction():
    meta_list = get_dummy_meta(5)
    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='uniformity-test_z', lower_thr=1)
    assert result.images['conjunction'].dtype == np.int
    assert_array_almost_equal(result.images['conjunction'], [2, 2, 3, 2, 0])
    assert result.info['criterion'] == '>1'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='pFgA_given_pF=0.50', upper_thr=-0.3)
    assert_array_almost_equal(result.images['conjunction'], [3, 2, 2, 1, 0])
    assert result.info['based on'] == 'pFgA_given_pF=0.50'
    assert result.info['criterion'] == '<-0.3'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='association-test_z_FDR_0.01', lower_thr=-10, upper_thr=0.5)
    assert_array_almost_equal(result.images['conjunction'], [1, 3, 1, 3, 5])
    assert result.info['based on'] == 'association-test_z_FDR_0.01'
    assert result.info['criterion'] == '-10-0.5'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='pFgA', lower_thr=-1.2, upper_thr=-30)
    assert_array_almost_equal(result.images['conjunction'], [4, 3, 3, 4, 5])
    assert result.info['criterion'] == '>-1.2or<-30'
