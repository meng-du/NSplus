from __future__ import absolute_import, print_function
from .globals import Global
from .autocomplete_page import AutocompletePage
from ..src.metaplus import NeurosynthInfo
from ..src.comparison import compare_expressions
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class PairCompPage(AutocompletePage):
    def __init__(self, parent, **kwargs):
        super(PairCompPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Pairwise Comparison'
        row_i = -1

        # page contents
        #  first expression
        row_i += 1
        self.ac_entry1 = self.create_labeled_ac_entry(row=row_i)[1]

        #  second expression
        row_i += 2
        self.ac_entry2 = self.create_labeled_ac_entry(
            row=row_i,
            label_text='Enter term or expression in contrast:')[1]

        #  checkbox: excluding overlap
        row_i += 2
        self.overlap_var = tk.IntVar(value=1)
        tk.Checkbutton(self,
                       text='Exclude studies associated with both terms',
                       variable=self.overlap_var) \
            .grid(row=row_i, padx=10, pady=(30, 2), sticky=tk.W)

        #  checkbox: equal study set sizes
        row_i += 1
        self.equal_size_var = tk.IntVar(value=1)
        tk.Checkbutton(self,
                       text='Randomly sample the larger study set to get '
                            'two equally sized sets',
                       variable=self.equal_size_var) \
            .grid(row=row_i, padx=10, pady=(2, 0), sticky=tk.W)
        self.equal_size_var.trace('w', lambda name, i, mode: self.equal_size_onchange())
        #  number of iterations
        row_i += 1
        tk.Label(self, text='Number of iterations:') \
            .grid(row=row_i, padx=(50, 0), pady=(0, 2), sticky='w')
        #   entry
        self.entry_num_iter = tk.Entry(self, width=5)
        self.entry_num_iter.insert(tk.END, Global().num_iterations)
        self.entry_num_iter.config(disabledbackground='#e0e0e0', disabledforeground='#6d6d6d')
        self.entry_num_iter.config(state=tk.DISABLED)
        self.entry_num_iter.grid(row=row_i, padx=(200, 0), sticky=tk.W)
        self.entry_num_iter.bind('<Return>', lambda e: self.change_num_iter())
        #   button
        self.btn_num_iter = tk.Button(self, command=self.change_num_iter, text=' Change ',
                                      highlightthickness=0)
        self.btn_num_iter.grid(row=row_i, padx=(270, 0), sticky=tk.W)

        #  checkbox: compare both ways
        row_i += 1
        self.two_way_var = tk.IntVar(value=1)
        tk.Checkbutton(self,
                       text='Analyze both terms (term1 vs term2, and term2 vs term1)',
                       variable=self.two_way_var) \
            .grid(row=row_i, padx=10, pady=2, sticky=tk.W)

        #  compare button
        row_i += 1
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Compare ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, padx=10, pady=(20, 10))

    def change_num_iter(self, discard_change=False):
        """
        Toggle the Change/Apply button, unless discard_change is True
        :param discard_change: if True, just disable the entry and make sure
                               the button shows "Change"
        """
        # discard change
        if discard_change and 'Apply' in self.btn_num_iter['text']:
            self.entry_num_iter.config(state=tk.DISABLED)
            self.btn_num_iter.config(text=' Change ')
            return

        # otherwise, toggle
        if self.equal_size_var.get() == 0:
            return
        if 'Change' in self.btn_num_iter['text']:
            # changing, "Change" -> "Apply"
            self.entry_num_iter.config(state=tk.NORMAL)
            self.btn_num_iter.config(text=' Apply ')
        else:
            # applying change, "Apply" -> "Change"
            new_num_iter = self.entry_num_iter.get()
            if Global().set_num_iter(new_num_iter):  # success
                self.entry_num_iter.config(state=tk.DISABLED)
                self.btn_num_iter.config(text=' Change ')
            else:  # error
                self.entry_num_iter.delete(0, tk.END)
                self.entry_num_iter.insert(tk.END, Global().num_iterations)

    def equal_size_onchange(self):
        if self.equal_size_var.get() == 0:  # unchecked
            self.change_num_iter(discard_change=True)
            num_iter = '1'
            button_state = tk.DISABLED
        else:  # checked
            num_iter = Global().num_iterations
            button_state = tk.NORMAL

        self.btn_num_iter.config(state=button_state)
        self.entry_num_iter.config(state=tk.NORMAL)
        self.entry_num_iter.delete(0, tk.END)
        self.entry_num_iter.insert(tk.END, num_iter)
        self.entry_num_iter.config(state=tk.DISABLED)

    def start(self):
        if not Global().valid_options():
            return

        expr = self.ac_entry1.get()
        contrary_expr = self.ac_entry2.get()
        exclude_overlap = self.overlap_var.get() == 1
        reduce_larger_set = self.equal_size_var.get() == 1
        two_way = self.two_way_var.get() == 1
        num_iterations = Global().num_iterations if reduce_larger_set else 1

        try:
            Global().validate_expression(expr)
            Global().validate_expression(contrary_expr)
        except ValueError as e:
            Global().show_error(e)
            return

        if not Global().update_status(
                status='Comparing "%s" and "%s"...' % (expr, contrary_expr),
                is_ready=False, user_op=True):
            return

        def _compare():
            try:
                # output directory
                dirname = NeurosynthInfo.get_shorthand_expr(expr) + '_vs_' + \
                          NeurosynthInfo.get_shorthand_expr(contrary_expr)
                outdir = Global().make_result_dir(dirname)
                # run
                compare_expressions(Global().dataset, expr, contrary_expr, exclude_overlap,
                                    reduce_larger_set, num_iterations, two_way,
                                    fdr=Global().fdr,
                                    extra_info=[
                                        ('mask', Global().roi_filename or Global().default_roi)],
                                    outdir=outdir)

                Global().root.event_generate('<<Done_comparison>>')  # trigger event

            except Exception as e:
                Global().show_error(e)

        Thread(target=_compare).start()
        Global().root.bind('<<Done_analysis>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outdir,
                               is_ready=True
                           ))
