from __future__ import absolute_import, print_function
from ..src.analysis import analyze_expression
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
        #  entry
        row_i += 1
        self.ac_entry = self.create_labeled_ac_entry(row=row_i)[1]

        #  instructions TODO make a help page
        row_i += 2
        help_text = 'Operators between terms:\n\n' \
                    '    AND &     OR |     NOT ~     WILDCARD *\n\n' \
                    'Examples:\n\n' \
                    '    "emotion & emotional": studies associated with both terms\n\n' \
                    '    "emotion | emotional": studies associated with either terms\n\n' \
                    '    "emo*": studies associated with any term starting with "emo"\n\n' \
                    '    "emotion &~ face": studies associated with emotion, but not face\n\n' \
                    '    "(emotion | emotional | emotionally) &~ *face*": studies\n' \
                    '    associated with at least one of emotion, emotional or emotionally,\n' \
                    '    but not with any term containing face'
        tk.Label(self, text=help_text, justify=tk.LEFT) \
            .grid(row=row_i, padx=15, pady=15)

        #  analyze button
        row_i += 2
        self.btn_start = tk.Button(self,
                                   command=self.start,
                                   text=' Analyze ',
                                   highlightthickness=0)
        self.btn_start.grid(row=row_i, padx=10, pady=10)

    def start(self):
        if not Global().validate_settings():
            return

        expression = self.ac_entry.get()
        try:
            Global().validate_expression(expression)
        except ValueError as e:
            Global().show_error(e)
            return

        if not Global().update_status(status='Analyzing "%s"...' % expression,
                                      is_ready=False, user_op=True):
            return

        def _analyze():
            try:
                # run
                analyze_expression(Global().dataset, expression,
                                   fdr=Global().fdr,
                                   extra_info=[('mask',
                                                Global().roi_filename or Global().default_roi)],
                                   outpath=Global().outpath)
                Global().root.event_generate('<<Done_analysis>>')  # trigger event
            except Exception as e:
                Global().show_error(e)

        Thread(target=_analyze).start()
        Global().root.bind('<<Done_analysis>>',
                           lambda e: Global().update_status(
                               status='Done. Files are saved to ' + Global().outpath,
                               is_ready=True
                           ))
