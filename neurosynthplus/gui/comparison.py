from __future__ import absolute_import, print_function
from .globals import Global
from .autocomplete_page import AutocompletePage
from ..src.metaplus import NeurosynthInfo
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

        # compare button
        row_i += 2
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

        if not Global().update_status(
                status='Comparing "%s" and "%s"...' % (expr, contrary_expr),
                is_ready=False, user_op=True):
            return

        def _compare():
            try:
                # output directory
                folder_name = NeurosynthInfo.get_shorthand_expr(expr)
            except Exception as e:
                Global().show_error(e)
