import os
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

class Application(tk.Frame):

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

	global_constants = {
		"MAX_STRING_LENGTH" : 80
	}

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
		ysb = ttk.Scrollbar(orient=VERTICAL, command=self.memory_areas_list.yview)
		xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.memory_areas_list.xview)
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
		self.memory_areas_list.column('#5', stretch=tk.YES, minwidth=10000)
		self.memory_areas_list.tag_configure('monospace', font='courier')
		self.memory_areas_list.grid(row=3, column=0, sticky=W+E+N+S)
		ysb.grid(row=0, column=1, sticky=NS)
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
		lines = self.get_lines(self.dir_path.get())
		memory_areas = self.process_lines(lines)
		self.memory_areas_list.delete(*self.memory_areas_list.get_children())
		for area in memory_areas:
			area_description = str(area.offset) + "	" + area.var_name + "	" + area.type_name + "	" + area.buffer
			self.memory_areas_list.insert('', 'end', text=area.var_name,values=[str(area.offset),area.size,area.type_name,area.buffer,self.get_map(area.offset,area.size)],tag='monospace')

	def get_lines(self,rootdir):
		self.status.set("wczytuje pliki")
		lines = []
		for root, subfolders, files in os.walk(rootdir):
			for path in files:
				print(path)
				if not path.upper().endswith("BAK"):
					with open(os.path.join(root,path),'r', errors='surrogateescape') as file:
						file_content = file.read()

						comments = self.get_text_blocks(file_content,"(*","*)")
						for comment in comments:
							file_content = file_content.replace(comment,"")

						constant_blocks = self.get_text_blocks(file_content,"VAR_GLOBAL CONSTANT","END_VAR")
						for constant_block in constant_blocks:
							constants = constant_block.strip().lstrip("VAR_GLOBAL CONSTANT").rstrip("END_VAR").strip().split(";")
							for constant in constants:
								if ":=" in constant:
									operator_split = constant.split(":=")
									if ":" in operator_split[0]:
										type_split = operator_split[0].split(":")
										global_constant_name = type_split[0].split()[-1].strip()
										global_constant_value = operator_split[1].strip()
										if not global_constant_name.isdigit() and global_constant_value.isdigit():
											self.global_constants[global_constant_name] = global_constant_value
											print("--- CONSTANT " + global_constant_name + " := " + global_constant_value)

						type_struct_blocks = self.get_text_blocks(file_content,"TYPE","END_TYPE")
						for type_struct_block in type_struct_blocks:
							if "STRUCT" in type_struct_block:
								type_struct_name, type_struct_size = self.get_type_struct_info(type_struct_block)
								self.type_sizes[type_struct_name] = type_struct_size
								print("--- TYPE " + type_struct_name + " := " + str(type_struct_size))

						file_content = file_content.split(";")
						for line in file_content:
							if "%MB" in line:
								lines.append(line)

		self.status.set("")
		return lines

	def get_text_blocks(self, file_content, block_start, block_end):
		blocks = []
		block_start_index = file_content.find(block_start)
		block_end_index = file_content.find(block_end)
		while(block_start_index > -1 and block_end_index > -1 and block_start_index < block_end_index):
			block_end_index = block_end_index + len(block_end)
			block = file_content[block_start_index:block_end_index]
			blocks.append(block)
			block_start_index = block_start_index + len(block_start)	
			block_start_index = file_content.find(block_start, block_start_index)
			block_end_index = file_content.find(block_end, block_end_index)
		return blocks

	def get_type_struct_info(self, type_struct_block):
		type_struct_block = type_struct_block.strip().lstrip("TYPE").rstrip("END_TYPE").strip()
		type_struct_size = 0
		struct_split = type_struct_block.split("STRUCT")
		type_struct_name = struct_split[0].strip().rstrip(":").strip()
		field_split = struct_split[1].split(";")
		for field in field_split:
			if ":" in field:
				field_type_split = field.split(":")
				field_type = field_type_split[1].strip()
				field_size = self.get_size(field_type)
				type_struct_size = type_struct_size + field_size
		return type_struct_name, type_struct_size

	def process_lines(self, lines):
		self.status.set("przetwarzam pliki")	
		memory_areas = []
		for line in lines:
			memory_area = self.process_memory(line)
			memory_areas.append(memory_area)

		for area in memory_areas:
			area.size = self.get_size(area.type_name)

		memory_areas.sort()
		self.status.set("")
		return memory_areas

	def process_memory(self, line):
		tmp_area = memory_area()
		tmp_area.buffer = line

		name_split = line.split("%MB")
		if len(name_split) == 2:
			offset_split = name_split[1].split(":")

			tmp_area.var_name = name_split[0].strip()
			if tmp_area.var_name.endswith("AT"):
				tmp_area.var_name = tmp_area.var_name.rstrip("AT")
			tmp_area.var_name = tmp_area.var_name.split()[-1]

			offset_str = offset_split[0].strip()
			tmp_area.offset = int(offset_str)

			tmp_area.type_name = offset_split[1].strip()
			if tmp_area.type_name.endswith(";"):
				tmp_area.type_name = tmp_area.type_name.rstrip(";")

		return tmp_area

	def get_size(self, type_name):
		if type_name.startswith("POINTER"):
			return self.type_sizes["POINTER"]
		elif type_name.startswith("ARRAY"):
			return self.get_array_size(type_name)
		elif type_name.startswith("STRING"):
			return self.get_string_size(type_name)
		elif type_name in self.type_sizes:
			return self.type_sizes[type_name]
		else:
			return 0

	def get_array_size(self, type_name):
		array_type_and_range = type_name.split("OF")
		array_indexes = array_type_and_range[0].split(",")
		array_total_size = 1
		for array_index in array_indexes:
			array_ranges = array_index.strip().lstrip("ARRAY").strip().lstrip("[").rstrip("]").split("..")
			if array_ranges[0] in self.global_constants:
				array_ranges[0] = self.global_constants[array_ranges[0]]
			if array_ranges[1] in self.global_constants:
				array_ranges[1] = self.global_constants[array_ranges[1]]
			range1_ok = array_ranges[0].isdigit()
			range2_ok = array_ranges[1].isdigit()
			if range1_ok and range2_ok:
				array_start = int(array_ranges[0])
				array_end = int(array_ranges[1])
				array_size = array_end - array_start + 1
				array_total_size = array_total_size * array_size
		array_type = array_type_and_range[1].strip()
		array_type_size = self.get_size(array_type)
		return array_total_size * array_type_size

	def get_string_size(self, type_name):
		if "(" in type_name:
			size_str = type_name.lstrip("STRING(").rstrip(")")
			if size_str.isdigit():
				return int(size_str) + 1
			elif size_str in global_constants:
				return global_constants[size_str] + 1
		return 80 + 1

	def get_map(self,offset,size):
		memmap = ""
		for i in range(offset):
			memmap = memmap + " "
		for i in range(size):
			memmap = memmap + "#"
		return memmap

root = tk.Tk()
Grid.rowconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 0, weight=1)

app = Application(master=root)
app.mainloop()
