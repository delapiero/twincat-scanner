import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import models

class Application(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)

        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.create_widgets()

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
        self.memory_areas_items = []

        self.const_list = self.create_tab(self.main_area, "Stałe", ("name", "value"))
        self.const_list.column('#0', stretch=tk.NO)
        self.const_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.const_items = []

        self.types_list = self.create_tab(self.main_area, "Typy", ("name", "size"))
        self.types_list.column('#0', stretch=tk.NO)
        self.types_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.types_items = []

        self.mem_list = self.create_tab(self.main_area, "Pamięć", ("adr", "variables"))
        self.mem_list.column('#0', stretch=tk.NO, anchor=tk.CENTER)
        self.mem_list.column('#1', stretch=tk.NO)
        self.mem_items = []

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
        scanner = models.TwinCatScanner()
        scanner.notify = self.app_notify
        path = self.dir_path.get()
        memory_areas, constants, types, memory_map = scanner.run(path)
        self.load(memory_areas, types, constants, memory_map)

    def load(self, memory_areas, types, constants, memory_map):
        self.load_memory_areas(memory_areas, types)
        self.load_constants(constants)
        self.load_types(types)
        self.load_memory_map(memory_map)
        self.refresh()

    def refresh(self):
        text_filter = self.filter_var.get().upper()
        self.refresh_list(self.memory_areas_list, self.memory_areas_items, text_filter=text_filter)
        self.refresh_list(self.const_list, self.const_items, text_filter=text_filter)
        self.refresh_list(self.types_list, self.types_items, text_filter=text_filter)
        self.refresh_list(self.mem_list, self.mem_items, text_filter=text_filter)

    def refresh_list(self, treeview, items, text_filter=""):
        treeview.delete(*treeview.get_children())
        for item in items:
            if not item[0] or treeview.exists(item[0]):
                filter_positive = not text_filter or text_filter in item[1].upper()
                for val in item[2]:
                    filter_positive = filter_positive or text_filter in str(val).upper()
                if filter_positive:
                    treeview.insert(item[0], 'end', item[1], text=item[1], values=item[2])

    def load_memory_areas(self, memory_areas, types):
        self.memory_areas_items.clear()
        for area in memory_areas:
            self.load_memory_area('', area['var_name'], area['type_name'], area['offset'], area['size'], types)

    def load_memory_area(self, parent_name, var_name, type_name, offset, size, types):
        values = [str(offset), size, type_name, " " * offset + "#" * size]
        self.memory_areas_items.append((parent_name, var_name, values))
        if type_name in types:
            twincat_type = types[type_name]
            field_offset = offset
            for field in twincat_type['fields']:
                field_text = "{}.{}".format(var_name, field)
                field_size = twincat_type['fields'][field]
                field_type = types[field_size]
                self.load_memory_area(var_name, field_text, field_size, field_offset, field_type['size'], types)
                field_offset += field_type['size']

    def load_constants(self, constants):
        self.const_items.clear()
        for const_name in constants:
            const_values = [str(constants[const_name])]
            self.const_items.append(('', const_name, const_values))

    def load_types(self, types):
        self.types_items.clear()
        for type_name in types:
            type_values = [str(types[type_name]['size'])]
            self.types_items.append(('', type_name, type_values))
            for field in types[type_name]['fields']:
                field_text = "{}.{}".format(type_name, field)
                field_values = [str(types[type_name]['fields'][field])]
                self.types_items.append((type_name, field_text, field_values))

    def load_memory_map(self, memory_map):
        self.mem_items.clear()
        for mem in memory_map:
            mem_values = [memory_map[mem]]
            self.mem_items.append(('', str(mem), mem_values))

    def app_notify(self, notification):
        self.status.set(notification)

    def csv_command(self):
        csv = tk.filedialog.asksaveasfile(filetypes=[("csv files", "*.csv")])
        if csv is not None:
            for item in self.memory_areas_items:
                csv.write("{};{};{};\n".format(item[1], item[1][0], item[1][2]))
            messagebox.showinfo("ProgressTwinCatScanner", "Zapisano plik")
            csv.close()

    def clear_filter_command(self):
        self.filter_var.set("")

    def filter_callback(self, a, b, c):
        self.refresh()

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
