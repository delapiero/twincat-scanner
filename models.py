import os
import re

class TwinCatMemoryArea:

    def __init__(self):
        self.var_name = ""
        self.offset = 0
        self.type_name = ""
        self.size = 1

class TwinCatType:

    def __init__(self, size=0):
        self.size = size
        self.fields = {}

    def get_copy(self):
        copy = TwinCatType(self.size)
        for field in self.fields:
            copy.fields[field] = self.fields[field]
        return copy

class TwinCatScanner:
    ''' '''
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
    variable_pattern = re.compile(r'(\w+)\s+AT\s*%M.?(\d+)\s*:\s*(.*?)(?:\s*:=\s*[^;]+)?\s*;', flags=re.DOTALL)
    comments_pattern = re.compile(r'\(\*.+?\*\)', flags=re.DOTALL)
    constants_pattern = re.compile(r'VAR_GLOBAL CONSTANT\s+(.+?)\s+END_VAR', flags=re.DOTALL)
    conts_field_pattern = re.compile(r'(\w+)\s*:\s*(\w+)\s*:=\s*(\d+)\s*;', flags=re.DOTALL)
    type_pattern = re.compile(r'TYPE\s+(\w+)\s*:\s*STRUCT\s+(.+?)\s+END_STRUCT\s+END_TYPE', flags=re.DOTALL)
    type_field_pattern = re.compile(r'(\w+)\s*:\s*(.+?)(?:\s*:=\s*[^;]+)?\s*;', flags=re.DOTALL)
    array_pattern = re.compile(r'ARRAY\s*\[(.+?)\]\s*OF\s+(\w+)', flags=re.DOTALL)
    array_index_pattern = re.compile(r'(\w+)\.\.(\w+)', flags=re.DOTALL)
    string_pattern = re.compile(r'STRING\((\w+)\)', flags=re.DOTALL)

    def notify(self, status):
        """Replace to get status """
        print(status)

    def run(self, rootdir):
        lines, types, constants = self.scan_dir(rootdir)
        memory_areas, memory_map = self.scan_lines(lines, types, constants)
        return memory_areas, types, constants, memory_map

    def get_default_types(self):
        return {
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

    def get_defualt_constants(self):
        return {
            "MAX_STRING_LENGTH" : 255
        }

    def scan_dir(self, rootdir):
        self.notify("wczytuje pliki")
        lines = []
        types = self.get_default_types()
        constants = self.get_defualt_constants()
        for root, _, files in os.walk(rootdir):
            for path in files:
                print(path)
                if not path.upper().endswith("BAK"):
                    with open(os.path.join(root, path), 'r', errors='replace') as file:
                        file_content = file.read()
                        file_lines, file_types, file_constants = self.scan_file(file_content)
                        for line in file_lines:
                            lines.append(line)
                        for file_type in file_types:
                            types[file_type] = file_types[file_type].get_copy()
                        for file_constant in file_constants:
                            constants[file_constant] = file_constants[file_constant]
        types_copy = self.compute_type_sizes(types, constants)
        self.notify("")
        return lines, types_copy, constants

    def scan_file(self, file_content):
        file_content = self.remove_comments(file_content)
        constants = self.scan_global_constants(file_content)
        types = self.scan_type_structs(file_content)
        lines = self.variable_pattern.findall(file_content)
        return lines, types, constants

    def remove_comments(self, file_content):
        return self.comments_pattern.sub("", file_content)

    def scan_global_constants(self, file_content):
        constants = self.get_defualt_constants()
        constants_blocks = self.constants_pattern.findall(file_content)
        for constants_block in constants_blocks:
            field_blocks = self.conts_field_pattern.findall(constants_block)
            for field in field_blocks:
                field_name = field[0]
                # field_type = field[1]
                field_value = field[2]
                constants[field_name] = int(field_value)
                print("--- CONSTANT %s := %s" % (field_name, field_value))
        return constants

    def scan_type_structs(self, file_content):
        types = self.get_default_types()
        type_struct_blocks = self.type_pattern.findall(file_content)
        for type_struct_block in type_struct_blocks:
            type_struct_name = type_struct_block[0]
            types[type_struct_name] = TwinCatType()
            field_blocks = self.type_field_pattern.findall(type_struct_block[1])
            for field in field_blocks:
                field_name = field[0]
                field_type = field[1]
                types[type_struct_name].fields[field_name] = field_type
            print("--- TYPE %s" % type_struct_name)
        return types

    def compute_type_sizes(self, types, constants):
        types_copy = {}
        for type_name in types:
            types_copy[type_name] = types[type_name].get_copy()
            types_copy[type_name].size = self.compute_type_size(type_name, types, constants)
        return types_copy

    def compute_type_size(self, type_name, types, constants):
        type_size = types[type_name]
        if not type_size.fields:
            return type_size.size
        else:
            type_struct_size = 0
            for field in type_size.fields:
                field_type = type_size.fields[field]
                field_size = 0
                if field_type in types:
                    field_size = self.compute_type_size(field_type, types, constants)
                else:
                    field_size = self.get_size(field_type, types, constants)
                type_struct_size += field_size
            return type_struct_size

    def scan_lines(self, lines, types, constants):
        self.notify("przetwarzam pliki")
        mem_areas = list(map(lambda line: self.scan_line(line, types, constants), lines))
        mem_areas.sort(key=lambda area: area.var_name.lower())
        mem_areas.sort(key=lambda area: area.offset)

        mem_map = {}
        for area in mem_areas:
            for current_adr in range(area.offset, area.offset + area.size):
                if current_adr not in mem_map:
                    mem_map[current_adr] = area.var_name
                else:
                    mem_map[current_adr] += ", {}".format(area.var_name)

        self.notify("")
        return mem_areas, mem_map

    def scan_line(self, line, types, constants):
        area = TwinCatMemoryArea()
        area.var_name = line[0]
        area.offset = int(line[1])
        area.type_name = line[2]
        area.size = self.get_size(area.type_name, types, constants)
        return area

    def get_size(self, type_name, types, constants):
        if type_name.startswith("POINTER"):
            return types["POINTER"].size
        elif type_name.startswith("ARRAY"):
            return self.get_array_size(type_name, types, constants)
        elif type_name.startswith("STRING"):
            return self.get_string_size(type_name, constants)
        elif type_name in types:
            return types[type_name].size
        else:
            return 0

    def get_array_size(self, type_name, types, constants):
        array_block = self.array_pattern.match(type_name)
        array_indexes = self.array_index_pattern.findall(array_block[1])
        array_total_size = 1
        for array_index in array_indexes:
            array_limit = [0, 0]
            for i in range(2):
                array_limit[i] = self.get_number(array_index[i], constants, 0)
            array_size = abs(array_limit[1] - array_limit[0]) + 1
            array_total_size = array_total_size * array_size
        array_type = array_block[2]
        array_type_size = self.get_size(array_type, types, constants)
        return array_total_size * array_type_size

    def get_string_size(self, type_name, constants):
        string_block = self.string_pattern.match(type_name)
        if string_block is not None:
            return self.get_number(string_block[1], constants, 80) + 1
        else:
            return 81

    def get_number(self, number_str, constants, default_numer):
        if number_str in constants:
            return constants[number_str]
        elif number_str.isdigit():
            return int(number_str)
        else:
            return default_numer
