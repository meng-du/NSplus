import os
import neurosynth as ns


class DatasetPlus(ns.dataset):
    """
    The Neurosynth Dataset class with a refactored constructor
    """
    def __init__(self, filename, feature_filename=None, masker=None, r=6,
            transform=True, target='MNI', **kwargs):
        # ns.Dataset.__init__(*args, **kwargs)
        # Instance properties
        self.r = r
        self.masker = masker
        self.default_masker = ns.mask.Masker(
            os.path.join(os.path.dirname(__file__), os.path.pardir,
                         'resources', 'MNI152_T1_2mm_brain.nii.gz'))  # TODO

        # Set up transformations between different image spaces
        if transform:
            if not isinstance(transform, dict):
                transform = {'T88': ns.transformations.t88_to_mni(),
                             'TAL': ns.transformations.t88_to_mni()
                             }
            self.transformer = ns.transformations.Transformer(transform, target)
        else:
            self.transformer = None

        # Load and process activation data
        self.activations = self._load_activations(filename)

        # Create supporting tables for images and features
        self.create_image_table()
        if feature_filename is not None:
            self.add_features(feature_filename, **kwargs)

    def reset_mask(self):
        if self.masker is None:
            return
        self.masker.unmask() # ???

    def add_mask(self, mask_file):
        self.masker = ns.mask.Masker(mask_file)
        self.create_image_table()
        if feature_filename is not None:  # ???
            self.add_features(feature_filename, **kwargs)
