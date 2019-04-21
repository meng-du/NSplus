import pytest
from .util import *
from nsplus import DatasetPlus


def test_default_database():
    dataset = DatasetPlus.load_default_database()
    assert dataset.image_table.data.shape == (228453, 14371)
    assert len(dataset.feature_names) == 3168
    assert len(dataset.get_studies(features='social')) == 1302
    assert len(dataset.get_studies(features='visual')) == 3110
    assert len(dataset.get_studies(features='yo nonsense feature')) == 0
    assert len(dataset.get_studies(expression='yo nonsense feature')) == 0


def test_add_custom_term_by_ids():
    dataset = get_test_dataset()
    added = dataset.add_custom_term_by_ids('such awesomeness', [9593960, 11114477, 12077008, 5300321])
    assert len(added) == 3
    added = dataset.add_custom_term_by_ids('moreawesomeness', ['9593960', '11114477', 12077008])
    assert len(added) == 1
    assert dataset.get_studies(features='moreawesomeness') == [12077008]
    assert len(dataset.get_studies(expression='such awesomeness')) == 3
    assert len(dataset.get_studies(expression='such awesomeness & moreawesomeness')) == 3
    assert len(dataset.get_studies(expression='such awesomeness | moreawesomeness')) == 4
    features = dataset.feature_names
    assert 'such awesomeness' in features
    assert 'moreawesomeness' in features
    with pytest.raises(ValueError):
        dataset.add_custom_term_by_ids('very wrong', [123, 456, 789])
    with pytest.raises(ValueError):
        dataset.add_custom_term_by_ids('emotion', [9593960, 11114477, 12077008])


def test_add_custom_term_by_expression():
    dataset = get_test_dataset()
    dataset.add_custom_term_by_ids('such awesomeness', [9593960, 11114477, 12077008, 5300321])
    dataset.add_custom_term_by_ids('moreawesomeness', ['9593960', '11114477', 12077008])
    added = dataset.add_custom_term_by_expression('aw', 'such awesomeness & moreawesomeness')
    assert len(added) == 3
    added = dataset.add_custom_term_by_expression('aww', 'such awesomeness | moreawesomeness')
    assert len(added) == 4
