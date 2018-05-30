from collections import OrderedDict
from string import punctuation
import numpy as np
import pandas as pd
import neurosynth as ns


class MetaAnalysisPlus(ns.meta.MetaAnalysis):
    """
    An extension of the NeuroSynth MetaAnalysis class.
    """
    def __init__(self, info, *args, **kwargs):
        """
        :param info: a list of string tuples containing information regarding the
                     meta analysis, e.g. [('expr', 'social'), ('num_studies', 1000)]
        """
        super(MetaAnalysisPlus, self).__init__(*args, **kwargs)
        self.info = self.Info(info)

    # Information #

    class Info(OrderedDict):
        # TODO convert to log file (with output file names etc)
        def __init__(self, *args, **kwargs):
            super(MetaAnalysisPlus.Info, self).__init__(*args, **kwargs)
            self.name = self.get_shorthand()

        def get_shorthand(self):
            """
            Return a short description of the meta analysis (to be used for file names)
            """
            name = ''
            if 'expr' in self:
                name = MetaAnalysisPlus.Info.get_shorthand_expr(self['expr'])
            if 'contrary_expr' in self:
                name += '_vs_' + MetaAnalysisPlus.Info.get_shorthand_expr(self['contrary_expr'])
            return name

        @staticmethod
        def get_shorthand_expr(expr):
            abbr = expr.split(' ', maxsplit=1)[0]
            return abbr.strip(punctuation)

    # Methods for File Output #

    def _get_images_with_info(self, image_names=None):
        """
        Get a pandas data frame of images prefixed with their information
        :param image_names: the names of images to be included in the result.
                            If None, all images will be returned.
        :return: a pandas data frame of images
        """
        if self.images is None:  # TODO unnecessary?
            raise RuntimeError('Images not initialized')

        images = list(set(image_names) & self.images.keys())  # find intersection
        info_list = [list(self.info.values()) + [img_name] for img_name in images]
        info_df = pd.DataFrame(info_list, index=list(self.info.keys()) + ['image'])
        image_df = pd.DataFrame([self.images[img_name].tolist() for img_name in images])
        image_df.transpose()
        return pd.concat([info_df, image_df])

    def write_images_to_csv(self, filename, delimiter=',', image_names=None):
        df = self._get_images_with_info(image_names)
        df.to_csv(filename, sep=delimiter, header=False)

    def save_images(self, prefix=None, postfix='', image_names=None):
        if self.images is None:  # TODO unnecessary?
            raise RuntimeError('Images not initialized')

        images = list(set(image_names) & self.images.keys())  # find intersection
        for img_name in images:
            # file name
            filename = prefix if prefix is not None else self.info.name
            if len(filename) > 0 and filename[len(filename) - 1] != '_':
                filename += '_'
            if len(postfix) > 0 and postfix[0] != '_':
                postfix = '_' + postfix
            filename += img_name + postfix + '.nii.gz'
            # save image
            ns.imageutils.save_img(self.images[img_name],
                                   filename=filename, masker=self.dataset.masker)

        # TODO: print/save self.info & corresponding file names
