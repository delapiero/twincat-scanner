import os

class TwinCatMemoryArea:

    def __init__(self):
        self.var_name = ""
        self.offset = 0
        self.type_name = ""
        self.size = 1
        self.buffer = ""

    def map(self):
        memmap = ""
        for _ in range(self.offset):
            memmap = memmap + " "
        for _ in range(self.size):
            memmap = memmap + "#"
        return memmap

class TwinCatType:

    def __init__(self, size=1):
        self.size = size
        self.fields = {}

class TwinCatScanner:

    def __init__(self):
        self.clear()

    def clear(self):
        self.memory_areas = []

        self.type_sizes = {
            "BOOL" : TwinCatType(1),
            "BYTE" : TwinCatType(1),
            "WORD" : TwinCatType(2),
            "DWORD" : TwinCatType(4),
            "SINT" : TwinCatType(1),
            "INT" : TwinCatType(2),
            "DINT" : TwinCatType(4),
            "LINT" : TwinCatType(8),
            "USINT" : TwinCatType(1),
            "UINT" : TwinCatType(2),
            "UDINT" : TwinCatType(4),
            "ULINT" : TwinCatType(8),
            "REAL" : TwinCatType(4),
            "LREAL" : TwinCatType(8),
            "TIME" : TwinCatType(4),
            "TIME_OF_DAY" : TwinCatType(4),
            "TOD" : TwinCatType(4),
            "DATE" : TwinCatType(4),
            "DATE_AND_TIME" : TwinCatType(4),
            "DT" : TwinCatType(4),
            "POINTER" : TwinCatType(4),
        }

        self.global_constants = {
            "MAX_STRING_LENGTH" : 255
        }

        self.memory_map = {}

    def notify(self, status):
        """Replace to get status """
        print(status)

    def run(self, rootdir):
        self.clear()
        lines = self.scan_dir(rootdir)
        self.memory_areas = self.scan_lines(lines)

    def scan_dir(self, rootdir):
        self.notify("wczytuje pliki")
        lines = []
        for root, _, files in os.walk(rootdir):
            for path in files:
                print(path)
                if not path.upper().endswith("BAK"):
                    with open(os.path.join(root, path), 'r', errors='replace') as file:
                        file_content = file.read()
                        file_lines = self.scan_file(file_content)
                        lines += file_lines
        self.notify("")
        return lines

    def scan_file(self, file_content):
        lines = []

        file_content = self.remove_comments(file_content)
        self.scan_global_constants(file_content)
        self.scan_type_structs(file_content)

        file_content = file_content.split(";")
        for line in file_content:
            if "%MB" in line:
                lines.append(line)

        return lines

    def remove_comments(self, file_content):
        comments = self.get_text_blocks(file_content, "(*", "*)")
        for comment in comments:
            file_content = file_content.replace(comment, "")
        return file_content

    def scan_global_constants(self, file_content):
        constant_blocks = self.get_text_blocks(file_content, "VAR_GLOBAL CONSTANT", "END_VAR")
        for constant_block in constant_blocks:
            constants = self.strip_block(constant_block, "VAR_GLOBAL CONSTANT", "END_VAR")
            constants = constants.split(";")
            for constant in constants:
                if ":=" in constant:
                    operator_split = constant.split(":=")
                    if ":" in operator_split[0]:
                        type_split = operator_split[0].split(":")
                        global_constant_name = type_split[0].split()[-1].strip()
                        global_constant_value = operator_split[1].strip()
                        if not global_constant_name.isdigit() and global_constant_value.isdigit():
                            self.global_constants[global_constant_name] = int(global_constant_value)
                            print("--- CONSTANT %s := %s" % (global_constant_name, global_constant_value))

    def scan_type_structs(self, file_content):
        type_struct_blocks = self.get_text_blocks(file_content, "TYPE", "END_TYPE")
        for type_struct_block in type_struct_blocks:
            if "STRUCT" in type_struct_block and "END_STRUCT" in type_struct_block:
                self.scan_type_struct(type_struct_block)

    def scan_type_struct(self, type_struct_block):
        type_struct_block = self.strip_block(type_struct_block, "TYPE", "END_TYPE")
        type_struct_size = 0
        struct_split = type_struct_block.split("STRUCT")
        type_struct_name = struct_split[0].strip().rstrip(":").strip()
        self.type_sizes[type_struct_name] = TwinCatType(type_struct_size)
        field_split = struct_split[1].split(";")
        for field in field_split:
            if ":" in field:
                field_type_split = field.split(":")
                field_name = field_type_split[0].split()[-1]
                field_type = field_type_split[1].strip()
                self.type_sizes[type_struct_name].fields[field_name] = field_type
                field_size = self.get_size(field_type)
                type_struct_size = type_struct_size + field_size
        self.type_sizes[type_struct_name].size = type_struct_size
        print("--- TYPE %s := %d" % (type_struct_name, type_struct_size))

    def get_text_blocks(self, content, start, end):
        blocks = []
        start_index = content.find(start)
        end_index = content.find(end, start_index + len(start))
        while start_index > -1 and end_index > -1 and start_index < end_index:
            block = content[start_index:end_index + len(end)]
            blocks.append(block)
            start_index = content.find(start, end_index + len(end))
            end_index = content.find(end, start_index + len(start))
        return blocks

    def strip_block(self, block, start, end):
        return block.strip().lstrip(start).rstrip(end).strip()

    def scan_lines(self, lines):
        self.notify("przetwarzam pliki")
        memory_areas = []
        for line in lines:
            memory_area = self.scan_line(line)
            memory_areas.append(memory_area)
        memory_areas.sort(key=lambda area: area.var_name.lower())
        memory_areas.sort(key=lambda area: area.offset)

        for area in memory_areas:
            area.size = self.get_size(area.type_name)
            for current_adr in range(area.offset, area.offset + area.size):
                if current_adr not in self.memory_map:
                    self.memory_map[current_adr] = area.var_name
                else:
                    self.memory_map[current_adr] = "{}, {}".format(self.memory_map[current_adr], area.var_name)

        self.notify("")
        return memory_areas

    def scan_line(self, line):
        area = TwinCatMemoryArea()
        area.buffer = line.strip()

        name_split = line.split("%MB")
        if len(name_split) == 2:
            offset_split = name_split[1].split(":")

            area.var_name = name_split[0].strip()
            if area.var_name.endswith("AT"):
                area.var_name = area.var_name.rstrip("AT")
            area.var_name = area.var_name.split()[-1]

            offset_str = offset_split[0].strip()
            area.offset = int(offset_str)

            area.type_name = offset_split[1].strip()
            if area.type_name.endswith(";"):
                area.type_name = area.type_name.rstrip(";")

        return area

    def get_size(self, type_name):
        if type_name.startswith("POINTER"):
            return self.type_sizes["POINTER"].size
        elif type_name.startswith("ARRAY"):
            return self.get_array_size(type_name)
        elif type_name.startswith("STRING"):
            return self.get_string_size(type_name)
        elif type_name in self.type_sizes:
            return self.type_sizes[type_name].size
        else:
            return 0

    def get_array_size(self, type_name):
        array_type_and_range = type_name.strip().lstrip("ARRAY").split("OF", 1)
        array_indexes = self.strip_block(array_type_and_range[0], "[", "]").split(",")
        array_total_size = 1
        for array_index in array_indexes:
            array_ranges = array_index.split("..")
            if len(array_ranges) == 2:
                array_limit = [0, 0]
                for i in range(2):
                    if array_ranges[i] in self.global_constants:
                        array_limit[i] = self.global_constants[array_ranges[i]]
                    elif array_ranges[i].isdigit():
                        array_limit[i] = int(array_ranges[i])
                array_size = abs(array_limit[1] - array_limit[0]) + 1
                array_total_size = array_total_size * array_size
        array_type = array_type_and_range[1].strip()
        array_type_size = self.get_size(array_type)
        return array_total_size * array_type_size

    def get_string_size(self, type_name):
        if "(" in type_name:
            size_str = self.strip_block(type_name, "STRING(", ")")
            if size_str.isdigit():
                return int(size_str) + 1
            elif size_str in self.global_constants:
                return self.global_constants[size_str] + 1
        return 80 + 1