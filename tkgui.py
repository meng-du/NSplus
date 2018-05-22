from sys import version_info
if version_info.major == 2:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename
elif version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename


class MainApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        parent.title('NeuroSynth++')
        # parent.geometry('350x200')

        # button style
        ttk.Style().map('C.TButton', background=[('pressed', 'blue')])
        # layout
        notebook = tk.ttk.Notebook(parent)
        page1 = ttk.Frame(notebook)
        page2 = ttk.Frame(notebook)
        notebook.add(page1, text='Rank Terms')
        notebook.add(page2, text='Analysis & Compare')
        notebook.pack(expand=1, fill='both')

        btn_choose_file = tk.Button(page1,
                                    command=askopenfilename,
                                    text=' Choose ROI file ',
                                    highlightbackground='#f2f2f2',  # ececec
                                    highlightthickness=0)
        btn_choose_file.pack(padx='10', pady='10')


def main():
    root = tk.Tk()
    MainApp(root).pack(side='top', fill='both')
    root.mainloop()


if __name__ == '__main__':
    main()
