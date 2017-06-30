import os
import re

class TwinCatMemoryArea:

    def __init__(self):
        self.var_name = ""
        self.offset = 0
        self.type_name = ""
        self.size = 1

class TwinCatType:

    def __init__(self, size=1):
        self.size = size
        self.fields = {}

class TwinCatScanner:

    def __init__(self):
        r'''
        REGEX special chars
        .    - char
        \w   - non whitespace char
        \s   - whitespace char
        \d   - digit
        REGEX modifiers
        ()   - group, in results
        (?:) - group, not in results
        *    - 0 or more, as many as possible
        +    - 1 or more, as many as possible
        *?   - 0 or more, as few as possible
        +?   - 1 or more, as few as possible
        '''
        variable_regex = r'(\w+)\s+AT\s*%M.?(\d+)\s*:\s*(.*?)\s*;'
        self.variable_pattern = re.compile(variable_regex, flags=re.DOTALL)
        comments_regex = r'\(\*.+?\*\)'
        self.comments_pattern = re.compile(comments_regex, flags=re.DOTALL)
        constants_regex = r'VAR_GLOBAL CONSTANT\s+(.+?)\s+END_VAR'
        self.constants_pattern = re.compile(constants_regex, flags=re.DOTALL)
        const_field_regex = r'(\w+)\s*:\s*(\w+)\s*:=\s*(\d+)\s*;'
        self.conts_field_pattern = re.compile(const_field_regex, flags=re.DOTALL)
        type_regex = r'TYPE\s+(\w+)\s*:\s*STRUCT\s+(.+?)\s+END_STRUCT\s+END_TYPE'
        self.type_pattern = re.compile(type_regex, flags=re.DOTALL)
        type_field_regex = r'(\w+)\s*:\s*(.+?)(?:\s*:=\s*[^;]+)?\s*;'
        self.type_field_pattern = re.compile(type_field_regex, flags=re.DOTALL)
        array_regex = r'ARRAY\s*\[(.+?)\]\s*OF\s+(\w+)'
        self.array_pattern = re.compile(array_regex, flags=re.DOTALL)
        array_index_regex = r'(\w+)\.\.(\w+)'
        self.array_index_pattern = re.compile(array_index_regex, flags=re.DOTALL)
        string_regex = r'STRING\((\w+)\)'
        self.string_pattern = re.compile(string_regex, flags=re.DOTALL)

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
        file_content = self.remove_comments(file_content)
        self.scan_global_constants(file_content)
        self.scan_type_structs(file_content)
        lines = self.variable_pattern.findall(file_content)
        return lines

    def remove_comments(self, file_content):
        return self.comments_pattern.sub("", file_content)

    def scan_global_constants(self, file_content):
        constants_blocks = self.constants_pattern.findall(file_content)
        for constants_block in constants_blocks:
            field_blocks = self.conts_field_pattern.findall(constants_block)
            for field in field_blocks:
                field_name = field[0]
                # field_type = field[1]
                field_value = field[2]
                self.global_constants[field_name] = int(field_value)
                print("--- CONSTANT %s := %s" % (field_name, field_value))

    def scan_type_structs(self, file_content):
        type_struct_blocks = self.type_pattern.findall(file_content)
        for type_struct_block in type_struct_blocks:
            type_struct_name = type_struct_block[0]
            type_struct_size = 0
            self.type_sizes[type_struct_name] = TwinCatType(type_struct_size)
            field_blocks = self.type_field_pattern.findall(type_struct_block[1])
            for field in field_blocks:
                field_name = field[0]
                field_type = field[1]
                self.type_sizes[type_struct_name].fields[field_name] = field_type
                field_size = self.get_size(field_type)
                type_struct_size = type_struct_size + field_size
            self.type_sizes[type_struct_name].size = type_struct_size
            print("--- TYPE %s := %d" % (type_struct_name, type_struct_size))

    def scan_lines(self, lines):
        self.notify("przetwarzam pliki")
        areas = []
        for line in lines:
            area = TwinCatMemoryArea()
            area.var_name = line[0]
            area.offset = int(line[1])
            area.type_name = line[2]
            area.size = self.get_size(area.type_name)
            areas.append(area)

        areas.sort(key=lambda area: area.var_name.lower())
        areas.sort(key=lambda area: area.offset)

        for area in areas:
            for current_adr in range(area.offset, area.offset + area.size):
                if current_adr not in self.memory_map:
                    self.memory_map[current_adr] = area.var_name
                else:
                    self.memory_map[current_adr] += ", {}".format(area.var_name)

        self.notify("")
        return areas

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
        array_block = self.array_pattern.match(type_name)
        array_indexes = self.array_index_pattern.findall(array_block[1])
        array_total_size = 1
        for array_index in array_indexes:
            array_limit = [0, 0]
            for i in range(2):
                array_limit[i] = self.get_number(array_index[i], 0)
            array_size = abs(array_limit[1] - array_limit[0]) + 1
            array_total_size = array_total_size * array_size
        array_type = array_block[2]
        array_type_size = self.get_size(array_type)
        return array_total_size * array_type_size

    def get_string_size(self, type_name):
        string_block = self.string_pattern.match(type_name)
        if string_block is not None:
            return self.get_number(string_block[1], 80) + 1
        else:
            return 81

    def get_number(self, number_str, default_numer):
        if number_str in self.global_constants:
            return self.global_constants[number_str]
        elif number_str.isdigit():
            return int(number_str)
        else:
            return default_numer

    def get_map(self, offset, size):
        return " " * offset + "#" * size

