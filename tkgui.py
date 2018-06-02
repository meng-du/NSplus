from datasetplus import DatasetPlus
import rank
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename
    import tkMessageBox as messagebox
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename
    from tkinter import messagebox


class RankingPage(tk.Frame):
    def __init__(self, parent, dataset, **kwargs):
        super(RankingPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.dataset = dataset
        self.nb_label = 'Ranking'
        self.roi_filename = None
        row_i = -1

        # page contents
        # 1 select mask
        #   instruction label
        row_i += 1
        tk.Label(self, text='Select an ROI mask:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   browse button
        row_i += 1
        tk.Button(self,
                  command=self.get_filename_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=10, pady=(2, 10))
        #   file name label
        self.label_filename = tk.Label(self, text='', width=20)
        self.label_filename.grid(row=row_i, column=1, padx=(0, 10), sticky='w')

        # 2 select image
        #   instruction label
        row_i += 1
        tk.Label(self, text='Rank terms by:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   radio buttons
        self.image_labels = {
            'Forward inference with a uniform prior=0.5': 'pAgF_given_pF=0.50',
            'Forward inference z score (consistency)': 'consistency_z',
            'Forward inference with multiple comparisons correction (FDR=0.05)': 'pAgF_z_FDR_0.05',
            'Reverse inference with a uniform prior=0.5': 'pFgA_given_pF=0.50',
            'Reverse inference z score (specificity)': 'specificity_z',
            'Reverse inference with multiple comparisons correction (FDR=0.05)': 'pFgA_z_FDR_0.05'
        }
        self.img_var = tk.StringVar(value='pFgA_given_pF=0.50')
        for text in self.image_labels.keys():
            row_i += 1
            tk.Radiobutton(self,
                           text=text,
                           variable=self.img_var,
                           value=self.image_labels[text]) \
                .grid(row=row_i, column=0, columnspan=2, padx=30, sticky='w')

        # 3 select procedure
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

        # 4 run button
        row_i += 1
        self.btn_file = tk.Button(self,
                                  command=self.run,
                                  text=' Start Ranking ',
                                  highlightthickness=0)
        self.btn_file.grid(row=row_i, columnspan=2, padx=1, pady=10)

    def get_filename_from_button(self):
        self.roi_filename = askopenfilename(initialdir='./',
                                            title='Select mask file',
                                            filetypes=(('NIFTI files', '*.nii'),
                                                       ('NIFTI files', '*.nii.gz'),
                                                       ('all files', '*.*')))
        self.label_filename.config(text=self.roi_filename.split('/')[-1])

    def run(self):
        if self.roi_filename is None:
            no_roi = messagebox.askyesno('Warning', 'You didn\'t specify an ROI file. '
                                                    'Are you sure you want to continue?')
            if not no_roi:
                return
        else:
            # load ROI mask to database
            Status().update_status('Loading ROI...')
            self.parent.dataset.mask(self.roi_filename)
            Status().update_status('Ranking terms...')
        selected_img = self.img_var.get()
        selected_proc = self.proc_var.get()
        out_filename = ''  # TODO
        rank.rank(self.dataset, rank_by=selected_img, rank_first=selected_proc,
                  csv_name=out_filename)
        Status().update_status('Done.')


class _Singleton(type):
    """
    Metaclass for singletons. See https://stackoverflow.com/a/6798042/3290263
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})): pass


class Status(Singleton):
    def __init__(self, parent, **kwargs):
        self.status = 'Ready'
        self.history = []

        # GUI
        self.statusbar = tk.Frame(parent, **kwargs)
        self.text_width = 50
        self.statusbar_label = tk.Label(parent, text=self.status.ljust(self.text_width),
                                        bd=1, relief=tk.SUNKEN, anchor='w',  padx=3,
                                        font=('Menlo', 12), bg='#6d6d6d', fg='#d6d6d6')
        self.statusbar_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, status='Ready', is_error=False):
        """
        :param status: string
        :param is_error: (boolean) the text will show as red if True
        """
        self.status = status
        self.history.append(status)
        if len(status) > self.text_width:
            statusbar_text = status[:(self.text_width - 3)] + '...'
        else:
            statusbar_text = status.ljust(self.text_width)
        if is_error:
            self.statusbar_label.config(text=statusbar_text, fg='#ff0000')
        else:
            self.statusbar_label.config(text=statusbar_text)

    def is_ready(self):
        return self.status == 'Ready'


class MainApp(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(MainApp, self).__init__(parent, **kwargs)
        self.parent = parent
        self.dataset = None

        parent.title('NeuroSynth+')
        # parent.geometry('350x200')

        # notebook layout
        self.notebook = ttk.Notebook(parent)
        self.nb_pages = [RankingPage(self.notebook, self.dataset)]
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.pack(expand=1, fill='both')

        # load NeuroSynth database
        # self.load_database()

    def load_database(self, data_file=None):
        """
        :param data_file: (string) path to a pickled data file
        """
        Status().update_status('Loading database...')
        if data_file is None:
            self.dataset = DatasetPlus.load_default_database()
        else:
            self.dataset = DatasetPlus.load(data_file)
        Status().update_status()


def main():
    # try:
    root = tk.Tk()
    main_app = MainApp(root)
    main_app.pack(side='top', fill='both')
    Status(root)
    root.mainloop()
    # except Exception as e:
    #     if status is None:
    #         messagebox.showerror('Error', str(e))
    #     else:
    #         status.update_status(str(e), is_error=True)


if __name__ == '__main__':
    main()
