from __future__ import absolute_import, print_function
from .analysis import AnalysisPage
from .ranking import RankingPage
from .globals import Global
from threading import Thread
import os
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename, askdirectory
    import tkMessageBox as messagebox
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename, askdirectory
    from tkinter import messagebox


class ComparisonPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(ComparisonPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Comparison'
        row_i = -1


class MainApp(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(MainApp, self).__init__(parent, **kwargs)
        self.parent = parent

        parent.title('NeuroSynth+')
        # parent.geometry('350x200')

        # notebook layout
        row_i = 0
        self.notebook = ttk.Notebook(self)
        self.nb_pages = [RankingPage(self.notebook),
                         AnalysisPage(self.notebook),
                         ComparisonPage(self.notebook)]
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.grid(row=row_i)

        # roi mask
        self.defult_roi = '(default) MNI152_T1_2mm_brain.nii.gz'
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
                  command=self.use_default_roi,
                  text=' Use default (whole brain) ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(250, 0), pady=(8, 0), sticky='w')
        #   file name label
        row_i += 1
        self.label_filename = tk.Label(self, text=self.defult_roi, font=('Menlo', 12),
                                       fg='#424242', width=80, anchor='w')
        self.label_filename.grid(row=row_i, column=0, padx=15)

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
            self.label_filename.config(text=os.path.split(Global().roi_filename)[1])
        else:
            return

        self.load_roi()

    def load_roi(self):
        Thread(target=self._load_roi, args=[Global().roi_filename]).start()

        def after_loading_roi():
            roi = Global().roi_filename or self.defult_roi.split()[1]
            Global().update_status(status='Done. ROI %s loaded.' % roi, is_ready=True)
            Global().root.unbind('<<Done_loading_roi>>')

        Global().root.bind('<<Done_loading_roi>>', after_loading_roi)

    def _load_roi(self, roi_filename):
        if not Global().update_status(status='Loading ROI...', is_ready=False, user_op=True):
            return
        Global().update_status('Loading ROI...', is_ready=False)
        Global().dataset.mask(roi_filename)
        Global().update_status(is_ready=True)
        Global().root.event_generate('<<Done_loading_roi>>')  # trigger event

    def use_default_roi(self):
        Global().roi_filename = None
        self.label_filename.config(text=self.defult_roi)
        self.load_roi()


def main_gui():
    gui_started = False
    try:
        root = tk.Tk()
        main_app = MainApp(root)
        main_app.pack(side='top', fill='both')
        Global(root, main_app)
        # load NeuroSynth database in another thread
        Thread(target=Global.load_pkl_database, args=[Global()]).start()
        # start GUI
        gui_started = True
        root.mainloop()
    except Exception as e:
        if gui_started:
            Global().show_error(e)
        else:
            messagebox.showerror('Error', str(e))


if __name__ == '__main__':
    main_gui()
