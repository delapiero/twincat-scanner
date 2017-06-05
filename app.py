import os
import sys
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.filedialog import askdirectory

class memory_area:
	var_name = ""
	offset = 0
	type_name = ""
	size = 1
	buffer = ""

	def __lt__(self, other):
		return self.offset < other.offset

type_sizes = {
	"BOOL" : 1,
	"BYTE" : 1,
	"WORD" : 2,
	"DWORD" : 4,
	"SINT" : 1,
	"INT" : 2,
	"DINT" : 4,
	"LINT" : 8,
	"USINT" : 1,
	"UINT" : 2,
	"UDINT" : 4,
	"ULINT" : 8,
	"REAL" : 4,
	"LREAL" : 8,
	"TIME" : 4,
	"TIME_OF_DAY" : 4,
	"TOD" : 4,
	"DATE" : 4,
	"DATE_AND_TIME" : 4,
	"DT" : 4,
	"POINTER" : 4,
}
		
class Application(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		
		self.grid(row=0, column=0, sticky=N+S+E+W)

		Grid.columnconfigure(self, 0, weight=1)
		Grid.rowconfigure(self, 3, weight=1)
	
		self.create_widgets()

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

		self.memory_areas_list = ttk.Treeview(self, columns=("name","offset","size","type", "buffer", "map"))
		ysb = ttk.Scrollbar(orient=VERTICAL, command= self.memory_areas_list.yview)
		xsb = ttk.Scrollbar(orient=HORIZONTAL, command= self.memory_areas_list.xview)
		self.memory_areas_list['yscroll'] = ysb.set
		self.memory_areas_list['xscroll'] = xsb.set

		self.memory_areas_list.heading('#0', text='name')
		self.memory_areas_list.heading('#1', text='offset')
		self.memory_areas_list.heading('#2', text='size')
		self.memory_areas_list.heading('#3', text='type')
		self.memory_areas_list.heading('#4', text='buffer')
		self.memory_areas_list.heading('#5', text='map')
		self.memory_areas_list.column('#0', stretch=tk.NO)
		self.memory_areas_list.column('#1', stretch=tk.NO)
		self.memory_areas_list.column('#2', stretch=tk.NO)
		self.memory_areas_list.column('#3', stretch=tk.NO)
		self.memory_areas_list.column('#4', stretch=tk.NO)
		self.memory_areas_list.column('#5', stretch=tk.YES)
		self.memory_areas_list.tag_configure('monospace', font='courier')
		self.memory_areas_list.grid(row=3, column=0, sticky=W+E+N+S)
		ysb.grid(row=3, column=1, sticky=NS)
		xsb.grid(row=4, column=0, sticky=EW)

		self.quit = tk.Button(self, text="Wyjście", command=root.destroy)
		self.quit.grid(row=5, column=0, sticky=W+E+N+S)
		
		self.status = StringVar()
		self.status_label = tk.Label(self, textvariable = self.status)
		self.status_label.grid(row=6, column=0, sticky=W+E+N+S)
		

	def dir_select_command(self):
		tmp_dir = tk.filedialog.askdirectory()
		print(tmp_dir)
		self.dir_path.insert(0, tmp_dir)

	def dir_process_command(self):
		memory_areas = self.process_lines(self.get_lines(self.dir_path.get()))
		self.memory_areas_list.delete(*self.memory_areas_list.get_children())
		for area in memory_areas:
			area_description = str(area.offset) + "    " + area.var_name + "    " + area.type_name + "    " + area.buffer
			self.memory_areas_list.insert('', 'end', text=area.var_name,values=[str(area.offset),area.size,area.type_name,area.buffer,self.get_map(area.offset,area.size)],tag='monospace')

	def get_lines(self,rootdir):
		self.status.set("wczytuje pliki")
		lines = []
		for root, subfolders, files in os.walk(rootdir):
			for path in files:
				print(path)
				if not path.upper().endswith("BAK"):
					with open(os.path.join(root,path),'r', errors='surrogateescape') as file:
						for line in file:
							try:
								if "%MB" in line:
									print(line)
									lines.append(line)
							except Exception as e:
								print(str(e))
		self.status.set("")
		return lines

	def process_lines(self,lines):
		self.status.set("przetwarzam pliki")
		memory_areas = []
		for line in lines:
			tmp_area = memory_area()
			tmp_area.buffer = line
			
			name_split = line.split("%MB")
			if len(name_split) == 2:
				offset_split = name_split[1].split(":")
				

				tmp_area.var_name = name_split[0].strip()
				if tmp_area.var_name.endswith("(*"):
					continue
				if tmp_area.var_name.endswith("AT"):
					tmp_area.var_name = tmp_area.var_name.rstrip("AT")

				offset_str = offset_split[0].strip()
				if offset_str.endswith("*)"):
					continue
				tmp_area.offset = int(offset_str)

				tmp_area.type_name = offset_split[1].strip()
				if tmp_area.type_name.endswith(";"):
					tmp_area.type_name = tmp_area.type_name.rstrip(";")
					
				tmp_area.size = self.get_size(tmp_area.type_name)

			memory_areas.append(tmp_area)
		memory_areas.sort()
		self.status.set("")
		return memory_areas
		
	def get_size(self,type_name):
		if type_name.startswith("POINTER"):
			return type_sizes["POINTER"]
		elif type_name.startswith("ARRAY"):
			array_type_and_range = type_name.split("OF")
			array_indexes = array_type_and_range[0].split(",")
			array_total_size = 1
			for array_index in array_indexes:
				array_ranges = array_index.strip().lstrip("ARRAY").strip().lstrip("[").rstrip("]").split("..")
				if array_ranges[0].isdigit() and array_ranges[1].isdigit():
					array_start = int(array_ranges[0])
					array_end = int(array_ranges[1])
					array_size = array_end - array_start + 1
					array_total_size = array_total_size * array_size	
			array_type = array_type_and_range[1].strip()
			array_type_size = 1
			if array_type in type_sizes:
				array_type_size = type_sizes[array_type]
			return array_total_size * array_type_size
		elif type_name in type_sizes:
			return type_sizes[type_name]
		else:
			return 0
			
	def get_map(self,offset,size):
		map = ""
		for i in range(offset):
			map = map + " "
		for i in range(size):
			map = map + "#"
		return map

root = tk.Tk()
Grid.rowconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 0, weight=1)

app = Application(master=root)
app.mainloop()