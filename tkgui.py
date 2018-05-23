import neurosynth as ns
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
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.nb_label = 'Ranking'
        self.roi_filename = None

        # page contents
        self.label_select = tk.Label(self, text='Select an ROI mask:')
        self.label_select.grid(row=0, column=0, padx=10, pady=(10, 2))

        self.btn_file = tk.Button(self,
                                  command=self.get_filename_from_button,
                                  text=' Browse ',
                                  highlightthickness=0)
        self.btn_file.grid(row=1, column=0, padx=10, pady=(2, 10))

        self.label_filename = tk.Label(self,
                                       text='',
                                       width=20)
        self.label_filename.grid(row=1, column=1, padx=(0, 10), sticky='w')

        self.btn_file = tk.Button(self,
                                  command=self.run,
                                  text=' Start Ranking ',
                                  highlightthickness=0)
        self.btn_file.grid(row=2, columnspan=2, padx=10, pady=10)

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
        if self.roi_filename is not None:
            # load ROI mask to database
            self.parent.dataset.masker = ns.mask.Masker(self.roi_filename)
            self.parent.dataset.create_image_table()
            if feature_filename is not None:
                self.add_features(feature_filename, **kwargs)


class StatusBar(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.status = 'Ready'
        self.statusbar = tk.Label(self, text=self.status, bd=1, relief=tk.SUNKEN, anchor='w')
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, status):
        self.status = status
        self.statusbar.config(text=status)

    def is_ready(self):
        return self.status == 'Ready'

    def ready_now(self):
        self.status = 'Ready'
        self.statusbar.config(text=self.status)


class MainApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        parent.title('NeuroSynth+')
        # parent.geometry('350x200')

        # notebook layout
        self.notebook = ttk.Notebook(parent)
        self.nb_pages = [RankingPage(self.notebook)]
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.pack(expand=1, fill='both')

        # tasks & status bar
        self.task_queue = []
        self.status = StatusBar(parent)

        # load NeuroSynth database
        self.dataset = self.load_database()

    def load_database(self, data_file='neurosynth_data/database.txt', *args, **kwargs):
        self.status.update_status('Loading database...')
        dataset = ns.Dataset(data_file, *args, **kwargs)
        self.status.ready_now()
        return dataset


def main():
    root = tk.Tk()
    MainApp(root).pack(side='top', fill='both')
    root.mainloop()


if __name__ == '__main__':
    main()
