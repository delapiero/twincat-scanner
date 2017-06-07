import os

class TwinCatMemoryArea:
    var_name = ""
    offset = 0
    type_name = ""
    size = 1
    buffer = ""

    def __lt__(self, other):
        return self.offset < other.offset

class TwinCatScanner:

    def __init__(self):
        self.type_sizes = {
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

        self.global_constants = {
            "MAX_STRING_LENGTH" : 255
        }

    def notify(self, status):
        """Replace to get status """
        print(status)

    def get_memory_areas(self, rootdir):
        lines = self.get_lines(rootdir)
        return self.process_lines(lines)

    def get_lines(self,rootdir):
        self.notify("wczytuje pliki")
        lines = []
        for root, _, files in os.walk(rootdir):
            for path in files:
                print(path)
                if not path.upper().endswith("BAK"):
                    with open(os.path.join(root, path), 'r', errors='surrogateescape') as file:
                        file_content = file.read()
                        file_lines = self.process_content(file_content)
                        lines += file_lines
        self.notify("")
        return lines

    def process_content(self, file_content):
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
            constants = constant_block.strip().lstrip("VAR_GLOBAL CONSTANT").rstrip("END_VAR")
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
                            print("--- CONSTANT {} := {}".format(global_constant_name, str(global_constant_value)))

    def scan_type_structs(self, file_content):
        type_struct_blocks = self.get_text_blocks(file_content, "TYPE", "END_TYPE")
        for type_struct_block in type_struct_blocks:
            if "STRUCT" in type_struct_block:
                type_struct_name, type_struct_size = self.get_type_struct_info(type_struct_block)
                self.type_sizes[type_struct_name] = type_struct_size
                print("--- TYPE " + type_struct_name + " := " + str(type_struct_size))

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
        self.notify("przetwarzam pliki")
        memory_areas = []
        for line in lines:
            memory_area = self.process_memory(line)
            memory_areas.append(memory_area)

        for area in memory_areas:
            area.size = self.get_size(area.type_name)

        memory_areas.sort()
        self.notify("")
        return memory_areas

    def process_memory(self, line):
        area = TwinCatMemoryArea()
        area.buffer = line

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
            elif size_str in self.global_constants:
                return self.global_constants[size_str] + 1
        return 80 + 1

    def get_map(self, offset, size):
        memmap = ""
        for _ in range(offset):
            memmap = memmap + " "
        for _ in range(size):
            memmap = memmap + "#"
        return memmap
