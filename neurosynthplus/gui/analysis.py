from __future__ import absolute_import, print_function
from ..src.analysis import analyze_expression
from .autocomplete import AutocompleteEntry
from .globals import Global
import re
import os
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


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
        if not Global().valid_options():
            return

        expression = self.ac_entry.get()

        if not Global().update_status(status='Analyzing "%s"...' % expression,
                                      is_ready=False, user_op=True):
            return

        def _analyze():
            try:
                if Global().roi_filename is None:
                    postfix = 'output'
                else:
                    roi_name = os.path.split(Global().roi_filename)[1]
                    postfix = 'masked_by_%s' % roi_name.split('.')[0]
                analyze_expression(Global().dataset, expression,
                                   csv_postfix=postfix,
                                   outdir=Global().outdir)
                Global().root.event_generate('<<Done_analysis>>')  # trigger event
            except Exception as e:
                Global().show_error(e)

        Thread(target=_analyze).start()
        Global().root.bind('<<Done_analysis>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outdir,
                               is_ready=True
                           ))

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
