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

        self.grid(row=0, column=0, sticky=N+S+E+W)
        Grid.columnconfigure(self, 0, weight=1)
        Grid.rowconfigure(self, 3, weight=1)

        self.create_widgets()
        self.scanner.notify = self.app_notify

    def create_widgets(self):
        self.dir_path = tk.Entry(self)
        self.dir_path.grid(row=0, column=0, sticky=W+E+N+S)

        self.dir_select = tk.Button(self)
        self.dir_select["text"] = "Wybierz projekt"
        self.dir_select["command"] = self.dir_select_command
        self.dir_select.grid(row=1, column=0, sticky=W+E+N+S)

        self.dir_process = tk.Button(self)
        self.dir_process["text"] = "Wczytaj projekt"
        self.dir_process["command"] = self.dir_process_command
        self.dir_process.grid(row=2, column=0, sticky=W+E+N+S)

        self.main_area = ttk.Notebook(self)
        self.main_area.grid(row=3, column=0, sticky=W+E+N+S)

        main_tab = Frame(self.main_area)
        main_tab.pack(expand=True, fill=BOTH)
        self.main_area.add(main_tab, text="Zmienne")

        self.memory_areas_list = ttk.Treeview(main_tab, columns=("name", "offset", "size", "type", "map"))
        ysb = ttk.Scrollbar(orient=VERTICAL, command=self.memory_areas_list.yview)
        xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.memory_areas_list.xview)
        self.memory_areas_list['yscroll'] = ysb.set
        self.memory_areas_list['xscroll'] = xsb.set

        self.memory_areas_list.heading('#0', text='name')
        self.memory_areas_list.heading('#1', text='offset')
        self.memory_areas_list.heading('#2', text='size')
        self.memory_areas_list.heading('#3', text='type')
        self.memory_areas_list.heading('#4', text='map')
        self.memory_areas_list.column('#0', stretch=tk.NO)
        self.memory_areas_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#2', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#3', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#4', stretch=tk.YES, minwidth=10000)
        self.memory_areas_list.tag_configure('monospace', font=('courier', 10))
        self.memory_areas_list.pack(expand=True, fill=BOTH)
        ysb.grid(row=0, column=1, sticky=NS)
        xsb.grid(row=4, column=0, sticky=EW)

        const_tab = Frame(self.main_area)
        const_tab.pack(expand=True, fill=BOTH)
        self.main_area.add(const_tab, text="Stałe")

        self.const_list = ttk.Treeview(const_tab, columns=("name", "value"))
        const_ysb = ttk.Scrollbar(orient=VERTICAL, command=self.const_list.yview)
        const_xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.const_list.xview)
        self.const_list['yscroll'] = const_ysb.set
        self.const_list['xscroll'] = const_xsb.set

        self.const_list.heading('#0', text='name')
        self.const_list.heading('#1', text='value')
        self.const_list.column('#0', stretch=tk.NO)
        self.const_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.const_list.tag_configure('monospace', font=('courier', 10))
        self.const_list.pack(expand=True, fill=BOTH)
        const_ysb.grid(row=0, column=1, sticky=NS)
        const_xsb.grid(row=4, column=0, sticky=EW)

        types_tab = Frame(self.main_area)
        types_tab.pack(expand=True, fill=BOTH)
        self.main_area.add(types_tab, text="Typy")

        self.types_list = ttk.Treeview(types_tab, columns=("name", "size"))
        types_ysb = ttk.Scrollbar(orient=VERTICAL, command=self.types_list.yview)
        types_xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.types_list.xview)
        self.types_list['yscroll'] = types_ysb.set
        self.types_list['xscroll'] = types_xsb.set

        self.types_list.heading('#0', text='name')
        self.types_list.heading('#1', text='size')
        self.types_list.column('#0', stretch=tk.NO)
        self.types_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.types_list.tag_configure('monospace', font=('courier', 10))
        self.types_list.pack(expand=True, fill=BOTH)
        types_ysb.grid(row=0, column=1, sticky=NS)
        types_xsb.grid(row=4, column=0, sticky=EW)

        mem_tab = Frame(self.main_area)
        mem_tab.pack(expand=True, fill=BOTH)
        self.main_area.add(mem_tab, text="Pamięć")

        self.mem_list = ttk.Treeview(mem_tab, columns=("adr", "variables"))
        mem_ysb = ttk.Scrollbar(orient=VERTICAL, command=self.mem_list.yview)
        mem_xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.mem_list.xview)
        self.mem_list['yscroll'] = mem_ysb.set
        self.mem_list['xscroll'] = mem_xsb.set

        self.mem_list.heading('#0', text='adr')
        self.mem_list.heading('#1', text='variables')
        self.mem_list.column('#0', stretch=tk.NO, anchor=tk.CENTER)
        self.mem_list.column('#1', stretch=tk.NO)
        self.mem_list.tag_configure('monospace', font=('courier', 10))
        self.mem_list.pack(expand=True, fill=BOTH)
        mem_ysb.grid(row=0, column=1, sticky=NS)
        mem_xsb.grid(row=4, column=0, sticky=EW)

        self.quit = tk.Button(self, text="Wyjście", command=root.destroy)
        self.quit.grid(row=5, column=0, sticky=W+E+N+S)

        self.status = StringVar()
        self.status_label = tk.Label(self, textvariable=self.status)
        self.status_label.grid(row=6, column=0, sticky=W+E+N+S)

    def dir_select_command(self):
        tmp_dir = tk.filedialog.askdirectory()
        print(tmp_dir)
        self.dir_path.insert(0, tmp_dir)

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
Grid.rowconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 0, weight=1)

app = Application(master=root)
app.mainloop()
