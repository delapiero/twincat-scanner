import tkinter as tk
import models

from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.filedialog import askdirectory

class Application(tk.Frame):

    scanner = models.TwinCatScanner()

    def __init__(self, master=None):
        super().__init__(master)

        self.grid(row=0, column=0, sticky=NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.create_widgets()
        self.scanner.notify = self.app_notify

    def create_widgets(self):

        self.dir_select = tk.Button(self)
        self.dir_select["text"] = "Wybierz projekt"
        self.dir_select["command"] = self.dir_select_command
        self.dir_select.grid(row=0, column=0, sticky=NSEW)

        self.dir = StringVar()
        self.dir_path = tk.Entry(self, textvariable=self.dir)
        self.dir_path.grid(row=1, column=0, sticky=NSEW)

        self.dir_process = tk.Button(self)
        self.dir_process["text"] = "Wczytaj projekt"
        self.dir_process["command"] = self.dir_process_command
        self.dir_process.grid(row=2, column=0, sticky=NSEW)

        self.quit = tk.Button(self, text="Wyjście", command=root.destroy)
        self.quit.grid(row=0, column=1, rowspan=3, sticky=NSEW)

        self.main_area = ttk.Notebook(self)
        self.main_area.grid(row=3, column=0, columnspan=2, sticky=NSEW)

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

        self.status = StringVar()
        self.status_label = tk.Label(self, textvariable=self.status)
        self.status_label.grid(row=4, column=0, sticky=W+E+N+S)

    def create_tab(self, master, text, columns):
        tab = Frame(master)
        tab.pack(expand=True, fill=BOTH)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        master.add(tab, text=text)

        tree = ttk.Treeview(tab, columns=columns)
        tab_ysb = ttk.Scrollbar(tab, orient=VERTICAL, command=tree.yview)
        tab_xsb = ttk.Scrollbar(tab, orient=HORIZONTAL, command=tree.xview)
        tree['yscroll'] = tab_ysb.set
        tree['xscroll'] = tab_xsb.set

        size = range(len(columns))
        for i in size:
            tree.heading("#{}".format(str(i)), text=columns[i])

        tree.tag_configure('monospace', font=('courier', 10))

        tree.grid(row=0, column=0, sticky=NSEW)
        tab_ysb.grid(row=0, column=1, sticky=NS)
        tab_xsb.grid(row=1, column=0, sticky=EW)

        return tree

    def dir_select_command(self):
        tmp_dir = tk.filedialog.askdirectory()
        self.dir.set(tmp_dir)

    def dir_process_command(self):
        path = self.dir_path.get()
        lines = self.scanner.get_lines(path)
        memory_areas = self.scanner.process_lines(lines)
        self.memory_areas_list.delete(*self.memory_areas_list.get_children())
        for area in memory_areas:
            area_values = [str(area.offset), area.size, area.type_name, self.scanner.get_map(area.offset, area.size)]
            self.memory_areas_list.insert('', 'end', area.var_name, text=area.var_name, values=area_values, tag='monospace')
        self.const_list.delete(*self.const_list.get_children())
        for const_name in self.scanner.global_constants:
            const_values = [str(self.scanner.global_constants[const_name])]
            self.const_list.insert('', 'end', const_name, text=const_name, values=const_values, tag='monospace')
        self.types_list.delete(*self.types_list.get_children())
        for type_size in self.scanner.type_sizes:
            type_values = [str(self.scanner.type_sizes[type_size].size)]
            self.types_list.insert('', 'end', type_size, text=type_size, values=type_values, tag='monospace')
            for field in self.scanner.type_sizes[type_size].fields:
                field_values = [str(self.scanner.type_sizes[type_size].fields[field])]
                self.types_list.insert(type_size, 'end', text=field, values=field_values, tag='monospace')
        self.mem_list.delete(*self.mem_list.get_children())
        for mem in self.scanner.memory_map:
            mem_values = [str(self.scanner.memory_map[mem])]
            self.mem_list.insert('', 'end', mem, text=mem, values=mem_values, tag='monospace')

    def app_notify(self, notification):
        self.status.set(notification)

root = tk.Tk()
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

app = Application(master=root)
app.mainloop()
