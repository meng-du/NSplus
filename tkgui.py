from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename


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
                                  # highlightbackground='#ececec',
                                  highlightthickness=0)
        self.btn_file.grid(row=1, column=0, padx=10, pady=(2, 10))

        self.label_filename = tk.Label(self,
                                       text='',
                                       justify=tk.LEFT,
                                       # wraplength=200,
                                       width=20)
        self.label_filename.grid(row=1, column=1, padx=(0, 10))

        self.btn_file = tk.Button(self,
                                  command=self.run,
                                  text=' Start Ranking ',
                                  justify=tk.RIGHT,
                                  # highlightbackground='#ececec',
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
        pass


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


def main():
    root = tk.Tk()
    MainApp(root).pack(side='top', fill='both')
    root.mainloop()


if __name__ == '__main__':
    main()
