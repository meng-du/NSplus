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
        """
        :param dataset: initialize from a Neurosynth Dataset instance
        """
        super(DatasetPlus, self).__init__(*args, **kwargs)
        self.custom_terms = {}  # term - study IDs

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
        all_features = super(DatasetPlus, self).get_feature_names(features)
        all_features = [feature for feature in all_features if not feature[0].isdigit()]
        return all_features + list(self.custom_terms.keys())

    def add_custom_term(self, term, study_ids):
        """
        Add a custom term to the dataset
        :param term: (string) name of your term
        :param study_ids: (list of integers) a list of study IDs
        """
        if term in self.get_feature_names():
            raise ValueError('Term "%s" already exists.' % term)
        # get IDs that are in database
        valid_ids = set(self.image_table.ids) & set(study_ids)
        if len(valid_ids) == 0:
            raise ValueError('Must provide a list of valid study IDs')
        self.custom_terms[term] = valid_ids

    def get_studies(self, features=None, expression=None, *args, **kwargs):
        results = []
        if isinstance(features, str):
            results += self.get_custom_studies(features)
        elif isinstance(features, list):
            for feature in features:
                results += self.get_custom_studies(feature)
        results += self.get_custom_studies(expression)

        if len(results) == 0:
            return super(DatasetPlus, self).get_studies(features=features,
                                                        expression=expression,
                                                        *args, **kwargs)

    def get_custom_studies(self, custom_term):
        if custom_term in self.custom_terms:
            return self.custom_terms[custom_term]
        else:
            return []

    @classmethod
    def load_default_database(cls):
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_file = os.path.join(parent_dir, 'data', 'database_v0.7.pkl.gz')
        return cls.load(data_file, compressed=True)

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
        dataset.custom_terms = {}
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
