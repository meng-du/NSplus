from __future__ import absolute_import, print_function
from ..src.datasetplus import DatasetPlus
from ..src import rank_terms, analyze_expression
from .autocomplete import AutocompleteEntry
import os
import re
from datetime import datetime
from threading import Thread, Lock
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


def load_roi(roi_filename):
    Global().dataset.mask(roi_filename)
    Global().root.event_generate('<<Done_roi>>')  # trigger event


def show_error(exception):
    Global().update_status('Error: ' + str(exception), is_error=True)
    raise exception


class AnalysisPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(AnalysisPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Analysis'
        row_i = -1

        # page contents
        # instruction label
        row_i += 1
        tk.Label(self, text='Enter term or expression:') \
            .grid(row=row_i, padx=10, pady=(10, 2), sticky='w')

        # term/expression entry
        row_i += 1
        self.ac_entry = AutocompleteEntry([], self, listboxLength=8, width=55,
                                          matchesFunction=AnalysisPage.matches_term,
                                          setFunction=AnalysisPage.set_selection)
        self.ac_entry.grid(row=row_i, padx=15, pady=(2, 10))

        def update_ac_list(event):  # do it after database loaded
            self.ac_entry.autocompleteList = Global().dataset.get_feature_names()
        self.parent.master.parent.bind('<<Database_loaded>>', update_ac_list)

        # analyze button
        row_i += 1
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Analyze ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, padx=10, pady=(130, 10))

    def start(self):
        if not os.path.isdir(Global().outdir):
            messagebox.showerror('Error', 'Please select a valid output directory')
            return
        expression = self.ac_entry.get()

        if not Global().update_status('Analyzing "%s"...' % expression, user_op=True):
            return

        def _analyze():
            try:
                analyze_expression(Global().dataset, expression, outdir=Global().outdir)
                Global().root.event_generate('<<Done_analysis>>')  # trigger event
            except Exception as e:
                show_error(e)

        Thread(target=_analyze).start()
        Global().root.bind('<<Done_analysis>>',
                           lambda e: Global().update_status('Done. Files are saved to ' + Global().outdir))

    @staticmethod
    def matches_term(field_value, ac_list_entry):
        last_word = re.findall(r'[a-zA-Z0-9 ]+$', field_value)
        if len(last_word) == 0:
            return False
        last_word = last_word[0].lstrip()
        pattern = re.compile(re.escape(last_word) + '.*', re.IGNORECASE)
        return re.match(pattern, ac_list_entry)

    @staticmethod
    def set_selection(field_value, ac_list_entry):
        last_word_index = [m.start() for m in re.finditer(r'[a-zA-Z0-9 ]+$', field_value)]
        if len(last_word_index) == 0:
            return field_value
        last_word_index = last_word_index[0]
        while field_value[last_word_index].isspace():  # strip whitespace
            last_word_index += 1
        return field_value[:last_word_index] + ac_list_entry


class ComparisonPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(ComparisonPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Comparison'
        row_i = -1


class RankingPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(RankingPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Ranking'
        self.roi_filename = ''
        row_i = -1

        # page contents
        # 1 mask selection
        #   instruction label
        row_i += 1
        tk.Label(self, text='Select an ROI mask:') \
            .grid(row=row_i, column=0, padx=10, pady=(10, 2), sticky='w')
        #   browse button
        tk.Button(self,
                  command=self.get_filename_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=row_i, column=0, padx=(160, 0), pady=(8, 0), sticky='w')
        #   file name label
        row_i += 1
        self.label_filename = tk.Label(self, text='', font=('Menlo', 12),
                                       fg='#424242', width=60, anchor='w')
        self.label_filename.grid(row=row_i, column=0, columnspan=2, padx=5)

        # 2 image selection
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

        # 3 procedure selection
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
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Start Ranking ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, columnspan=2, padx=1, pady=20)

    def get_filename_from_button(self):
        self.roi_filename = askopenfilename(initialdir='./',
                                            title='Select mask file',
                                            filetypes=(('NIFTI files', '*.nii'),
                                                       ('NIFTI files', '*.nii.gz'),
                                                       ('all files', '*.*')))
        self.label_filename.config(text=self.roi_filename.split('/')[-1])

    def start(self):
        """
        Load ROI and then call the rank method
        """
        if not os.path.isdir(Global().outdir):
            messagebox.showerror('Error', 'Please select a valid output directory')
            return
        meta_img = self.img_var.get()
        procedure = self.proc_var.get()

        # output file name
        if len(self.roi_filename) == 0:
            continuing = messagebox.askyesno('Warning',
                                             'You didn\'t specify an ROI file. '
                                             'Are you sure you want to continue?')
            if not continuing:
                return
            outfile_name = 'whole_brain_ranked_by_%s' % meta_img
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')
        else:
            _, roi_name = os.path.split(self.roi_filename)
            outfile_name = '%s_ranked_by_%s' % (roi_name.split('.')[0], meta_img)
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')

        if os.path.isfile(outfile):
            outfile_name += '_' + str(datetime.now()).split('.')[0] \
                .replace('-', '').replace(':', '').replace(' ', '_')
            outfile = os.path.join(Global().outdir, outfile_name + '.csv')

        # start running
        if len(self.roi_filename) == 0:
            self.run_rank(meta_img, procedure, outfile)
        else:
            # load ROI mask to database
            if not Global().update_status('Loading ROI...', user_op=True):
                return
            Thread(target=load_roi, args=[self.roi_filename]).start()
            # call rank() later
            Global().root.bind('<<Done_roi>>',
                               lambda e: self.run_rank(meta_img, procedure, outfile))

    def run_rank(self, selected_meta, selected_proc, csv_name):
        Global().root.unbind('<<Done_roi>>')
        if not Global().update_status('Analyzing terms...',
                                      user_op=(len(self.roi_filename) == 0)):
            return

        def _rank():
            try:
                rank_terms(Global().dataset, rank_by=selected_meta, rank_first=selected_proc,
                           csv_name=csv_name)  # ranking
                Global().root.event_generate('<<Done_ranking>>')  # trigger event
            except Exception as e:
                show_error(e)

        Thread(target=_rank).start()
        Global().root.bind('<<Done_ranking>>',
                           lambda e: Global().update_status('Done. A file is saved to ' + csv_name))


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


class Global(Singleton):
    """
    A class that maintains the NeuroSynth dataset instance and the current app status
    """
    def __init__(self, root, app, **kwargs):
        self.root = root
        self.status = 'Ready'
        self.has_error = False
        self.history = []
        self.dataset = None
        self.status_mutex = Lock()
        self.outdir = os.path.expanduser('~')
        app.label_outdir.config(text=self.outdir)

        # GUI
        self.statusbar = tk.Frame(root, **kwargs)
        self.text_width = 80
        self.statusbar_label = tk.Label(root, text=self.status.ljust(self.text_width),
                                        bd=1, relief=tk.SUNKEN, anchor='w', padx=3,
                                        font=('Menlo', 12), bg='#6d6d6d', fg='#d6d6d6')
        self.statusbar_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, status, is_error=False):  # not thread safe
        self.status = status
        self.has_error = is_error
        self.history.append(status)
        if len(status) > self.text_width:
            statusbar_text = status[:(self.text_width - 3)] + '...'
        else:
            statusbar_text = status.ljust(self.text_width)
        text_color = '#ff0000' if is_error else '#e3e3e3'
        if status == 'Ready':
            text_color = '#90ee90'
        self.statusbar_label.config(text=statusbar_text, fg=text_color)

    def update_status(self, status='Ready', is_error=False, user_op=False):  # thread safe
        """
        :param status: string
        :param is_error: (boolean) the text will show as red if True
        :param user_op: (boolean) whether a status change is requested by user.
                        If True and the current status is not 'Ready', the request will
                        be declined, in which case this function returns False and the
                        status bar shows a warning
        :return: (boolean) whether the status has been updated successfully
        """
        prev = False
        with self.status_mutex:
            if (not user_op) or self.is_ready():
                self._update_status(status, is_error)
            else:
                prev = self.status, self.has_error
                self._update_status('Another task is running... Please try again later',
                                    is_error=True)

        def back_to_prev(prev_status, prev_has_error):
            # show error for 2 seconds and then go back to the previous status
            with self.status_mutex:
                if not self.is_ready():  # last task still running
                    self._update_status(prev_status, is_error=prev_has_error)

        if prev:
            self.statusbar.after(2000, back_to_prev, *prev)

        return not bool(prev)

    def is_ready(self):
        return self.status == 'Ready' or self.status.startswith('Done')

    def load_pkl_database(self):
        """
        Call this function after a Global instance has been initiated
        """
        try:
            self.update_status('Loading database...')
            self.dataset = DatasetPlus.load_default_database()
            self.update_status()
            self.root.event_generate('<<Database_loaded>>')  # trigger event
        except Exception as e:
            messagebox.showerror('Error: failed to load database', str(e))
            self.update_status('Error: failed to load database. ' + str(e), is_error=True)


class MainApp(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(MainApp, self).__init__(parent, **kwargs)
        self.parent = parent

        parent.title('NeuroSynth+')
        # parent.geometry('350x200')

        # notebook layout
        self.notebook = ttk.Notebook(self)
        self.nb_pages = [RankingPage(self.notebook),
                         AnalysisPage(self.notebook),
                         ComparisonPage(self.notebook)]
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.grid(row=0)

        # output directory
        #   instruction label
        tk.Label(self, text='Output directory:') \
            .grid(row=1, column=0, padx=10, pady=(10, 2), sticky='w')
        #   browse button
        tk.Button(self,
                  command=self.get_outdir_from_button,
                  text=' Browse ',
                  highlightthickness=0) \
            .grid(row=1, column=0, padx=(140, 0), pady=(8, 0), sticky='w')
        #   directory label
        self.label_outdir = tk.Label(self, text='', font=('Menlo', 12),
                                     fg='#424242', width=80, anchor='w')
        self.label_outdir.grid(row=2, column=0, padx=12, pady=(0, 10))

    def get_outdir_from_button(self):
        Global().outdir = askdirectory(initialdir=Global().outdir)
        self.label_outdir.config(text=Global().outdir)


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
            show_error(e)
        else:
            messagebox.showerror('Error', str(e))


if __name__ == '__main__':
    main_gui()
