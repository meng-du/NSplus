import pytest
import pandas as pd
from pandas.testing import assert_series_equal
from .util import *
from nsplus.src.ranking import sort_and_save


def test_sort_and_save():
    metas = get_dummy_meta(10, num_info=3)
    means = [[(i + j) * (-1) ** j
              for j in range(3)] for i in range(len(metas))]
    imgs = ['img0', 'img2', 'img3']
    extra_info = pd.DataFrame([('ranked by', 'img2'), ('data type', 'test')])
    result = sort_and_save(metas, means, imgs,
                           rank_by='img2',
                           csv_name='test_sort.csv',
                           extra_info_df=extra_info)
    assert result.shape == (11, 6)
    s = pd.Series(['f1', 'f 2', 'f3', 'f 4', 'f5'] * 2, name='term')
    assert_series_equal(result['term'], s)
    s = pd.Series([i for i in range(1, 11)], name='rank')
    assert_series_equal(result['rank'], s)
