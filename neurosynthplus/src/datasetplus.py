import os
import pickle
import gzip
import shutil
import neurosynth as ns


class DatasetPlus(ns.Dataset):
    """
    An extension of the NeuroSynth Dataset class.
    """
    def __init__(self, *args, **kwargs):
        super(DatasetPlus, self).__init__(*args, **kwargs)

    def mask(self, mask_file=None):
        if mask_file is None:  # use neurosynth default mask
            mask_file = os.path.join(os.path.dirname(os.path.abspath(ns.__file__)),
                                     'resources',
                                     'MNI152_T1_2mm_brain.nii.gz')
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
                                 'database_v0.7_with_features.pkl.gz')
        dataset = cls.load(data_file, compressed=True)
        return dataset

    @classmethod
    def load(cls, filename, compressed=False):
        """
        Load a pickled Dataset instance from pickle file or compressed pickle file.
        """
        if compressed:
            with gzip.open(filename, 'rb') as infile:
                # this is just copy-pasting from neurosynth code
                try:
                    dataset = pickle.load(infile)
                except UnicodeDecodeError:
                    dataset = pickle.load(infile, encoding='latin')

            if hasattr(dataset, 'feature_table'):
                dataset.feature_table._csr_to_sdf()
        else:
            dataset = super(DatasetPlus, cls).load(filename)

        dataset.__class__ = DatasetPlus  # TODO any better way to downcast class?
        return dataset

    def save(self, filename, compress=False):
        super(DatasetPlus, self).save(filename)
        if compress:
            temp_filename = filename + '.temporarynspfile'
            os.rename(filename, temp_filename)
            with open(temp_filename, 'rb') as infile:
                with gzip.open(filename, 'wb') as outfile:
                    shutil.copyfileobj(infile, outfile)
            os.remove(temp_filename)
