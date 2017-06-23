import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import models

class Application(tk.Frame):

    scanner = models.TwinCatScanner()

    def __init__(self, master=None):
        super().__init__(master)

        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.create_widgets()
        self.scanner.notify = self.app_notify

    def create_widgets(self):

        self.dir_select = ttk.Button(self, text="Wybierz projekt", command=self.dir_select_command)
        self.dir_select.grid(row=0, column=0, sticky=tk.NSEW)

        self.dir = tk.StringVar()
        self.dir_path = ttk.Entry(self, textvariable=self.dir)
        self.dir_path.grid(row=1, column=0, sticky=tk.NSEW)

        self.dir_process = ttk.Button(self, text="Wczytaj projekt", command=self.dir_process_command)
        self.dir_process.grid(row=2, column=0, sticky=tk.NSEW)

        self.quit = ttk.Button(self, text="Wyjście", command=ROOT.destroy)
        self.quit.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW)

        self.export = ttk.Button(self, text="CSV", command=self.csv_command)
        self.export.grid(row=2, column=1, sticky=tk.NSEW)

        self.main_area = ttk.Notebook(self)
        self.main_area.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)

        self.memory_areas_list = self.create_tab(self.main_area, "Zmienne", ("name", "offset", "size", "type", "map"))
        self.memory_areas_list.column('#0', stretch=tk.NO)
        self.memory_areas_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#2', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#3', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#4', stretch=tk.YES, minwidth=10000)

        self.const_list = self.create_tab(self.main_area, "Stałe", ("name", "value"))
        self.const_list.column('#0', stretch=tk.NO)
        self.const_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)

        self.types_list = self.create_tab(self.main_area, "Typy", ("name", "size"))
        self.types_list.column('#0', stretch=tk.NO)
        self.types_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)

        self.mem_list = self.create_tab(self.main_area, "Pamięć", ("adr", "variables"))
        self.mem_list.column('#0', stretch=tk.NO, anchor=tk.CENTER)
        self.mem_list.column('#1', stretch=tk.NO)

        self.status = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=tk.NSEW)

    def create_tab(self, master, text, columns):
        tab = ttk.Frame(master)
        tab.pack(expand=True, fill=tk.BOTH)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        master.add(tab, text=text)

        tree = ttk.Treeview(tab, columns=columns)
        tab_ysb = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=tree.yview)
        tab_xsb = ttk.Scrollbar(tab, orient=tk.HORIZONTAL, command=tree.xview)
        tree['yscroll'] = tab_ysb.set
        tree['xscroll'] = tab_xsb.set

        size = range(len(columns))
        for i in size:
            tree.heading("#{}".format(str(i)), text=columns[i])

        tree.grid(row=0, column=0, sticky=tk.NSEW)
        tab_ysb.grid(row=0, column=1, sticky=tk.NS)
        tab_xsb.grid(row=1, column=0, sticky=tk.EW)

        return tree

    def dir_select_command(self):
        tmp_dir = filedialog.askdirectory()
        self.dir.set(tmp_dir)

    def dir_process_command(self):
        path = self.dir_path.get()
        self.scanner.run(path)
        self.memory_areas_list.delete(*self.memory_areas_list.get_children())
        for area in self.scanner.memory_areas:
            area_values = [str(area.offset), area.size, area.type_name, area.map()]
            self.memory_areas_list.insert('', 'end', area.var_name, text=area.var_name, values=area_values)
        self.const_list.delete(*self.const_list.get_children())
        for const_name in self.scanner.global_constants:
            const_values = [str(self.scanner.global_constants[const_name])]
            self.const_list.insert('', 'end', const_name, text=const_name, values=const_values)
        self.types_list.delete(*self.types_list.get_children())
        for type_size in self.scanner.type_sizes:
            type_values = [str(self.scanner.type_sizes[type_size].size)]
            self.types_list.insert('', 'end', type_size, text=type_size, values=type_values)
            for field in self.scanner.type_sizes[type_size].fields:
                field_values = [str(self.scanner.type_sizes[type_size].fields[field])]
                self.types_list.insert(type_size, 'end', text=field, values=field_values)
        self.mem_list.delete(*self.mem_list.get_children())
        for mem in self.scanner.memory_map:
            mem_values = [str(self.scanner.memory_map[mem])]
            self.mem_list.insert('', 'end', mem, text=mem, values=mem_values)

    def app_notify(self, notification):
        self.status.set(notification)

    def csv_command(self):
        csv = tk.filedialog.asksaveasfile(filetypes=[("csv files", "*.csv")])
        if csv is not None:
            for area in self.scanner.memory_areas:
                csv.write("{};{};{};\n".format(area.var_name, str(area.offset), area.type_name))
            messagebox.showinfo("ProgressTwinCatScanner", "Zapisano plik")
            csv.close()


ROOT = tk.Tk()
ROOT.title("ProgressTwinCatScanner")
ROOT.rowconfigure(0, weight=1)
ROOT.columnconfigure(0, weight=1)

ROOT.style = ttk.Style()
ROOT.style.theme_use("alt")
ROOT.style.configure('.', font=('courier', 10))
ROOT.style.configure('TFrame', foreground="white", background="navy")
ROOT.style.configure('TEntry', foreground="white", fieldbackground="brown4", font=('fixedsys', 10))
ROOT.style.configure('TButton', foreground="white", background="aquamarine4")
ROOT.style.configure('TMenubutton', foreground="white", background="aquamarine4")
ROOT.style.configure('TNotebook', foreground="white", background="navy")
ROOT.style.configure('Treeview', foreground="white", background="navy", fieldbackground="navy")
ROOT.style.configure('TLabel', foreground="white", background="black")
ROOT.style.configure("Vertical.TScrollbar", troughcolor="medium orchid")
ROOT.style.configure("Horizontal.TScrollbar", troughcolor="medium orchid")

APP = Application(master=ROOT)
APP.mainloop()
