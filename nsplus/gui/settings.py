from __future__ import absolute_import, print_function
from .globals import Global
from .pagebuilder import PageBuilder
from .autocompletepage import AutocompletePage
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


class SettingsPage(PageBuilder, AutocompletePage):
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
        tk.Label(self, text='Associate this term with:') \
            .grid(row=row_i, padx=20, sticky=tk.W)
        # term association radio button
        self.new_term_var = tk.BooleanVar(value=False)  # whether to do alias
        def term_association_onchange():
            is_alias = self.new_term_var.get()
            self.label_term_entry['text'] = self.term_entry_instr[int(is_alias)]
            if is_alias:
                self.ac_entry_custom.turn_on()
            else:
                self.ac_entry_custom.turn_off()
            self.ac_entry_custom.delete(0, tk.END)
        tk.Radiobutton(self, text='A list of study IDs', variable=self.new_term_var,
                       value=False, command=term_association_onchange) \
            .grid(row=row_i, padx=(195, 0), sticky=tk.W)
        tk.Radiobutton(self, text='Another term or expression', variable=self.new_term_var,
                       value=True, command=term_association_onchange) \
            .grid(row=row_i, padx=(340, 0), sticky=tk.W)
        row_i += 1
        self.term_entry_instr = ('Enter study IDs (separated by commas):',
                                 'Enter the term or expresion to be aliased:')
        self.label_term_entry = tk.Label(self, text=self.term_entry_instr[0])
        self.label_term_entry.grid(row=row_i, padx=20, sticky=tk.W)
        row_i += 1
        self.ac_entry_custom = self.create_labeled_ac_entry(row=row_i,
                                                            width=60,
                                                            padx=20,
                                                            pady=(0, 10),
                                                            label_text=None)[0]
        self.ac_entry_custom.turn_off()
        row_i += 1
        tk.Button(self, text=' Add term ', command=self.add_custom_term) \
            .grid(row=row_i, padx=20, sticky=tk.W)
        tk.Button(self, text=' Show all custom terms ',
                  command=self.show_custom_terms) \
            .grid(row=row_i, padx=(100, 0), sticky=tk.W)

    def add_custom_term(self):
        # new term error checking
        new_term = self.entry_term.get().strip()
        if len(new_term) == 0:
            Global().show_error('New term cannot be empty.')
            return
        if len(re.findall('[^a-zA-Z0-9 ]', new_term)) > 0:
            Global().show_error('Invalid character in term.')
            return
        # get term associations
        try:
            if self.new_term_var.get():  # is alias
                expr = self.ac_entry_custom.get().strip()
                if not Global().validate_expression(expr):
                    return
                added_ids = Global().dataset.add_custom_term_by_expression(new_term, expr)
            else:                        # is list of IDs
                ids = self.ac_entry_custom.get()
                if len(re.findall('[^0-9, ]', ids)) > 0:
                    Global().show_error('Invalid character in study IDs.')
                    return
                if len(new_term) == 0 or len(ids) == 0:
                    return
                # add to dataset
                ids = [int(i) for i in ids.split(',')]
                added_ids = Global().dataset.add_custom_term_by_ids(term, ids)
        except ValueError as e:
            Global().show_error(e)
            return

        Global().update_ac_lists()  # update autocomplete lists
        Global().update_status('Associated "%s" with %d studies.' % (new_term, len(added_ids)),
                               is_ready=True)
        self.entry_term.delete(0, tk.END)
        self.ac_entry_custom.delete(0, tk.END)

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
        if not Global().update_status(is_ready=True, user_op=True):  # not ready
            return
        # get filename
        roi_filename = askopenfilename(initialdir=Global().outpath,
                                       title='Select ROI file',
                                       filetypes=(('NIFTI files', '*.nii'),
                                                  ('NIFTI files', '*.gz'),
                                                  ('all files', '*.*')))
        if len(roi_filename) > 0:
            Global().roi_filename = roi_filename
            Global().load_roi(self.label_roi_file)
