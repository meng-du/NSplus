from __future__ import absolute_import, print_function
from .globals import Global
from .pagebuilder import PageBuilder
from .autocompletepage import AutocompletePage
from ..src.comparison import compare_multiple
from ..src.analysisinfo import AnalysisInfo
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class MultiCompPage(PageBuilder, AutocompletePage):
    def __init__(self, parent, **kwargs):
        super(MultiCompPage, self).__init__(parent=parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Battle Royale'  # 'Multi-Term Comparison'
        row_i = -1

        # page contents
        #  entry
        row_i += 1
        self.ac_entry = self.create_labeled_ac_entry(row=row_i, width=54)[1]
        #  add button
        row_i += 1
        self.btn_add = tk.Button(self, command=self.add_expression, text=' Add ',
                                 highlightthickness=0)
        self.btn_add.grid(row=row_i, padx=(0, 10), pady=(2, 30), sticky=tk.E)

        #  expression list
        row_i += 1
        self.listbox = tk.Listbox(self, height=5, width=60)
        self.listbox.grid(row=row_i, padx=10)
        #  counter
        row_i += 1
        self.label_counter = tk.Label(self, text='0 term(s)')
        self.label_counter.grid(row=row_i, padx=20, sticky=tk.W)
        #  remove button
        self.btn_remove = tk.Button(self, command=self.remove_expression,
                                    text=' Remove ', highlightthickness=0)
        self.btn_remove.grid(row=row_i, padx=20, pady=(5, 0), sticky=tk.E)
        self.btn_remove.config(state=tk.DISABLED)
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)

        #  image selection
        row_i += 1
        tk.Label(self, text='Create battle images based on:') \
            .grid(row=row_i, padx=10, pady=(10, 2), sticky=tk.W)
        row_i = self.add_img_selection(row_i + 1, exclude_imgs=['pA', 'pA_given_pF='])

        #  thresholds
        def change_func(which_thr):
            if which_thr == 'lower':
                if self.lower_thr_var.get() == 1:
                    self.entry_control(self.entry_lower_thr, self.btn_lower_thr,
                                       Global().lower_thr, Global().set_lower_thr)
            else:
                if self.upper_thr_var.get() == 1:
                    self.entry_control(self.entry_upper_thr, self.btn_upper_thr,
                                       Global().upper_thr, Global().set_upper_thr)
        #  lower threshold
        row_i += 1
        self.lower_thr_var = tk.IntVar(value=1)
        tk.Checkbutton(self, text='Lower threshold:',
                       variable=self.lower_thr_var) \
            .grid(row=row_i, padx=10, pady=(10, 0), sticky=tk.W)
        self.entry_lower_thr, self.btn_lower_thr = \
            self.add_controlled_entry_with_controller(row=row_i,
                                                      entry_val=lambda: Global().lower_thr,
                                                      disabled_entry_val=None,
                                                      btn_func=lambda: change_func('lower'),
                                                      checkbox_var=self.lower_thr_var,
                                                      padx=(150, 0), pady=(10, 0))
        #  upper threshold
        row_i += 1
        self.upper_thr_var = tk.IntVar(value=0)
        tk.Checkbutton(self, text='Upper threshold:',
                       variable=self.upper_thr_var) \
            .grid(row=row_i, padx=10, pady=(2, 5), sticky=tk.W)
        self.entry_upper_thr, self.btn_upper_thr = \
            self.add_controlled_entry_with_controller(row=row_i,
                                                      entry_val=lambda: Global().upper_thr,
                                                      disabled_entry_val=None,
                                                      btn_func=lambda: change_func('upper'),
                                                      checkbox_var=self.upper_thr_var,
                                                      padx=(150, 0), pady=(2, 5))

        #  label
        row_i += 1
        tk.Label(self, text='When comparing each pair:') \
            .grid(row=row_i, padx=10, pady=(10, 0), sticky=tk.W)

        self.add_comparison_settings(row=row_i + 1, two_ways=False,
                                     start_func=self.start)

    def on_selection_change(self, event):
        if len(self.listbox.curselection()) > 0:  # selected
            self.btn_remove.config(state=tk.NORMAL)
        else:   # deselected
            self.btn_remove.config(state=tk.DISABLED)

    def add_expression(self):
        expression = self.ac_entry.get()
        try:
            Global().validate_expression(expression)
        except ValueError as e:
            Global().show_error(e)
            return

        self.listbox.insert(tk.END, expression)
        self.label_counter.config(text='%d term(s)' % self.listbox.size())
        self.ac_entry.delete(0, tk.END)

    def remove_expression(self):
        selected = self.listbox.curselection()
        if len(selected) == 0:
            return
        self.listbox.delete(selected[0])
        self.label_counter.config(text='%d term(s)' % self.listbox.size())
        self.btn_remove.config(state=tk.DISABLED)

    def start(self):
        if not Global().validate_settings():
            return

        # discard any changes
        self.entry_control(self.entry_num_iter, self.btn_num_iter,
                           discard_change=True)

        expressions = self.listbox.get(0, tk.END)
        if len(expressions) < 3:
            Global().show_error('Please specify more than 2 terms')
            return

        image = AnalysisInfo.add_num_to_name(self.img_var.get(),
                                             Global().prior, Global().fdr)

        lower_thr = Global().lower_thr if self.lower_thr_var.get() == 1 else None
        upper_thr = Global().upper_thr if self.upper_thr_var.get() == 1 else None
        no_overlap = self.overlap_var.get() == 1
        reduce = self.equal_size_var.get() == 1
        num_iter = Global().num_iterations if reduce else 1

        mask = ('mask', Global().roi_filename or Global().default_roi)

        if not Global().update_status(
                status='Comparing term group...',
                is_ready=False, user_op=True):
            return

        def _compare():
            try:
                # run
                compare_multiple(Global().dataset, expressions, image, lower_thr,
                                 upper_thr, extra_info=[mask], outpath=Global().outpath,
                                 exclude_overlap=no_overlap, reduce_larger_set=reduce,
                                 num_iterations=num_iter)
                Global().root.event_generate('<<Done_group_comp>>')  # trigger event

            except Exception as e:
                Global().show_error(e)

        Thread(target=_compare).start()
        Global().root.bind('<<Done_group_comp>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outpath,
                               is_ready=True))
