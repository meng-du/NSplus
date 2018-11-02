from neurosynthplus import DatasetPlus, MetaAnalysisPlus
import os
import numpy as np


def get_dummy_dataset():
    data_file = os.path.join(os.path.dirname(__file__), os.pardir, 'data',
                             'test_dummy_database.pkl.gz')
    return DatasetPlus.load(data_file, compressed=True)


def get_test_dataset():
    data_file = os.path.join(os.path.dirname(__file__), os.pardir, 'data',
                             'test_database.pkl.gz')
    return DatasetPlus.load(data_file, compressed=True)


def get_dummy_meta(how_many=1, dataset=None, num_info=1):
    if dataset is None:
        dataset = get_dummy_dataset()
    features = dataset.get_feature_names()
    meta_list = []
    for i in range(how_many):
        info = [('expression', features[i % 5])]
        if num_info > 1:
            info.append(('contrary expression', features[(i + 1) % 5]))
        if num_info > 2:
            for j in range(num_info - 2):
                info.append(('info ' + str(j + 2), features[(i + j + 2) % 5]))
        x = i + 1
        images = {'img%d' % img: np.array([4, 0.3, -2, -0.1, 0]) * ((-1) ** x) * x * img
                  for img in range(5)}
        meta_list.append(MetaAnalysisPlus(info, dataset, images))

    return meta_list if how_many > 1 else meta_list[0]
