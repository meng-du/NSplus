from __future__ import absolute_import, print_function
from .globals import Global
import os
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename, askdirectory
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename, askdirectory


class SettingsPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(SettingsPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = '<Settings>'
        row_i = -1

        # roi mask
        #   instruction label
        row_i += 1
        tk.Label(self, text='Load an ROI mask:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   browse button
        tk.Button(self,
                  command=self.load_roi_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(160, 0), pady=(8, 0), sticky='w')
        tk.Button(self,
                  command=lambda: Global().use_default_roi(),
                  text=' Use default (whole brain) ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(250, 0), pady=(8, 0), sticky='w')
        #   file name label
        row_i += 1
        self.label_roi_file = tk.Label(self,
                                       text='(default) ' + Global().default_roi,
                                       font=('Menlo', 12), fg='#424242',
                                       width=80, anchor='w')
        self.label_roi_file.grid(row=row_i, column=0, padx=15)

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, column=0, sticky='we', padx=10, pady=15)

        # output directory
        #   instruction label
        row_i += 1
        tk.Label(self, text='Output directory:') \
            .grid(row=row_i, column=0, padx=10, pady=2, sticky='w')
        #   browse button
        tk.Button(self,
                  command=self.get_outdir_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(140, 0), sticky='w')
        #   directory label
        row_i += 1
        self.label_outdir = tk.Label(self, text=Global().outdir,
                                     font=('Menlo', 12), fg='#424242',
                                     width=80, anchor='w')
        self.label_outdir.grid(row=row_i, column=0, padx=15)

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, column=0, sticky='we', padx=10, pady=15)

        # fdr
        row_i += 1
        tk.Label(self, text='False discovery rate when '
                            'correcting for multiple comparisons:') \
            .grid(row=row_i, column=0, padx=10, pady=2, sticky='w')
        self.entry_fdr = tk.Entry(self, width=5)
        self.entry_fdr.insert(tk.END, Global().fdr)
        self.entry_fdr.config(state=tk.DISABLED)
        self.entry_fdr.config(disabledbackground='#e0e0e0', disabledforeground='#6d6d6d')
        self.entry_fdr.grid(row=row_i, column=0, padx=(0, 110), sticky='e')
        self.entry_fdr.bind('<Return>', lambda e: self.change_fdr())
        self.btn_fdr = tk.Button(self, command=self.change_fdr, text=' Change ',
                                 highlightthickness=0)
        self.btn_fdr.grid(row=row_i, column=0, padx=(0, 30), sticky='e')

    def get_outdir_from_button(self):
        outdir = askdirectory(initialdir=Global().outdir)
        if len(outdir) > 0:
            Global().outdir = outdir
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
            self.label_roi_file.config(text=os.path.split(Global().roi_filename)[1])
        else:
            return

        Global().load_roi(self.label_roi_file)

    def change_fdr(self):
        if 'Change' in self.btn_fdr['text']:  # changing fdr
            self.entry_fdr.config(state=tk.NORMAL)
            self.btn_fdr.config(text=' Apply ')
        else:  # applying change
            new_fdr = self.entry_fdr.get()
            if Global().set_fdr(new_fdr):  # success
                self.entry_fdr.config(state=tk.DISABLED)
                self.btn_fdr.config(text=' Change ')
            else:  # error
                self.entry_fdr.delete(0, tk.END)
                self.entry_fdr.insert(tk.END, Global().fdr)
