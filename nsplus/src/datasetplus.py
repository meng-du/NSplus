import os
import pickle
import gzip
import shutil
import pkg_resources as pkgr
import neurosynth as ns
import pandas as pd
import numpy as np
import copy


class DatasetPlus(ns.Dataset):
    """
    An extension of the Neurosynth Dataset class.
    """
    def __init__(self, ns_dataset=None, *args, **kwargs):
        """
        :param dataset: initialize from a Neurosynth Dataset instance
        """
        if ns_dataset:
            self.__dict__ = copy.copy(ns_dataset.__dict__)
        else:
            super(DatasetPlus, self).__init__(*args, **kwargs)
        self.custom_terms = {}  # term - study IDs
        self.feature_names = set(super(DatasetPlus, self).get_feature_names())

    def mask(self, mask_file=None):
        if mask_file is None:  # use neurosynth default mask
            mask_file = os.path.join(os.path.dirname(os.path.abspath(ns.__file__)),
                                     'resources',
                                     'MNI152_T1_2mm_brain.nii.gz')
        self.masker = ns.mask.Masker(mask_file)
        self.create_image_table()

    def add_custom_term_by_ids(self, new_term, study_ids, frequency=0.1):
        """
        Add a custom term to the dataset by associating it with a list of
        study IDs.
        This will add the new term as a feature to the feature table of the
        database, where the associated study IDs has an arbitrary fixed
        term frequency. The purpose of this arbitrary frequency
        is just for the get_studies function to return the associated
        study IDs.

        :param new_term: (string) name of your term
        :param study_ids: (list of integers) a list of study IDs associated
                          with the new term
        :param frequency: (float) an arbitrary term frequency level to be
                          associated with the study IDs in the database.
                          Should be sufficiently greater than the default
                          frequency threshold (0.001).
        :return a subset of the given study_ids that are valid
        """
        if new_term in self.feature_names:
            raise ValueError('Term "%s" already exists.' % new_term)
        # get IDs that are in database
        all_study_ids = self.feature_table.data.index.values
        valid_ids = set(all_study_ids) & set(study_ids)
        if len(valid_ids) == 0:
            raise ValueError('Must provide a list of valid study IDs')
        # add to custom term list
        self.custom_terms[new_term] = valid_ids
        self.feature_names.add(new_term)
        # add to database
        feature_df = pd.DataFrame(np.zeros((len(all_study_ids), 1)),
                                  index=all_study_ids, columns=[new_term])
        feature_df[new_term][valid_ids] = frequency
        self.add_features(feature_df)
        return valid_ids

    def add_custom_term_by_expression(self, new_term, expression,
                                      frequency=0.1, **kwargs):
        """
        Add a custom term by associating it with study IDs found with an
        existing expression. See more information in add_custom_term_by_ids
        Example:
            dataset.add_custom_term_by_expression(
                'emotional experience',
                'emotion* &~ (emotional faces | emotional stimuli)')

        :return: a list of study IDs associated with the new term
        """
        if new_term in self.feature_names:
            raise ValueError('Term "%s" already exists.' % new_term)
        study_ids = self.get_studies(expression=expression, **kwargs)
        study_ids = self.add_custom_term_by_ids(new_term, study_ids, frequency)
        return study_ids

    @classmethod
    def load_default_database(cls):
        data_file = pkgr.resource_stream('nsplus',
                                         os.path.join('data',
                                                      'database_v0.7.pkl.gz'))
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

        return cls(ns_dataset=dataset)

    def save(self, filename, compress=False):
        """
        Save the current Dataset instance to a pickle file.
        Note all custom terms will be lost.
        """
        super(DatasetPlus, self).save(filename)
        if compress:
            temp_filename = filename + '.temporarynspfile'
            os.rename(filename, temp_filename)
            with open(temp_filename, 'rb') as infile:
                with gzip.open(filename, 'wb') as outfile:
                    shutil.copyfileobj(infile, outfile)
            os.remove(temp_filename)
