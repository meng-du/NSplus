import os
import neurosynth as ns


class DatasetPlus(ns.Dataset):
    """
    An extension of the NeuroSynth Dataset class.
    """
    def __init__(self, *args, **kwargs):
        super(DatasetPlus, self).__init__(*args, **kwargs)

    def mask(self, mask_file):
        self.masker = ns.mask.Masker(mask_file)
        self.create_image_table()

    def get_feature_names(self, features=None):
        """
        Returns names of features, but excluding those that start with a digit
        """
        all_feature_names = super(DatasetPlus, self).get_feature_names(features)
        return [feature for feature in all_feature_names if not feature[0].isdigit()]

    @classmethod
    def load_default_database(cls):
        data_file = os.path.join(os.path.dirname(__file__), os.pardir, 'data',
                                 'database_v0.7_with_features.pkl')
        dataset = cls.load(data_file)
        dataset.__class__ = DatasetPlus  # TODO any better way to downcast class?
        return dataset
