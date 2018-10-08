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
        self.nb_label = 'Settings'
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
        self.label_roi_file = tk.Label(self, text='', font=('Menlo', 12),
                                       fg='#424242', width=80, anchor='w')
        self.label_roi_file.grid(row=row_i, column=0, padx=15)

        # separator
        row_i += 1
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=row_i, column=0)

        # output directory
        #   instruction label
        row_i += 1
        tk.Label(self, text='Output directory:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   browse button
        tk.Button(self,
                  command=self.get_outdir_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(140, 0), pady=(8, 0), sticky='w')
        #   directory label
        row_i += 1
        self.label_outdir = tk.Label(self, text='', font=('Menlo', 12),
                                     fg='#424242', width=80, anchor='w')
        self.label_outdir.grid(row=row_i, column=0, padx=15, pady=(0, 10))

    def get_outdir_from_button(self):
        outdir = askdirectory(initialdir=Global().outdir)
        if len(outdir) > 0:
            Global().outdir = outdir
            self.label_outdir.config(text=outdir)

    def load_roi_from_button(self):
        # get filename
        roi_filename = askopenfilename(initialdir='./',
                                       title='Select mask file',
                                       filetypes=(('NIFTI files', '*.nii'),
                                                  ('NIFTI files', '*.nii.gz'),
                                                  ('all files', '*.*')))
        if len(roi_filename) > 0:
            Global().roi_filename = roi_filename
            self.label_roi_file.config(text=os.path.split(Global().roi_filename)[1])
        else:
            return

        Global().load_roi()
