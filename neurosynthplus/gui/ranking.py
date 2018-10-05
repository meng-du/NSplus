from __future__ import absolute_import, print_function
from ..src.ranking import rank_terms
from .globals import Global
import os
from datetime import datetime
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import tkMessageBox as messagebox
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import messagebox


class RankingPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(RankingPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Ranking'
        row_i = -1

        # page contents
        # image selection
        #   instruction label
        row_i += 1
        tk.Label(self, text='Sort terms by:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   radio buttons
        self.image_labels = {
            'Forward inference with a uniform prior=0.5': 'pAgF_given_pF=0.50',
            'Forward inference z score (uniformity test)': 'uniformity-test_z',
            'Forward inference with multiple comparisons correction (FDR=0.01)': 'uniformity-test_z_FDR_0.01',
            'Reverse inference with a uniform prior=0.5': 'pFgA_given_pF=0.50',
            'Reverse inference z score (association test)': 'association-test_z',
            'Reverse inference with multiple comparisons correction (FDR=0.01)': 'association-test_z_FDR_0.01'
        }
        self.img_var = tk.StringVar(value='pFgA_given_pF=0.50')
        for text in self.image_labels.keys():
            row_i += 1
            tk.Radiobutton(self,
                           text=text,
                           variable=self.img_var,
                           value=self.image_labels[text]) \
                .grid(row=row_i, column=0, columnspan=2, padx=30, sticky='w')

        # procedure selection
        #   instruction label
        row_i += 1
        tk.Label(self, text='Procedure:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   radio buttons
        self.proc_var = tk.BooleanVar(value=False)  # whether to rank first
        for i, text in enumerate(['Average the values across ROI first, then rank terms',
                                  'Rank terms at each voxel first, then average ranks across ROI']):
            row_i += 1
            tk.Radiobutton(self,
                           text=text,
                           variable=self.proc_var,
                           value=bool(i)) \
                .grid(row=row_i, column=0, columnspan=2, padx=30, sticky='w')

        # run button
        row_i += 1
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Start Ranking ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, columnspan=2, padx=1, pady=20)

    def start(self):
        """
        Load ROI and then call the rank method
        """
        if not Global().valid_options():
            return

        meta_img = self.img_var.get()
        procedure = self.proc_var.get()

        # output file name
        if Global().roi_filename is None:
            continuing = messagebox.askyesno('Warning',
                                             'You didn\'t specify an ROI file. '
                                             'Are you sure you want to continue?')
            if not continuing:
                return
            outfile_name = 'whole_brain_ranked_by_%s' % meta_img
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')
        else:
            roi_name = os.path.split(Global().roi_filename)[1]
            outfile_name = 'masked_by_%s_ranked_by_%s' % (roi_name.split('.')[0], meta_img)
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')

        if os.path.isfile(outfile):
            outfile_name += '_' + str(datetime.now()).split('.')[0] \
                .replace('-', '').replace(':', '').replace(' ', '_')
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')

        # start ranking
        if not Global().update_status('Analyzing terms...', user_op=True):
            return

        def _rank():
            try:
                rank_terms(Global().dataset, rank_by=meta_img, rank_first=procedure,
                           csv_name=outfile)  # ranking
                Global().root.event_generate('<<Done_ranking>>')  # trigger event
            except Exception as e:
                Global().show_error(e)

        Thread(target=_rank).start()
        Global().root.bind('<<Done_ranking>>',
                           lambda e: Global().update_status('Done. A file is saved to ' + outfile))
