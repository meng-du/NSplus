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

    @classmethod
    def load_default_database(cls):
        data_file = os.path.join(os.path.dirname(__file__), 'neurosynth_data',
                                 'database_v0.6_with_features.pkl')
        return cls.load(data_file)
