import pytest
from numpy.testing import assert_array_almost_equal
from .util import *
from neurosynthplus import MetaAnalysisPlus


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
    assert meta_list[2].images['img0'].dtype == np.float64
    assert_array_almost_equal(meta_list[1].images['img2'], [16, 1.2, -8, -0.4, 0])
    assert_array_almost_equal(meta_list[4].images['img0'], [0, 0, 0, 0, 0])

    # constructed images TODO


def test_conjunction():
    meta_list = get_dummy_meta(5)
    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='img4', lower_threshold=1)
    assert result[0].dtype == np.int
    assert_array_almost_equal(result[0], [2, 2, 3, 2, 0])
    assert result[1] == '>1'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='img1', upper_threshold=-0.3)
    assert_array_almost_equal(result[0], [3, 2, 2, 1, 0])
    assert result[1] == '<-0.3'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='img2', lower_threshold=-10, upper_threshold=0.5)
    assert_array_almost_equal(result[0], [1, 3, 1, 3, 5])
    assert result[1] == '-10-0.5'

    result = MetaAnalysisPlus.conjunction(
        meta_list, image_name='img3', lower_threshold=-1.2, upper_threshold=-30)
    assert_array_almost_equal(result[0], [4, 3, 3, 4, 5])
    assert result[1] == '>-1.2or<-30'
