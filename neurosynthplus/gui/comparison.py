from __future__ import absolute_import, print_function
from .globals import Global
from .autocomplete_page import AutocompletePage
from abc import ABCMeta, abstractmethod
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class ComparisonPage(AutocompletePage):
    __metaclass__ = ABCMeta

    def __init__(self, parent, **kwargs):
        super(ComparisonPage, self).__init__(parent, **kwargs)
        self.parent = parent

    def add_settings(self, row, overlap=True, size=True, two_ways=True, comp_btn=True):
        #  checkbox: excluding overlap
        if overlap:
            self.overlap_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Exclude studies associated with both terms',
                           variable=self.overlap_var) \
                .grid(row=row, padx=10, pady=(10, 2), sticky=tk.W)

        #  checkbox: equal study set sizes
        if size:
            row += 1
            self.equal_size_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Randomly sample the larger study set to get '
                                'two equally sized sets',
                           variable=self.equal_size_var) \
                .grid(row=row, padx=10, pady=(2, 0), sticky=tk.W)
            self.equal_size_var.trace('w', lambda name, i, mode: self.equal_size_onchange())
            #  number of iterations
            row += 1
            tk.Label(self, text='Number of iterations:') \
                .grid(row=row, padx=(50, 0), pady=(0, 2), sticky='w')
            #   entry
            self.entry_num_iter = tk.Entry(self, width=5)
            self.entry_num_iter.insert(tk.END, Global().num_iterations)
            self.entry_num_iter.config(disabledbackground='#e0e0e0', disabledforeground='#6d6d6d')
            self.entry_num_iter.config(state=tk.DISABLED)
            self.entry_num_iter.grid(row=row, padx=(200, 0), sticky=tk.W)
            self.entry_num_iter.bind('<Return>', lambda e: self.change_num_iter())
            #   button
            self.btn_num_iter = tk.Button(self, command=self.change_num_iter, text=' Change ',
                                          highlightthickness=0)
            self.btn_num_iter.grid(row=row, padx=(270, 0), sticky=tk.W)

        #  checkbox: compare both ways
        if two_ways:
            row += 1
            self.two_way_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Analyze both terms (term1 vs term2, and term2 vs term1)',
                           variable=self.two_way_var) \
                .grid(row=row, padx=10, pady=2, sticky=tk.W)

        #  compare button
        if comp_btn:
            row += 1
            self.btn_start = tk.Button(self,
                                       command=self.start,
                                       text=' Compare ',
                                       highlightthickness=0)
            self.btn_start.grid(row=row, padx=10, pady=(30, 10))

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

    @abstractmethod
    def start(self):
        pass
