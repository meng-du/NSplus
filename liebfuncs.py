"""Further Neurosynth tools for use in our lab

v0.1 - added count_voxels_z, count_voxels_pp, voxel_file
        began compare_terms_pairs and compare_terms_group"""


from neurosynth import Dataset, meta, network, decode
from neurosynth.base import imageutils
import numpy as np
import pandas
import operator
import random
from decimal import *

def count_voxels_z(some_meta):
    """Count the number of voxels that have significant z-score in given meta analysis
    Args: some_meta - some meta analysis for which you want to count the z-scores
    Returns: dict with number of significant z-score voxels in each z-score image
    """
    
    z_images = ['pAgF_z', 'pFgA_z', ('pAgF_z_FDR_%s' %some_meta.threshold), 
        ('pFgA_z_FDR_%s' %some_meta.threshold)]
    z_vox_count = {}
    for k in z_images:
        z_vox_count[k] = np.count_nonzero(some_meta.images.get(k))
    return z_vox_count

 
def count_voxels_pp(some_meta, prob=None):
    """If method is called with only a meta argument defined, will count the number of 
            voxels with a probability that is greater than the prior probability given 
            to the meta object. If method is also called with a prob argument, will count
            the number of voxels with a probability that is greater than this argument 
            value.
        Args: some_meta - some meta analysis for which you want to count the posterior probabilities
              prob - Default set to the prior probability provided to meta object. Must be
                    an int, float, or long that is between 0 and 1. 
        Returns: dict with number of voxels showing a posterior probability over the provided
                    value in each probability image
    """
    
    if prob==None:
        prob=some_meta.prior
    p_images = [('pAgF_given_pF%s' %some_meta.prior), ('pFgA_given_pF%s' %some_meta.prior)]
    p_voxel_count = {}
    if not isinstance(prob, (int, float, long)) or not 0<=prob<=1:
        raise TypeError('Prob argument must be a number between 0 and 1')
    else:
        for k in p_images:
            p = np.array(some_meta.images.get(k))
            p_vox_count[k] = len(p[np.where(p>prob)])
        return p_vox_count
        
        
def voxel_dataframe(comparisons, compnames, maps):
    """Creates a dataframe that displays the z and/or pp values for each voxel in each
        provided image.
        Args: comparisons - list of meta analyses to include in one dataframe
                            e.g. [meta_1, meta_2, ... meta_n]
              compnames - string names of the comparisons you want to show up in the dataframe.
                            Must be in the same order as the comparisons list
              maps - list of maps to include in spreadsheet
                            e.g. ['pFgA_z', 'pFgA_given_pF0.5']
        Returns: dataframe 
    """
    
    df_dict = {}
    df = pandas.DataFrame()
    
    #for each comparison meta analysis in the comparison list, add the maps from the map 
    #list to df_dict
    for c in zip(comparisons, compnames):
        for m in maps:
            if m in c[0].images:
                colname = c[1] + '_' + m
                df_dict[colname] = pandas.Series(c[0].images[m])
    
    #return full dataframe
    df = pandas.DataFrame(df_dict)
    return df
    
    
def compare_terms_pairs(dataset, term_list_a, term_list_b, maps, name, sampling=1, return_images=True,
    even_studies=True, real_priors=True):
    """1. Finds the studies corresponding to each term in term lists in dataset
       2. For each item in term_list_a, compare to each item in term_list_b
       3. For each comparison, count the number of studies for each term. If even_studies 
            is True, then take a random sample of studies so that each term contains an even
            number of studies. 
       4. Do a vs. b and b vs. a meta analyses
       5. Put those analyses into a voxel file dataframe
       6. If sampling is greater than 1, repeat x number of times and put all dataframes into 
            a Panel
       7. Take average value for each voxel across all dataframes in panel, and output that 
            average dataframe 
        Args: dataset - dataset of studies to use in meta analyses
              term_list_a - terms to compare (strings)
              term_list_b - terms to be compared to (strings)
              maps - list of maps to include in final spreadsheet (pp maps must have 4 digits
                            after the decimal point if not forcing 0.5, and must know the priors
                            for every analysis you want to get back in the .txt file)
              name - string name of final output file
              sampling - number of times to run the analyses, after which the average value
                            will be returned in the final spreadsheet
              return_images - whether or not to also output average nii.gz brain maps for each analysis
              even_studies - whether or not the program should randomly select studies so
                            the compared terms have the same number of studies per analysis
              real_priors - whether or not priors should reflect real study numbers going into
                            the analysis, or if the priors should be forced to be 0.5
        Returns: .txt file and optionally nii.gz file
                            
    """
    
    #find studies corresponding to each term in term list in dataset
    study_dict = {}
    study_num = {}
    study_dict_reduce = {}
    study_num_reduce = {}
    all_samplings = {}
    e11list = []
    for a in term_list_a:
        for b in term_list_b:
            expr1 = a + ' &~ ' + b
            expr2 = b + ' &~ ' + a
            study_dict[(a,b)] = dataset.get_studies(expression=expr1)
            study_dict[(b,a)] = dataset.get_studies(expression=expr2)
            study_num[(a,b)] = len(study_dict[(a,b)])
            study_num[(b,a)] = len(study_dict[(b,a)])
            
               
    #Create terma vs. termb and termb vs. terma meta analyses. In each kind of 
    #brain map specified, add the voxel values from these maps for each meta analysis 
    #to a dataframe. Then repeat this "sampling" number of times, and average across 
    #all the dataframes.
    for s in range(sampling):
        print s + 1
        metas = []
        metanames = []
        for a in term_list_a:
            for b in term_list_b:
                if even_studies:
                    #find the term with the fewest studies in each pairing, and reduce the other
                    #term list to that number by randomly sampling from its set of studies
                    if study_num[(a,b)] > study_num[(b,a)]:
                        study_dict_reduce[(a,b)] = random.sample(study_dict[(a,b)], study_num[(b,a)])
                        study_dict_reduce[(b,a)] = study_dict[(b,a)]
                        study_num_reduce[(a,b)] = study_num[(b,a)]
                        study_num_reduce[(b,a)] = study_num[(b,a)]
                    else:
                        study_dict_reduce[(b,a)] = random.sample(study_dict[(b,a)], study_num[(a,b)])
                        study_dict_reduce[(a,b)] = study_dict[(a,b)]
                        study_num_reduce[(b,a)] = study_num[(a,b)]
                        study_num_reduce[(a,b)] = study_num[(a,b)]
                else:
                    study_dict_reduce[(a,b)] = study_dict[(a,b)]
                    study_dict_reduce[(b,a)] = study_dict[(b,a)]
                    study_num_reduce[(a,b)] = study_num[(a,b)]
                    study_num_reduce[(b,a)] = study_num[(b,a)]
            
                #set assigned priors
                prior1 = 0.5
                prior2 = 0.5
                if real_priors:
                    ttl = study_num_reduce[(a,b)] + study_num_reduce[(b,a)]
                    prior1 = round(Decimal(study_num_reduce[(a,b)]/ttl),4)
                    prior2 = round(Decimal(study_num_reduce[(b,a)]/ttl),4)
                
                a_v_b = meta.MetaAnalysis(dataset, study_dict_reduce[(a,b)], study_dict_reduce[(b,a)], prior=prior1)
                b_v_a = meta.MetaAnalysis(dataset, study_dict_reduce[(b,a)], study_dict_reduce[(a,b)], prior=prior2)
                meta_name1 = a + '_v_' + b + str(study_num_reduce[(a,b)])
                meta_name2 = b + '_v_' + a + str(study_num_reduce[(b,a)])
                metas.append(a_v_b)
                metas.append(b_v_a)
                metanames.append(meta_name1)
                metanames.append(meta_name2)
        all_samplings[s] = voxel_dataframe(metas, metanames, maps)
        
    #make panels of voxel values, find average (represented as a single dataframe)
    if sampling>1:
        dp = pandas.Panel(all_samplings)
        mean_df = dp.mean(axis=0, skipna=True)
    else:
        mean_df = pandas.DataFrame(all_samplings[0])
    
    #return spreadsheet of average voxel values
    name = name + '.txt'
    mean_df.to_csv(name, sep='\t')
    
    #return average nii.gz brain maps
    if return_images:
        files = mean_df.columns.values.tolist()
        for k in files:
            imageutils.save_img(mean_df[k], k+'.nii.gz', dataset.masker)       
            
    
    
def compare_terms_group(dataset, term_list, maps, name, sampling=1, return_images=True):
    """1. Finds the studies corresponding to each term in term list in dataset
       2. For each term, count the number of studies. Then take a random sample of studies 
            so that each term contains an even number of studies. 
       3. For each item in term_list, compare to the group of studies with the other terms 
       4. Do term vs. group and group vs. term meta analyses (no thresholding or specific voxel seed)
       5. Put those analyses into a voxel file dataframe
       6. If sampling is greater than 1, repeat x number of times and put all dataframes into 
            a Panel
       7. Take average value for each voxel across all dataframes in panel, and output that 
            average dataframe 
        Args: dataset - dataset of studies to use in meta analyses
              term_list - terms to compare (strings)
              maps - list of maps to include in final spreadsheet. If some maps exist in only 
                    some meta analyses, list all potential maps and the spreadsheet will return
                    which of those maps exist for each meta analysis
              name - string name of final output file
              sampling - number of times to run the analyses, after which the average value
                            will be returned in the final spreadsheet
              returnmaps - whether or not to also output average nii.gz brain maps for each analysis
        Returns: .txt file and optionally nii.gz file
                            
    """
    
    #find studies corresponding to each term in term list in dataset
    study_dict = {}
    study_num = {}
    study_dict_reduce = {}
    study_num_reduce = {}
    ind = 0
    for t in term_list:
        if ind==0:
            otherterms = '(' + ' | '.join(term_list[ind+1:]) + ')'
        elif ind==len(term_list)-1:
            otherterms = '(' + ' | '.join(term_list[:ind]) + ')'
        else:
            otherterms = '(' + ' | '.join(term_list[:ind]) + ' | ' + ' | '.join(term_list[ind+1:]) + ')'
        expr = t + ' &~ ' + otherterms
        study_dict[t] = dataset.get_studies(expression=expr)
        study_num[t] = len(study_dict[t])
        ind += 1
        
    #Find the term with the fewest associated studies, and randomly sample from the rest so
    #every term is a set of the same number of studies
    min = 10000
    for x in study_num:
        if study_num[x]<min:
            min=study_num[x]
            
    #Create term vs. others and others vs. term meta analyses. In each kind of brain map 
    #specified, add the voxel values from these maps for each meta analysis to a dataframe.
    #Then repeat this "sampling" number of times, and average across all the dataframes. 
    all_samplings = {}
    print 'number of study samplings:'
    for s in range(sampling):
        print s
        for r in study_dict:
            study_dict_reduce[r] = random.sample(study_dict[r], min)
        metas = []
        metanames = []
        for m in study_dict_reduce:
            bunch = []
            for w in study_dict_reduce:
                if w!=m:
                    bunch = bunch + study_dict_reduce[w]
            term_v_bunch = meta.MetaAnalysis(dataset, study_dict_reduce[m], bunch, prior=round(Decimal(1.0/len(term_list)),4))
            bunch_v_term = meta.MetaAnalysis(dataset, bunch, study_dict_reduce[m], prior=round(Decimal(1-(1.0/len(term_list))),4))
            meta_name1 = m + '_v_bunch' + str(min)
            meta_name2 = 'bunch_v_' + m + str(min)
            metas.append(term_v_bunch)
            metas.append(bunch_v_term)
            metanames.append(meta_name1)
            metanames.append(meta_name2)
        all_samplings[s] = voxel_dataframe(metas, metanames, maps)
    
    #make panels of voxel values, find average (represented as a single dataframe)
    dp = pandas.Panel(all_samplings)
    mean_df = dp.mean(axis=0, skipna=True)

    #return spreadsheet of average voxel values
    name = name + '.txt'
    mean_df.to_csv(name, sep='\t')
    
    #return average nii.gz brain maps
    if return_images:
        files = mean_df.columns.values.tolist()
        for k in files:
            imageutils.save_img(mean_df[k], k +'.nii.gz', dataset.masker)







if __name__ == '__main__':
    filePath = 'current_data/dataset.pkl'
    dataset = Dataset.load(filePath)
    compare_terms_pairs(dataset,
                        ['emotion'],
                        ['pain', 'memory', 'language'],
                        maps=['pA_pF_emp_prior', 'pFgA_emp_prior', 'pAgF', 'consistency_z_FDR_0.01', 'consistency_z',
                              'specificity_z_FDR_0.01', 'specificity_z', 'pFgA_emp_prior_FDR_0.01'],
                        name='out',
                        even_studies=False)
