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


class ComparisonPage(AutocompletePage):
    def __init__(self, parent, **kwargs):
        super(ComparisonPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Comparison'
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
            .grid(row=row_i, padx=10, pady=(30, 0))

        #  checkbox: equal study set sizes
        row_i += 1
        self.equal_size_var = tk.IntVar(value=1)
        tk.Checkbutton(self,
                       text='Random sample the larger study set to get '
                            'two equally sized sets',
                       variable=self.equal_size_var) \
            .grid(row=row_i, padx=10)
        # TODO # iterations

        #  checkbox: compare both ways
        row_i += 1
        self.two_way_var = tk.IntVar(value=1)
        tk.Checkbutton(self,
                       text='Analyze both terms (term1 vs term2 and term2 vs term1)',
                       variable=self.two_way_var) \
            .grid(row=row_i, padx=10)

        #  compare button
        row_i += 1
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Compare ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, padx=10, pady=(100, 10))

    def start(self):
        if not Global().valid_options():
            return

        expr = self.ac_entry1.get()
        contrary_expr = self.ac_entry1.get()
        exclude_overlap = self.overlap_var.get() == 1
        reduce_larger_set = self.equal_size_var.get() == 1
        two_way = self.two_way_var.get() == 1

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

            except Exception as e:
                Global().show_error(e)

