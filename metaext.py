import neurosynth as ns
import numpy as np
import csv
from collections import OrderedDict


class MetaExtension(object):
    # TODO inherit meta?
    def __init__(self, info=(), meta_analysis=None, images=None, name='', filenamer_func=None, mask=None):
        # TODO assign a name to each MetaExtension rather than using a function
        # TODO remove meta_analysis
        """
        Create a MetaExtension instance
        :param info: an OrderedDict of information related to this meta analysis
        :param meta_analysis: a neurosynth MetaAnalysis object
        :param images: a dictionary of {image_name: image}, same as neurosynth.MetaAnalysis.images
        :param filenamer_func: a function that takes the info dictionary (i.e. the first parameter) and return a string
                               to be prefixed to image names when saving the images
        """
        self.info = info
        self.mask = meta_analysis.dataset.masker if meta_analysis is not None else mask
        self.images = images
        self.name = name
        self.filenamer = filenamer_func
        if images is None and meta_analysis is not None:
            self.images = meta_analysis.images

    def get_filename(self):
        # TODO change func name to descriptor
        return '' if self.filenamer is None else self.filenamer(self.info)

    def get_images_as_list(self, image_names=None):
        """
        Get a list of images prefixed with information
        :param image_names: the names of images to be included in the result. If None, all images will be returned.
        :return: a list of images (a list of lists of strings)
        """
        if self.images is None:
            raise RuntimeError('Images not initialized')
        result = []
        # Note: the length of image arrays here exceeds the maximum number of columns in MS Excel
        for imageName in self.images.keys():
            if (image_names is not None) and (imageName not in image_names):
                continue
            imageAsList = self.images[imageName].tolist()
            prefix = self.info.values()
            prefix.append(imageName)
            result.append(prefix + imageAsList)
        return result

    @classmethod
    def get_mean_images(cls, metaext_lists):
        # TODO test when length != 1
        """
        :param metaext_lists: a list of lists of MetaExtension to be averaged
        :return: a list of MetaExtension
        """
        if len(metaext_lists) == 1:
            mean_meta_ext_list = metaext_lists[0]
        else:
            mean_meta_ext_list = []
            # calculate means for each comparison across all iterations
            for metaExts in zip(*metaext_lists):  # iterating through columns
                # find intersection of image names
                allImgNames = [metaExt.images.keys() for metaExt in metaExts]
                imgNames = set(allImgNames[0]).intersection(*allImgNames)
                # calculate means
                meanImages = {}
                for imgName in imgNames:
                    meanImages[imgName] = np.mean([metaExt.images[imgName] for metaExt in metaExts], axis=0)
                mean_meta_ext_list.append(MetaExtension(info=metaExts[0].info, images=meanImages,
                                                        filenamer_func=metaExts[0].filenamer, mask=metaExts[0].mask))
        return mean_meta_ext_list

    @classmethod
    def _save_computed_image(cls, metaext_list, computed_img, comparison_name, computation_type, save_files, image_name,
                             image_info=None, file_prefix=None):
        """
        :param image_info: an extra string containing information regarding the computed image.
        """
        # TODO change image_info to a dict?
        analysis_names = [(metaext.name if len(metaext.name) > 0 else metaext.get_filename())
                          for metaext in metaext_list]
        if image_info is None:
            info = OrderedDict([('source_images', ', '.join(analysis_names))])
        else:
            info = OrderedDict([('source_images', ', '.join(analysis_names)), ('info', image_info)])
        prefix = file_prefix + '_' if (file_prefix is not None) and len(file_prefix) > 0 else ''
        csv_name = prefix + image_name + comparison_name + '_' + computation_type
        result = cls(info, images={image_name: computed_img}, name=csv_name, mask=metaext_list[0].mask)
        if save_files:
            result.write_images_to_csv(csv_name + '.csv')  # TODO path
            result.save_images(metaext_list[0].mask, prefix, comparison_name + '_' + computation_type)
        return result

    @classmethod
    def get_selectivity_image(cls, metaext_list, thresholds, image_name='pFgA_z', save_files=True, file_prefix=None):
        """
        Given a list of pairwise comparison results featuring one expression, compute a new MetaExtension object with
        one image, where the integer values at a voxel means the level of superiority the featured expression has over
        the compared expressions. For example, given the comparisons (expr0_vs_expr1, expr0_vs_expr2, expr0_vs_expr3),
        and thresholds (0.50, 0.60), a voxel would have 0 if its value < 0.50 in any of the three comparisons; or 1 if
        its value > 0.50 in all of the three comparisons, but < 0.60 in any of them; or 2 if its value > 0.60 in all of
        the three comparisons.
        The maximum value at a voxel in the result image equals the length of the thresholds list.
        :param metaext_list: a list of MetaExtension objects resulted from a pairwise comparison
        :param thresholds: (a list of floats) points that define different levels of superiority
        :param image_name: a string name of the image to create the selectivity map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the selectivity image
        """
        if thresholds is None or len(thresholds) == 0:
            raise ValueError('No threshold specified')
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        selectivity = np.zeros(sourceImgs.shape[1]).astype(np.float64)  # empty array of same length as the source image
        for threshold in thresholds:
            selectivity += np.all(sourceImgs > threshold, axis=0).astype(np.float64)

        info = str(thresholds)[1:-1]
        return cls._save_computed_image(metaext_list, selectivity, '', 'selectivity', save_files, image_name, info,
                                        file_prefix)

    @classmethod
    def get_max_image(cls, metaext_list, image_name='pFgA_z', save_files=True, file_prefix=None):
        """
        Given a MetaExtension list, compute a new MetaExtension object with one image, where the value at each voxel is
        the maximum value at that voxel in the given list
        """
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        maximum = np.amax(sourceImgs, axis=0)
        return cls._save_computed_image(metaext_list, maximum, '', 'maximum', save_files, image_name, None, file_prefix)

    @classmethod
    def _get_conjunction_array(cls, metaext_list, lower_threshold=None, upper_threshold=None, image_name='pFgA_z'):
        """
        Helper function
        :return: the conjunction image as an nd array, and a string describing the conjunction criterion
        """
        if lower_threshold is None and upper_threshold is None:
            raise ValueError('No threshold specified')
        sourceImgs = np.array([metaext.images[image_name] for metaext in metaext_list])
        if upper_threshold is None:
            conjunction = np.sum(sourceImgs > lower_threshold, axis=0).astype(np.float64)
            comparison_name = '>' + str(lower_threshold)
        elif lower_threshold is None:
            conjunction = np.sum(sourceImgs < upper_threshold, axis=0).astype(np.float64)
            comparison_name = '<' + str(upper_threshold)
        else:
            if lower_threshold < upper_threshold:
                conjunction = np.sum((sourceImgs > lower_threshold) & (sourceImgs < upper_threshold), axis=0) \
                              .astype(np.float64)
                comparison_name = str(lower_threshold) + '-' + str(upper_threshold)
            elif lower_threshold > upper_threshold:
                conjunction = np.sum((lower_threshold < sourceImgs or sourceImgs < upper_threshold), axis=0) \
                              .astype(np.float64)
                comparison_name = '>' + str(lower_threshold) + 'or' + '<' + str(upper_threshold)
            else:
                raise ValueError('Lower and upper thresholds must be different values')

        return conjunction, comparison_name

    @classmethod
    def get_conjunction_image(cls, metaext_list, lower_threshold=None, upper_threshold=None, image_name='pFgA_z',
                              save_files=True, file_prefix=None):  # TODO change file_prefix to a info dict?
        """
        From images with the specified image_name in the given list, compute a new MetaExtension object with one image,
        where the value at a voxel is the number of images in which this voxel value passes the given threshold
        criterion.
        If both lower_threshold and upper_threshold are specified, and lower_threshold > upper_threshold, the voxels
        that are EITHER greater than the lower_threshold OR less the upper_threshold will be counted; otherwise if
        lower_threshold < upper_threshold, the voxels that are BOTH greater than the lower_threshold AND less the
        upper_threshold will be counted.
        MetaExtension objects must have the same mask.
        :param metaext_list: a list of MetaExtension objects
        :param upper_threshold: a float value criterion for voxels
        :param lower_threshold: a float value criterion for voxels
        :param image_name: a string name of the image to create the conjunction map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the conjunction image
        """
        conjunction, comparison_name = cls._get_conjunction_array(metaext_list, lower_threshold, upper_threshold,
                                                                  image_name)
        return \
            cls._save_computed_image(metaext_list, conjunction, comparison_name, 'conjunction', save_files, image_name,
                                     file_prefix=file_prefix)

    @classmethod
    def get_conjunction_image_with_separate_criteria(cls, metaext_list, thresholds, binary=False, image_name='pFgA_z',
                                                     save_files=True, file_prefix=None):
        """
        From images with the specified image_name in the given list, create a new MetaExtension object with one image,
        where the value at a voxel is the number of images in which this voxel value passes the given threshold criterion.
        If both lower_threshold and upper_threshold are specified, and lower_threshold > upper_threshold, the voxels
        that are EITHER greater than the lower_threshold OR less the upper_threshold will be counted; otherwise if
        lower_threshold < upper_threshold, the voxels that are BOTH greater than the lower_threshold AND less the
        upper_threshold will be counted.
        MetaExtension objects must have the same mask.
        :param metaext_list: a list of MetaExtension objects
        :param thresholds: a list of tuples [(lower_threshold_1, upper_threshold_1), (lower_threshold_2,
                           upper_threshold_2), ...]. Its length should be the same as metaext_list
        :param binary: if True, any voxel with value == number_of_images will be substituted with a 1, and other voxel
                       values will be substituted with 0s
        :param image_name: a string name of the image to create the conjunction map from
        :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
        :param file_prefix: a string to be prefixed to .csv and .nii.gz conjunction file names
        :return: a MetaExtension object with the conjunction image
        """
        individual_conjs = []
        info = ''
        for metaext, threshold in zip(metaext_list, thresholds):
            individual_conj, comparison_name = cls._get_conjunction_array([metaext], threshold[0], threshold[1],
                                                                          image_name)
            individual_conjs.append(individual_conj)
            info += comparison_name + ', '
        info = info[:-2]
        conjunction = np.sum(individual_conjs, axis=0)
        if binary:
            conjunction = (conjunction == len(individual_conjs)).astype(np.float64)
        return cls._save_computed_image(metaext_list, conjunction, '', 'conjunction', save_files, image_name, info,
                                        file_prefix)

    def write_images_to_csv(self, filename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        data = np.array(self.get_images_as_list(image_names)).T
        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for row in data:
                writer.writerow(row)

    @classmethod
    def write_ext_list_to_csv(cls, metaext_list, outfilename, delimiter=',', image_names=None):
        # TODO could add row names (self.info.keys()) before image list
        results = [meta_ext.get_images_as_list(image_names) for meta_ext in metaext_list]
        results = np.concatenate(results).T  # concatenate and transpose
        with open(outfilename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for result in results:
                writer.writerow(result)

    def save_images(self, mask=None, file_prefix=None, file_postfix=''):
        # TODO create a new directory
        if self.images is None:
            raise RuntimeError('Images not initialized')
        for imageName in self.images.keys():
            filename = file_prefix if file_prefix is not None else self.get_filename()
            if len(filename) > 0 and filename[len(filename) - 1] != '_':
                filename += '_'
            if len(file_postfix) > 0 and file_postfix[0] != '_':
                file_postfix = '_' + file_postfix
            filename += imageName + file_postfix + '.nii.gz'
            mask = mask if mask is not None else self.mask
            ns.imageutils.save_img(self.images[imageName], filename=filename, masker=mask)


def get_image_means(metaexts, img_names, mask=None):
    """
    Get a mean for all of the voxel values in each image
    """
    if mask is not None:
        return [np.mean([np.array(metaext.images[img])[mask] for img in img_names], axis=1) for metaext in metaexts]
    else:
        return [np.mean([metaext.images[img] for img in img_names], axis=1) for metaext in metaexts]


def filenamer(info_dict):
    # TODO assign a name to each MetaExtension rather than a function
    """
    Goes together with the info_dict above
    """
    filename = get_shorthand_expression(info_dict['expr'])
    if 'contrary_expr' in info_dict:
        filename += '_vs_' + get_shorthand_expression(info_dict['contrary_expr'])
    return filename


def get_shorthand_expression(expression):
    word = expression.split(' ', 1)[0]
    if word[0] == '(':
        word = word[1:]
    return word


def analyze_expression(dataset, expression, prior=0.5, fdr=0.01, image_names=None, save_files=True):
    # TODO mask
    # TODO parameter += customized study ids, as an alternative to dataset.get_studies
    """
    Analyze a single expression, output a set of .nii.gz image files and a csv file containing voxel values in images
    :param dataset: a neurosynth Dataset instance to get studies from
    :param expression: a string expression to be analyzed
    :param priors: a list of float priors to be used when calculating conditional probabilities
                   The real prior will always be calculated and added to this list
    :param fdr: the FDR threshold to use when correcting for multiple comparisons
    :param image_names: the names of images to be included in the csv file. If None, all images will be included.
                        For images named 'pFgA_given_pF=0.xx', specifying 'pFgA_given_pF' will include all of them.
    :param save_files: a boolean whether or not to save the result as .csv and .nii.gz files
    :return: an MetaExtension object
    """
    # get studies
    print expression
    try:
        studySet = dataset.get_studies(expression=expression)
    except AttributeError:
        studySet = dataset.get_studies(features=expression)  # in case expression doesn't work

    process_image_names(image_names, prior, fdr)
    # analyze
    meta = ns.meta.MetaAnalysis(dataset, studySet, prior=prior, q=fdr)
    metaExt = MetaExtension(info=create_info_dict(expression, len(studySet)), meta_analysis=meta,
                            filenamer_func=filenamer)
    # output
    if save_files:
        metaExt.write_images_to_csv(get_shorthand_expression(expression) + '_output.csv', image_names=image_names)
        metaExt.save_images(dataset.masker)
    return metaExt


def analyze_all_terms(dataset, extra_expr=()):
    """
    Generate a MetaExtension object for each term/expression in the dataset and the given extra expression list
    :return: a tuple (a list of MetaExtensions, a list of sorted image names)
    """
    metaexts = [analyze_expression(dataset, term, priors=[0.5], save_files=False)
                for term in dataset.get_feature_names() if not term[0].isdigit()]
    for extra in extra_expr:
        metaexts.append(analyze_expression(dataset, extra, priors=[0.5], save_files=False))

    img_names = metaexts[0].images.keys()
    img_names.sort()
    return metaexts, img_names
