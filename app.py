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

        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self.filter_callback)
        self.filter_entry = ttk.Entry(self, textvariable=self.filter_var)
        self.filter_entry.grid(row=4, column=0, sticky=tk.NSEW)

        self.clear_filter = ttk.Button(self, text="Wyczyść filtr", command=self.clear_filter_command)
        self.clear_filter.grid(row=4, column=1, sticky=tk.NSEW)

        self.status = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status)
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)

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
        self.load()

    def load(self):
        text_filter = self.filter_var.get().upper()
        self.load_memory_areas(text_filter=text_filter)
        self.load_constants(text_filter=text_filter)
        self.load_types(text_filter=text_filter)
        self.load_memory_map(text_filter=text_filter)

    def load_memory_areas(self, text_filter=""):
        self.memory_areas_list.delete(*self.memory_areas_list.get_children())
        for area in self.scanner.memory_areas:
            if not text_filter or text_filter in area.var_name.upper() or text_filter in area.type_name.upper():
                self.load_memory_area('', area.var_name, area.type_name, area.offset, area.size)

    def load_memory_area(self, parent_name, var_name, type_name, offset, size):
        values = [str(offset), size, type_name, self.scanner.get_map(offset, size)]
        self.memory_areas_list.insert(parent_name, 'end', var_name, text=var_name, values=values)
        if type_name in self.scanner.type_sizes:
            type_size = self.scanner.type_sizes[type_name]
            field_offset = offset
            for field in type_size.fields:
                field_text = "{}.{}".format(var_name, field)
                field_size = type_size.fields[field]
                field_type = self.scanner.type_sizes[field_size]
                self.load_memory_area(var_name, field_text, field_size, field_offset, field_type.size)
                field_offset += field_type.size
                
    def load_constants(self, text_filter=""):
        self.const_list.delete(*self.const_list.get_children())
        for const_name in self.scanner.global_constants:
            if not text_filter or text_filter in const_name.upper():
                const_values = [str(self.scanner.global_constants[const_name])]
                self.const_list.insert('', 'end', const_name, text=const_name, values=const_values)

    def load_types(self, text_filter=""):
        self.types_list.delete(*self.types_list.get_children())
        for type_size in self.scanner.type_sizes:
            text_filter_positive = text_filter in type_size.upper()
            for field in self.scanner.type_sizes[type_size].fields:
                field_value = str(self.scanner.type_sizes[type_size].fields[field])
                text_filter_positive = text_filter_positive or text_filter in field.upper() or text_filter in field_value.upper()
            if text_filter_positive:
                type_values = [str(self.scanner.type_sizes[type_size].size)]
                self.types_list.insert('', 'end', type_size, text=type_size, values=type_values)
                for field in self.scanner.type_sizes[type_size].fields:
                    field_values = [str(self.scanner.type_sizes[type_size].fields[field])]
                    self.types_list.insert(type_size, 'end', text=field, values=field_values)

    def load_memory_map(self, text_filter=""):
        self.mem_list.delete(*self.mem_list.get_children())
        for mem in self.scanner.memory_map:
            mem_value = str(self.scanner.memory_map[mem])
            if not text_filter or text_filter in mem_value.upper():
                mem_values = [mem_value]
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

    def clear_filter_command(self):
        self.filter_var.set("")

    def filter_callback(self, a, b, c):
        self.load()

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
