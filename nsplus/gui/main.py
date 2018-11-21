from __future__ import absolute_import, print_function
from .singleterm import AnalysisPage
from .ranking import RankingPage
from .paircomp import PairCompPage
from .multicomp import MultiCompPage
from .settings import SettingsPage
from .globals import Global
from ..version import __version__
from threading import Thread
import os
from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox


class MainApp(tk.Frame):
    def __init__(self, root, **kwargs):
        super(MainApp, self).__init__(root, **kwargs)
        self.parent = root
        root.title('NS+')

        # menu bar
        menubar = tk.Menu(root)
        appmenu = tk.Menu(menubar, name='apple')
        menubar.add_cascade(menu=appmenu)
        appmenu.add_command(label='About NS+',
                            command=lambda: AboutPage(tk.Toplevel(root), root))
        root.config(menu=menubar)

        # notebook layout
        row_i = 0
        self.notebook = ttk.Notebook(self)
        self.settings_page = SettingsPage(self.notebook)
        self.nb_pages = [self.settings_page,
                         RankingPage(self.notebook),
                         AnalysisPage(self.notebook),
                         PairCompPage(self.notebook),
                         MultiCompPage(self.notebook)]
        for page in self.nb_pages:
            self.notebook.add(page, text=page.nb_label)
        self.notebook.grid(row=row_i)


class AboutPage(tk.Frame):
    def __init__(self, parent, root, **kwargs):
        super(AboutPage, self).__init__(parent, **kwargs)
        parent.title('About NS+')
        bg_color = '#f1f1f1'
        parent.config(bg=bg_color)
        # icon
        iconpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon = tk.PhotoImage(file=os.path.join(iconpath, 'res', 'icon.png'))
        label = tk.Label(parent, image=icon, bg=bg_color)
        label.image = icon
        label.grid(row=0, pady=20)
        # texts
        tk.Label(parent, text='NS+', bg=bg_color, font='Verdana 18 bold') \
            .grid(row=1, padx=30, pady=0)
        tk.Label(parent, text='Extends the functionality of Neurosynth.org',
                 bg=bg_color, font='Verdana 12') \
            .grid(row=2, padx=20, pady=(0, 5))
        tk.Label(parent, text='Version ' + __version__, bg=bg_color, font='Verdana 11') \
            .grid(row=3, padx=20)
        tk.Label(parent, text=u'© 2018 Created by Meng Du and Matthew Lieberman',
                 bg=bg_color, font='Verdana 11') \
            .grid(row=4, padx=20, pady=20)
        tk.Label(parent, text='For citations, please use:',
                 bg=bg_color, font='Verdana 11') \
            .grid(row=5, padx=20, pady=(10, 0))
        # citation
        citation = 'Du, M. & Lieberman, M. D. (2018). NS+: A new\n' \
                   'meta-analysis tool to extend the utility of NeuroSynth.\n' \
                   'Unpublished manuscript.'
        tk.Label(parent, text=citation, bg=bg_color, font='TkFixedFont') \
            .grid(row=6, padx=20, pady=2)

        def copy_citation():
            root.clipboard_clear()
            root.clipboard_append(citation.replace('\n', ' '))
        tk.Button(parent, text=' Copy ', command=copy_citation, highlightthickness=0) \
            .grid(row=7, padx=20, pady=(0, 15))


def main_gui():
    gui_started = False
    try:
        root = tk.Tk()
        Global(root=root)
        main_app = MainApp(root)
        main_app.pack(side='top', fill='both')
        # load Neurosynth database in another thread
        Thread(target=Global.load_pkl_database, args=[Global()]).start()
        # start GUI
        gui_started = True
        root.mainloop()
    except Exception as e:
        if gui_started:
            Global().show_error(e)
        else:
            messagebox.showerror('Error', str(e))
            raise e


if __name__ == '__main__':
    main_gui()
