from __future__ import absolute_import, print_function
from .globals import Global
from .autocomplete import AutocompleteEntry
import re
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class AutocompletePage(tk.Frame):
    """
    Base class for any frame that has an AutocompleteEntry in it
    """
    def __init__(self, parent, **kwargs):
        super(AutocompletePage, self).__init__(master=parent, **kwargs)
        self.ac_entry_list = []
        Global().ac_lists.append(self.ac_entry_list)

    def create_labeled_ac_entry(self, width=60, row=0, padx=10, pady=(10, 2),
                                label_text='Enter term or expression:'):
        if label_text and len(label_text) > 0:
            ac_label = tk.Label(self, text=label_text) \
                .grid(row=row, padx=10, pady=(10, 2), sticky=tk.W)
            row += 1
        else:
            ac_label = None

        # term/expression entry
        ac_entry = AutocompleteEntry([], self, listboxLength=8, width=width,
                                     matchesFunction=self.matches_term,
                                     setFunction=self.set_selection)
        ac_entry.grid(row=row, padx=padx, pady=pady, sticky=tk.W)
        self.ac_entry_list.append(ac_entry)
        return ac_entry, ac_label

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
        while last_word_index < len(field_value) and \
                field_value[last_word_index].isspace():  # strip whitespace
            last_word_index += 1
        return field_value[:last_word_index] + ac_list_entry
