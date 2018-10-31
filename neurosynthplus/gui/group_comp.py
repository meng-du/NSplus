from __future__ import absolute_import, print_function
from .globals import Global
from .comparison import ComparisonPage
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class GroupCompPage(ComparisonPage):
    def __init__(self, parent, **kwargs):
        super(GroupCompPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Group Comparison'
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
        self.listbox = tk.Listbox(self, height=8, width=60)
        self.listbox.grid(row=row_i, padx=15)
        #  remove button
        row_i += 1
        self.btn_remove = tk.Button(self, command=self.remove_expression,
                                    text=' Remove ', highlightthickness=0)
        self.btn_remove.grid(row=row_i, padx=15, pady=(5, 0), sticky=tk.E)
        self.btn_remove.config(state=tk.DISABLED)
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)

        #  label
        row_i += 1
        tk.Label(self, text='When comparing each pair:') \
            .grid(row=row_i, padx=10, pady=(10, 2), sticky=tk.W)

        self.add_settings(row=row_i + 1, two_ways=False)

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
        self.ac_entry.delete(0, tk.END)

    def remove_expression(self):
        selected = self.listbox.curselection()
        if len(selected) == 0:
            return
        self.listbox.delete(selected[0])
        self.btn_remove.config(state=tk.DISABLED)

    def start(self):
        if not Global().validate_options():
            return
        expressions = self.listbox.get(0, tk.END)

        exclude_overlap = self.overlap_var.get() == 1
        reduce_larger_set = self.equal_size_var.get() == 1
        two_way = self.two_way_var.get() == 1
        num_iterations = Global().num_iterations if reduce_larger_set else 1

        if not Global().update_status(
                status='Comparing terms...',
                is_ready=False, user_op=True):
            return

        def _compare():
            try:
                # run TODO

                Global().root.event_generate('<<Done_group_comp>>')  # trigger event

            except Exception as e:
                Global().show_error(e)

        Thread(target=_compare).start()
        Global().root.bind('<<Done_group_comp>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outdir,
                               is_ready=True
                           ))
