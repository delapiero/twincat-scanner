import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import threading
import twincatscanner

class Application(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)

        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.create_widgets()

    def create_widgets(self):

        self.buttons = ttk.Frame(self)
        self.buttons.grid(row=0, column=0, sticky=tk.NSEW)
        self.buttons.columnconfigure(6, weight=1)
        self.buttons.rowconfigure(1, weight=1)

        self.dir_select = ttk.Button(self.buttons, text="Wybierz projekt", command=self.dir_select_command)
        self.dir_select.grid(row=0, column=0, sticky=tk.NSEW)

        self.dir = tk.StringVar()
        self.dir_path = ttk.Entry(self, textvariable=self.dir)
        self.dir_path.grid(row=1, column=0, sticky=tk.NSEW)

        self.dir_process = ttk.Button(self.buttons, text="Skanuj projekt", command=self.dir_process_command_async)
        self.dir_process.grid(row=0, column=1, sticky=tk.NSEW)

        self.export = ttk.Button(self.buttons, text="Zapisz projekt", command=self.csv_command)
        self.export.grid(row=0, column=3, sticky=tk.NSEW)

        self.select_type = ttk.Button(self.buttons, text="Typ", command=self.type_command, state='disabled')
        self.select_type.grid(row=0, column=4, sticky=tk.NSEW)

        self.select_mem_map = ttk.Button(self.buttons, text="Pamięć", command=self.mem_map_command, state='disabled')
        self.select_mem_map.grid(row=0, column=5, sticky=tk.NSEW)

        self.quit = ttk.Button(self, text="Wyjście", command=ROOT.destroy)
        self.quit.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW)

        self.main_area = ttk.Notebook(self)
        self.main_area.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)

        self.tab_names = {0 : "Zmienne", 1 : "Stałe", 2 : "Typy", 3 : "Pamięć"}

        self.memory_areas_list = self.create_tab(self.main_area, self.tab_names[0], ("name", "offset", "size", "type", "overlap count"))
        self.memory_areas_list.column('#0', stretch=tk.NO)
        self.memory_areas_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#2', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#3', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.column('#4', stretch=tk.NO, anchor=tk.CENTER)
        self.memory_areas_list.bind('<<TreeviewSelect>>', self.memory_areas_select_command)
        self.memory_areas_items = []

        self.const_list = self.create_tab(self.main_area, self.tab_names[1], ("name", "value"))
        self.const_list.column('#0', stretch=tk.NO)
        self.const_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.const_items = []

        self.types_list = self.create_tab(self.main_area, self.tab_names[2], ("name", "size"))
        self.types_list.column('#0', stretch=tk.NO)
        self.types_list.column('#1', stretch=tk.NO, anchor=tk.CENTER)
        self.types_items = []

        self.mem_list = self.create_tab(self.main_area, self.tab_names[3], ("adr", "variables"))
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

    def memory_areas_select_command(self, _):
        state = 'normal' if self.memory_areas_list.selection() else 'disabled'
        self.select_type['state'] = state
        self.select_mem_map['state'] = state

    def dir_process_command(self):
        scanner = models.TwinCatScanner()
        scanner.notify = self.app_notify
        path = self.dir_path.get()
        memory_areas, constants, types, memory_map = scanner.run(path)
        self.load(memory_areas, types, constants, memory_map)
        self.memory_areas_select_command(None)

    def dir_process_command_async(self):
        thr = threading.Thread(target=self.dir_process_command)
        thr.daemon = True
        thr.start()

    def load(self, memory_areas, types, constants, memory_map):
        self.app_notify("ładowanie")
        self.load_memory_areas(memory_areas)
        self.load_constants(constants)
        self.load_types(types)
        self.load_memory_map(memory_map)
        self.app_notify("")
        self.refresh_async()

    def refresh(self):
        self.app_notify("odświeżanie")
        text_filter = self.filter_var.get().upper()
        self.refresh_list(self.memory_areas_list, self.memory_areas_items, text_filter=text_filter)
        self.refresh_list(self.const_list, self.const_items, text_filter=text_filter)
        self.refresh_list(self.types_list, self.types_items, text_filter=text_filter)
        self.refresh_list(self.mem_list, self.mem_items, text_filter=text_filter)
        self.app_notify("")

    def refresh_async(self):
        thr = threading.Thread(target=self.refresh)
        thr.daemon = True
        thr.start()

    def refresh_list(self, treeview, items, text_filter=""):
        treeview.delete(*treeview.get_children())
        for item in items:
            if not treeview.exists(item[1]) and self.filter_item(item, text_filter):
                self.insert_item(item, treeview, items)

    def filter_item(self, item, text_filter):
        if not text_filter or text_filter in item[1].upper():
            return True
        for val in item[2]:
            if text_filter in str(val).upper():
                return True
        return False

    def insert_item(self, item, treeview, items):
        if item[0] and not treeview.exists(item[0]):
            for parent in items:
                if parent[1] == item[0]:
                    self.insert_item(parent, treeview, items)
        treeview.insert(item[0], 'end', item[1], text=item[1], values=item[2])

    def load_memory_areas(self, memory_areas):
        self.memory_areas_items.clear()
        for area in memory_areas:
            count = len(list(filter(lambda x, y=area: self.memory_area_overlap(x, y), memory_areas))) - 1
            values = [str(area['offset']), area['size'], area['type_name'], str(count)]
            self.memory_areas_items.append(('', area['var_name'], values))

    def memory_area_overlap(self, area1, area2):
        if area1['size'] and area2['size']:
            r1 = range(area1['offset'], area1['offset'] + area1['size'])
            r2 = range(area2['offset'], area2['offset'] + area2['size'])
            return not ((r1[-1]<r2[0]) or (r2[-1]<r1[0]))
        else:
            return False

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
        import os
        path = self.dir_path.get()
        checked = path if path else "ProgressTwinCatScan"
        basedir = os.path.normpath(checked)
        basename = os.path.basename(basedir)
        selected = self.main_area.index(self.main_area.select())
        filename = "{}_{}".format(basename, self.tab_names[selected])
        csv = tk.filedialog.asksaveasfile(filetypes=[("csv files", "*.csv")], initialfile=filename, defaultextension=".csv")
        if csv is not None:
            if selected == 0:
                self.csv_write(csv, self.memory_areas_list, self.csv_memory_areas)
            elif selected == 1:
                self.csv_write(csv, self.const_list, self.csv_other)
            elif selected == 2:
                self.csv_write(csv, self.types_list, self.csv_other, subitems=True)
            elif selected == 3:
                self.csv_write(csv, self.mem_list, self.csv_other)
            messagebox.showinfo("ProgressTwinCatScanner", "Zapisano plik")
            csv.close()

    def csv_write(self, csv, treeview, csv_format, subitems=False, item=None):
        childen = treeview.get_children(item)
        for child in childen:
            item = treeview.item(child)
            csv.write(csv_format(item))
            if subitems:
                self.csv_write(csv, treeview, csv_format, subitems=True, item=child)

    def csv_memory_areas(self, item):
        return "{};{};{};\n".format(item['text'], item['values'][0], item['values'][2])

    def csv_other(self, item):
        return "{};{};\n".format(item['text'], item['values'][0])

    def type_command(self):
        self.jump(self.types_list, 2, 2)

    def mem_map_command(self):
        self.jump(self.mem_list, 3, 0)

    def jump(self, treeview, treeview_index, value_index):
        selection = self.memory_areas_list.selection()
        if selection is not None:
            selected_item = self.memory_areas_list.item(selection)
            selected_value = selected_item['values'][value_index]
            if treeview.exists(selected_value):
                self.main_area.select(treeview_index)
                treeview.selection_set(selected_value)
                value_index = treeview.index(treeview.selection())
                value_count = len(treeview.get_children())
                if value_count > 0:
                    treeview.yview_moveto(value_index/value_count)

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
