from __future__ import absolute_import, print_function
from ..src.analysis import analyze_expression
from ..src.metaplus import NeurosynthInfo
from .autocomplete_page import AutocompletePage
from .globals import Global
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class AnalysisPage(AutocompletePage):
    def __init__(self, parent, **kwargs):
        super(AnalysisPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Analysis'
        row_i = -1

        # page contents
        # instruction label
        row_i += 1
        self.ac_entry = self.create_labeled_ac_entry(row=row_i)[1]

        # analyze button
        row_i += 2
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
                # output directory
                outdir = Global().make_result_dir(NeurosynthInfo.get_shorthand_expr(expression))
                # run
                analyze_expression(Global().dataset, expression,
                                   fdr=Global().fdr,
                                   extra_info=[('mask',
                                                Global().roi_filename or Global().default_roi)],
                                   outdir=outdir)
                Global().root.event_generate('<<Done_analysis>>')  # trigger event
            except Exception as e:
                Global().show_error(e)

        Thread(target=_analyze).start()
        Global().root.bind('<<Done_analysis>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outdir,
                               is_ready=True
                           ))
