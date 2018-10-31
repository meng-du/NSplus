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


class GroupCompPage(AutocompletePage):
    def __init__(self, parent, **kwargs):
        super(GroupCompPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Group Comparison'
        row_i = -1

        # page contents
        #  entry
        row_i += 1
        self.ac_entry = self.create_labeled_ac_entry(row=row_i, width=55)[1]
        #  add button
        row_i += 1
        self.btn_add = tk.Button(self, command=self.add_expression, text=' Add ',
                                 highlightthickness=0)
        self.btn_add.grid(row=row_i, padx=(0, 10), pady=(2, 10), sticky=tk.E)

        #  expression list
        row_i += 1
        self.listbox = tk.Listbox(self, height=10, width=60)
        self.listbox.grid(row=row_i, padx=15, pady=10)

    def add_expression(self):
        expression = self.ac_entry.get()
        try:
            Global().validate_expression(expression)
        except ValueError as e:
            Global().show_error(e)
            return

        self.listbox.insert(tk.END, expression)
