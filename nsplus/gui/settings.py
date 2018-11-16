from __future__ import absolute_import, print_function
from .globals import Global
from .pagebuilder import PageBuilder
from sys import version_info
import re
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename, askdirectory
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename, askdirectory


class SettingsPage(tk.Frame, PageBuilder):
    def __init__(self, parent, **kwargs):
        super(SettingsPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = '<Settings>'
        row_i = -1

        # roi mask
        #   instruction label
        row_i += 1
        tk.Label(self, text='Load an ROI mask:') \
            .grid(row=row_i, padx=10, pady=(25, 2), sticky=tk.W)
        #   browse button
        tk.Button(self,
                  command=self.load_roi_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, padx=(160, 0), pady=(23, 0), sticky=tk.W)
        tk.Button(self,
                  command=lambda: Global().use_default_roi(),
                  text=' Use default (whole brain) ',
                  highlightthickness=0) \
            .grid(row=row_i, padx=(250, 0), pady=(23, 0), sticky=tk.W)
        #   file name label
        row_i += 1
        self.label_roi_file = tk.Label(self,
                                       text='(default) ' + Global().default_roi,
                                       font=('Menlo', 12), fg='#424242',
                                       width=80, anchor='w')
        self.label_roi_file.grid(row=row_i, padx=15)

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, sticky='we', padx=10, pady=25)

        # output directory
        #   instruction label
        row_i += 1
        tk.Label(self, text='Output directory:') \
            .grid(row=row_i, padx=10, pady=2, sticky=tk.W)
        #   browse button
        tk.Button(self,
                  command=self.get_outdir_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, padx=(140, 0), sticky=tk.W)
        #   directory label
        row_i += 1
        self.label_outdir = tk.Label(self, text=Global().outpath,
                                     font=('Menlo', 12), fg='#424242',
                                     width=80, anchor='w')
        self.label_outdir.grid(row=row_i, padx=15)

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, sticky='we', padx=10, pady=25)

        # fdr
        row_i += 1
        tk.Label(self, text='False discovery rate when '
                            'correcting for multiple comparisons:') \
            .grid(row=row_i, padx=10, pady=2, sticky='w')
        self.entry_fdr, self.btn_fdr = self.add_controlled_entry(
            row_i, width=5, padx=(0, 40), sticky=tk.E,
            entry_val=Global().fdr,
            btn_func=lambda: self.entry_control(
                self.entry_fdr, self.btn_fdr, Global().fdr, Global().set_fdr))

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, sticky='we', padx=10, pady=25)

        # customize terms
        row_i += 1
        tk.Label(self, text='Add a custom term:') \
            .grid(row=row_i, padx=10, pady=2, sticky=tk.W)
        row_i += 1
        tk.Label(self, text='Enter your term:') \
            .grid(row=row_i, padx=20, pady=2, sticky=tk.W)
        row_i += 1
        self.entry_term = tk.Entry(self, width=60)
        self.entry_term.grid(row=row_i, padx=20, pady=(2, 10), sticky=tk.W)
        row_i += 1
        tk.Label(self, text='Enter study IDs, separated by comma:') \
            .grid(row=row_i, padx=20, pady=2, sticky=tk.W)
        row_i += 1
        self.entry_ids = tk.Entry(self, width=60)
        self.entry_ids.grid(row=row_i, padx=20, pady=(2, 10), sticky=tk.W)
        row_i += 1
        tk.Button(self, text=' Add term ', command=self.add_custom_term) \
            .grid(row=row_i, padx=20, sticky=tk.W)
        tk.Button(self, text=' Show all custom terms ',
                  command=self.show_custom_terms) \
            .grid(row=row_i, padx=(100, 0), sticky=tk.W)

    def add_custom_term(self):
        # error checking
        term = self.entry_term.get()
        term = term.strip()
        if len(re.findall('[^a-zA-Z0-9 ]', term)) > 0:
            Global().show_error('Invalid character in term.')
            return
        ids = self.entry_ids.get()
        if len(re.findall('[^0-9, ]', ids)) > 0:
            Global().show_error('Invalid character in study IDs.')
            return
        if len(term) == 0 or len(ids) == 0:
            return
        # add to dataset
        try:
            ids = [int(i) for i in ids.split(',')]
            valid_ids = Global().dataset.add_custom_term(term, ids)
        except ValueError as e:
            Global().show_error(e)
            return
        Global().update_ac_lists(term)  # add to autocomplete lists
        Global().update_status('Added term "%s" with %d studies.' % (term, len(valid_ids)),
                               is_ready=True)
        self.entry_term.delete(0, tk.END)
        self.entry_ids.delete(0, tk.END)

    def show_custom_terms(self):
        if len(Global().dataset.custom_terms) == 0:
            Global().update_status(status='Nothing yet!',
                                   is_ready=True, user_op=True)
            return
        win = tk.Toplevel(Global().root)
        win.title('Custom Terms')
        row = -1
        for term in Global().dataset.custom_terms:
            row += 1
            tk.Label(win, text=term) \
                .grid(row=row, padx=10, pady=(5, 1), sticky=tk.W)
            row += 1
            entry = tk.Entry(win, width=30)
            entry.grid(row=row, padx=20, pady=(1, 10))
            ids = ','.join([str(i) for i in Global().dataset.custom_terms[term]])
            entry.insert(tk.END, ids)
            entry.config(state='readonly')

    def get_outdir_from_button(self):
        outdir = askdirectory(initialdir=Global().outpath)
        if len(outdir) > 0:
            Global().outpath = outdir
            self.label_outdir.config(text=outdir)

    def load_roi_from_button(self):
        # get filename
        roi_filename = askopenfilename(initialdir='./',
                                       title='Select ROI file',
                                       filetypes=(('NIFTI files', '*.nii'),
                                                  ('NIFTI files', '*.gz'),
                                                  ('all files', '*.*')))
        if len(roi_filename) > 0:
            Global().roi_filename = roi_filename
            self.label_roi_file.config(text=Global().get_roi_name(with_ext=True))
        else:
            return

        Global().load_roi(self.label_roi_file)
