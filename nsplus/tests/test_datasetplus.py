import pytest
from .util import *
from nsplus import DatasetPlus


def test_default_database():
    dataset = DatasetPlus.load_default_database()
    assert dataset.image_table.data.shape == (228453, 14371)
    assert len(dataset.get_feature_names()) == 3168
    assert len(dataset.get_studies(features='social')) == 1302
    assert len(dataset.get_studies(features='visual')) == 3110


def test_add_custom_term():
    dataset = get_test_dataset()
    added = dataset.add_custom_term('such awesomeness', [9593960, 11114477, 12077008])
    assert len(added) == 3
    added = dataset.add_custom_term('moreawesomeness', ['9593960', '11114477', 12077008])
    assert len(added) == 1
    assert dataset.get_studies(features='moreawesomeness') == [12077008]
    assert len(dataset.get_studies(expression='such awesomeness')) == 3
    features = dataset.get_feature_names()
    assert 'such awesomeness' in features
    assert 'moreawesomeness' in features
    with pytest.raises(ValueError):
        dataset.add_custom_term('very wrong', [123, 456, 789])
    with pytest.raises(ValueError):
        dataset.add_custom_term('emotion', [9593960, 11114477, 12077008])
