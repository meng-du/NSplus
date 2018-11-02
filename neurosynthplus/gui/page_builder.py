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
        """
        Add 6 radio buttons that asks user to select one of the images
        :return: the last row number
        :param row: (integer) the first row number for these widgets
        :return: (integer) the last row number
        """
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
                                comp_btn=True, start_func=None):
        """
        Add 3 check box widgets related to term comparison
        :param start_func: a function that runs when comp_btn is clicked; must be
                           defined if comp_btn=True
        :return: (integer) the last row number
        """
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
            #  number of iterations text label
            row += 1
            tk.Label(self, text='Number of iterations:') \
                .grid(row=row, padx=(50, 0), pady=(0, 2), sticky='w')

            #   controlled entry
            def change_func():
                if self.equal_size_var.get() == 1:
                    self.entry_controller(self.entry_num_iter, self.btn_num_iter,
                                          Global().num_iterations, Global().set_num_iter)
            self.entry_num_iter, self.btn_num_iter = \
                self.add_controlled_entry_with_controller(
                    row=row,
                    entry_val=lambda: Global().num_iterations,
                    disabled_entry_val='1',
                    btn_func=change_func,
                    checkbox_var=self.equal_size_var,
                    padx=(200, 0))

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
            if start_func is None:
                raise RuntimeError('No method specified for the compare button')
            self.btn_start = tk.Button(self,
                                       command=start_func,
                                       text=' Compare ',
                                       highlightthickness=0)
            self.btn_start.grid(row=row, padx=10, pady=(20, 10))

        return row

    # Methods below are related to a button-controlled entry, which can be together
    # controlled with a checkbox

    def add_controlled_entry(self, row, entry_val, btn_func,
                             width=5, padx=(0, 0), pady=(0, 0), sticky=tk.W):
        """
        Add an entry controlled by a button next to it. The button toggles the entry
        status between disabled (button showing "Apply") and normal (button showing
        "Change")

        :param entry_val: the initial value for the entry (could be None)
        :param btn_func: (function) a function that runs when the button is clicked,
                         see entry_controller below
        :param width: (integer) width of the entry
        :return: (tkinter widgets) the entry and the button
        """
        if sticky == tk.W:
            entry_padx = (padx[0], 0)
            btn_padx = (padx[0] + 10 * (width + 2), padx[1])
        elif sticky == tk.E:
            entry_padx = (padx[0], padx[1] + 10 * (width + 2))
            btn_padx = (0, padx[1])
        else:
            raise ValueError('Sticky type not supported')

        entry = tk.Entry(self, width=width)
        if entry_val is not None:
            entry.insert(tk.END, entry_val)
        entry.config(disabledbackground='#e0e0e0',
                     disabledforeground='#6d6d6d')
        entry.config(state=tk.DISABLED)
        entry.grid(row=row, padx=entry_padx, pady=pady, sticky=sticky)
        entry.bind('<Return>', lambda e: btn_func())

        button = tk.Button(self, command=btn_func, text=' Change ',
                           highlightthickness=0)
        button.grid(row=row, padx=btn_padx, pady=pady, sticky=sticky)

        return entry, button

    def entry_controller(self, entry, button, entry_val=None, set_func=None,
                         discard_change=False):
        """
        Toggles the Change/Apply button that controls an entry (see
        add_controlled_entry above), unless discard_change is True.
        Define another callback function with no parameters to pass to
        add_controlled_entry as btn_func, and call this function in it.

        :param entry_val: a value to fill the entry when set_func returns false
                          (i.e. when user enters an invalid value)
        :param set_func: a function called when clicking "Apply"; should take 1
                         parameter, i.e. the user input in the entry, and returns
                         either True (successful) or False (invalid entry input)
                         Must be specified when discard_change=False
        :param discard_change: if True, just disable the entry, discard changes if
                               there is any, and make sure the button shows "Change"
        """
        # discard change
        if discard_change:
            if 'Apply' in button['text']:
                entry.config(state=tk.DISABLED)
                button.config(text=' Change ')
            return

        # otherwise, toggle
        if 'Change' in button['text']:
            # changing, "Change" -> "Apply"
            entry.config(state=tk.NORMAL)
            button.config(text=' Apply ')
        else:
            # applying change, "Apply" -> "Change"
            if set_func is None:
                raise RuntimeError('No method specified to set the value')
            new_val = entry.get()
            if set_func(new_val):  # success
                entry.config(state=tk.DISABLED)
                button.config(text=' Change ')
            else:  # error
                entry.delete(0, tk.END)
                if entry_val is not None:
                    entry.insert(tk.END, entry_val)

    def add_controlled_entry_with_controller(self, row, entry_val, disabled_entry_val,
                                             btn_func, checkbox_var, **kwargs):
        """
        Same as add_controlled_entry, but both entry and button are controlled by
        another checkbox, whose variable is checkbox_var

        :param entry_val: initial and fallback value for the entry, or a function
                          that returns this value
                          Note: use lambda to pass by reference if it's a variable,
                          e.g. entry_val=lambda: some_entry_val
        :param kwargs: anything else passed to add_controlled_entry
        :return: (tkinter widgets) entry and button
        """
        val = entry_val() if callable(entry_val) else entry_val
        entry, button = self.add_controlled_entry(row, val, btn_func, **kwargs)

        #  checkbox callback
        def checkbox_onchange(name=None, index=None, mode=None):
            self.controlled_entry_controller_onchange(checkbox_var, entry, button,
                                                      disabled_entry_val, entry_val)

        checkbox_onchange()  # set initial state
        checkbox_var.trace('w', checkbox_onchange)

        return entry, button

    def controlled_entry_controller_onchange(self, checkbox_var, entry, button,
                                             disabled_entry_val, enabled_entry_val):
        """
        When a button-controlled entry is also controlled by another checkbox
        (i.e. the checkbox controls both: when it's not checked, button
        and entry are both disabled), this callback function defines the button
        and entry behaviors whenever the checkbox value changes
        Use this function like:
        checkbox_var.trace('w',
            lambda name, index, mode: controlled_entry_controller_onchange())

        :param checkbox_var: the tkinter variable for the checkbox
        :param disabled_entry_val: the value for the entry when the checkbox is not
                                   checked, or a function that returns this value
        :param enabled_entry_val: the value for the entry when the checkbox is
                                  checked, or a function that returns this value
        """
        if checkbox_var.get() == 0:  # unchecked
            self.entry_controller(entry, button, discard_change=True)
            entry_val = disabled_entry_val() if callable(disabled_entry_val) \
                else disabled_entry_val
            button_state = tk.DISABLED
        else:  # checked
            entry_val = enabled_entry_val() if callable(enabled_entry_val) \
                else enabled_entry_val
            button_state = tk.NORMAL

        button.config(state=button_state)
        entry.config(state=tk.NORMAL)
        entry.delete(0, tk.END)
        if entry_val is not None:
            entry.insert(tk.END, entry_val)
        entry.config(state=tk.DISABLED)
