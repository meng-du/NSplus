from __future__ import absolute_import, print_function
from .analysis import AnalysisPage
from .ranking import RankingPage
from .settings import SettingsPage
from .globals import Global
from threading import Thread
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox


class ComparisonPage(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(ComparisonPage, self).__init__(parent, **kwargs)
        self.parent = parent
        self.nb_label = 'Comparison'
        row_i = -1


class MainApp(tk.Frame):
    def __init__(self, root, **kwargs):
        super(MainApp, self).__init__(root, **kwargs)
        self.parent = root
        self.app_name = 'NeuroSynth+'

        root.title(self.app_name)
        # parent.geometry('350x200')

        # menu bar
        menubar = tk.Menu(root, title=self.app_name)
        about_menu = tk.Menu(menubar, name='test')
        about_menu.add_command(label='self.app_name', command=lambda: print('1'))
        menubar.add_cascade(label='About', menu=about_menu)
        root.config(menu=menubar)

        # notebook layout
        row_i = 0
        self.notebook = ttk.Notebook(self)
        self.nb_pages = [RankingPage(self.notebook),
                         AnalysisPage(self.notebook),
                         ComparisonPage(self.notebook),
                         SettingsPage(self.notebook)]
        self.settings_page_index = len(self.nb_pages) - 1
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.grid(row=row_i)

    def create_settings_button(self, btn_parent):
        return tk.Button(btn_parent,
                         command=lambda: self.notebook.select(self.settings_page_index),
                         text=' Settings ',
                         highlightthickness=0)


def main_gui():
    gui_started = False
    try:
        root = tk.Tk()
        main_app = MainApp(root)
        main_app.pack(side='top', fill='both')
        Global(root, main_app)
        # load NeuroSynth database in another thread
        Thread(target=Global.load_pkl_database, args=[Global()]).start()
        # start GUI
        gui_started = True
        root.mainloop()
    except Exception as e:
        if gui_started:
            Global().show_error(e)
        else:
            messagebox.showerror('Error', str(e))
            raise


if __name__ == '__main__':
    main_gui()
