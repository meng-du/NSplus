from __future__ import absolute_import, print_function
from .globals import Global
from abc import ABCMeta, abstractmethod
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
elif version_info.major == 3:
    import tkinter as tk


class PageBuilder(object):
    """
    Abstract base class containing methods to add shared page components
    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(PageBuilder, self).__init__(*args, **kwargs)

    def add_img_selection(self, row):
        self.image_labels = {
            'Forward inference with a uniform prior=0.5': 'pAgF_given_pF=0.50',
            'Forward inference z score (uniformity test)': 'uniformity-test_z',
            'Forward inference z score (uniformity test) with multiple comparison correction':
                'uniformity-test_z_FDR_',
            'Reverse inference with a uniform prior=0.5': 'pFgA_given_pF=0.50',
            'Reverse inference z score (association test)': 'association-test_z',
            'Reverse inference z score (association test) with multiple comparison correction':
                'association-test_z_FDR_'
        }
        self.img_var = tk.StringVar(value='pFgA_given_pF=0.50')
        for text in self.image_labels.keys():
            tk.Radiobutton(self,
                           text=text,
                           variable=self.img_var,
                           value=self.image_labels[text]) \
                .grid(row=row, column=0, columnspan=2, padx=30, sticky='w')
            row += 1

        return row - 1

    def add_comparison_settings(self, row, overlap=True, size=True, two_ways=True,
                                comp_btn=True):
        row -= 1
        #  checkbox: excluding overlap
        if overlap:
            row += 1
            self.overlap_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Exclude studies associated with both terms',
                           variable=self.overlap_var) \
                .grid(row=row, padx=15, pady=2, sticky=tk.W)

        #  checkbox: equal study set sizes
        if size:
            row += 1
            self.equal_size_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Randomly sample the larger study set to get '
                                'two equally sized sets',
                           variable=self.equal_size_var) \
                .grid(row=row, padx=15, pady=(2, 0), sticky=tk.W)
            self.equal_size_var.trace('w', lambda name, i, mode: self.equal_size_onchange())
            #  number of iterations
            row += 1
            tk.Label(self, text='Number of iterations:') \
                .grid(row=row, padx=(50, 0), pady=(0, 2), sticky='w')
            #   entry
            self.entry_num_iter, self.btn_num_iter = self.add_controlled_entry(
                row, width=5, padx=(200, 0),
                default_val=Global().num_iterations,
                btn_func=self.change_num_iter)

        #  checkbox: compare both ways
        if two_ways:
            row += 1
            self.two_way_var = tk.IntVar(value=1)
            tk.Checkbutton(self,
                           text='Analyze both terms (term1 vs term2, and term2 vs term1)',
                           variable=self.two_way_var) \
                .grid(row=row, padx=15, pady=2, sticky=tk.W)

        #  compare button
        if comp_btn:
            row += 1
            self.btn_start = tk.Button(self,
                                       command=self.start,
                                       text=' Compare ',
                                       highlightthickness=0)
            self.btn_start.grid(row=row, padx=10, pady=(20, 10))

        return row

    def add_controlled_entry(self, row, default_val, btn_func, width=5, padx=(0, 0),
                             pady=(0, 0), sticky=tk.W):
        if sticky == tk.W:
            entry_padx = (padx[0], 0)
            btn_padx = (padx[0] + 10 * (width + 2), padx[1])
        elif sticky == tk.E:
            entry_padx = (padx[0], padx[1] + 10 * (width + 2))
            btn_padx = (0, padx[1])
        else:
            raise ValueError('Sticky type not supported')

        entry = tk.Entry(self, width=width)
        entry.insert(tk.END, default_val)
        entry.config(disabledbackground='#e0e0e0',
                     disabledforeground='#6d6d6d')
        entry.config(state=tk.DISABLED)
        entry.grid(row=row, padx=entry_padx, pady=pady, sticky=sticky)
        entry.bind('<Return>', lambda e: btn_func())

        button = tk.Button(self, command=btn_func, text=' Change ',
                           highlightthickness=0)
        button.grid(row=row, padx=btn_padx, pady=pady, sticky=sticky)

        return entry, button

    def change_num_iter(self, discard_change=False):
        # TODO a general function
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
