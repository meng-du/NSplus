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

    # find studies corresponding to each term in term list in dataset
    study_dict = {}
    study_num = {}
    study_dict_reduce = {}
    study_num_reduce = {}
    ind = 0
    for t in term_list:
        if ind == 0:
            otherterms = '(' + ' | '.join(term_list[ind + 1:]) + ')'
        elif ind == len(term_list) - 1:
            otherterms = '(' + ' | '.join(term_list[:ind]) + ')'
        else:
            otherterms = '(' + ' | '.join(term_list[:ind]) + ' | ' + ' | '.join(term_list[ind + 1:]) + ')'
        expr = t + ' &~ ' + otherterms
        study_dict[t] = dataset.get_studies(expression=expr)
        study_num[t] = len(study_dict[t])
        ind += 1

    # Find the term with the fewest associated studies, and randomly sample from the rest so
    # every term is a set of the same number of studies
    min = 10000
    for x in study_num:
        if study_num[x] < min:
            min = study_num[x]

    # Create term vs. others and others vs. term meta analyses. In each kind of brain map
    # specified, add the voxel values from these maps for each meta analysis to a dataframe.
    # Then repeat this "sampling" number of times, and average across all the dataframes.
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
                if w != m:
                    bunch = bunch + study_dict_reduce[w]
            term_v_bunch = meta.MetaAnalysis(dataset, study_dict_reduce[m], bunch,
                                             prior=round(Decimal(1.0 / len(term_list)), 4))
            bunch_v_term = meta.MetaAnalysis(dataset, bunch, study_dict_reduce[m],
                                             prior=round(Decimal(1 - (1.0 / len(term_list))), 4))
            meta_name1 = m + '_v_bunch' + str(min)
            meta_name2 = 'bunch_v_' + m + str(min)
            metas.append(term_v_bunch)
            metas.append(bunch_v_term)
            metanames.append(meta_name1)
            metanames.append(meta_name2)
        all_samplings[s] = voxel_dataframe(metas, metanames, maps)

    # make panels of voxel values, find average (represented as a single dataframe)
    dp = pandas.Panel(all_samplings)
    mean_df = dp.mean(axis=0, skipna=True)

    # return spreadsheet of average voxel values
    name = name + '.txt'
    mean_df.to_csv(name, sep='\t')

    # return average nii.gz brain maps
    if return_images:
        files = mean_df.columns.values.tolist()
        for k in files:
            imageutils.save_img(mean_df[k], k + '.nii.gz', dataset.masker)