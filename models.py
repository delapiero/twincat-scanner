import os
import re

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
        lines, constants, types = self.scan_dir(rootdir)
        memory_areas, memory_map = self.scan_lines(lines, constants, types)
        return memory_areas, constants, types, memory_map

    def get_memory_area(self):
        return {
            'var_name' : "",
            'offset' : 0,
            'type_name' : "",
            'size' : 1
        }

    def get_type(self, size=0, fields={}):
        return {
            'size' : size,
            'fields' : fields
        }

    def copy_type(self, twincat_type):
        copy = self.get_type(twincat_type['size'])
        for field in twincat_type['fields']:
            copy['fields'][field] = twincat_type['fields'][field]
        return copy

    def get_default_types(self):
        return {
            "BOOL" : self.get_type(1),
            "BYTE" : self.get_type(1),
            "WORD" : self.get_type(2),
            "DWORD" : self.get_type(4),
            "SINT" : self.get_type(1),
            "INT" : self.get_type(2),
            "DINT" : self.get_type(4),
            "LINT" : self.get_type(8),
            "USINT" : self.get_type(1),
            "UINT" : self.get_type(2),
            "UDINT" : self.get_type(4),
            "ULINT" : self.get_type(8),
            "REAL" : self.get_type(4),
            "LREAL" : self.get_type(8),
            "TIME" : self.get_type(4),
            "TIME_OF_DAY" : self.get_type(4),
            "TOD" : self.get_type(4),
            "DATE" : self.get_type(4),
            "DATE_AND_TIME" : self.get_type(4),
            "DT" : self.get_type(4),
            "POINTER" : self.get_type(4),
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
                        file_lines, file_constants, file_types = self.scan_file(file_content)
                        for line in file_lines:
                            lines.append(line)
                        for file_constant in file_constants:
                            constants[file_constant] = file_constants[file_constant]
                        for file_type in file_types:
                            types[file_type] = self.copy_type(file_types[file_type])
        types_copy = self.compute_type_sizes(types, constants)
        self.notify("")
        return lines, constants, types_copy

    def scan_file(self, file_content):
        file_content = self.remove_comments(file_content)
        constants = self.scan_global_constants(file_content)
        types = self.scan_type_structs(file_content)
        lines = self.variable_pattern.findall(file_content)
        return lines, constants, types

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
                print("--- CONSTANT {} := {}".format(field_name, field_value))
        return constants

    def scan_type_structs(self, file_content):
        types = self.get_default_types()
        type_struct_blocks = self.type_pattern.findall(file_content)
        for type_struct_block in type_struct_blocks:
            type_struct_name = type_struct_block[0]
            types[type_struct_name] = self.get_type()
            field_blocks = self.type_field_pattern.findall(type_struct_block[1])
            for field in field_blocks:
                field_name = field[0]
                field_type = field[1]
                types[type_struct_name]['fields'][field_name] = field_type
            print("--- TYPE {}".format(type_struct_name))
        return types

    def compute_type_sizes(self, types, constants):
        types_copy = {}
        for type_name in types:
            types_copy[type_name] = self.copy_type(types[type_name])
            types_copy[type_name]['size'] = self.compute_type_size(type_name, types, constants)
        return types_copy

    def compute_type_size(self, type_name, types, constants):
        twincat_type = types[type_name]
        if not twincat_type['fields']:
            return twincat_type['size']
        else:
            type_struct_size = 0
            for field in twincat_type['fields']:
                field_type = twincat_type['fields'][field]
                if field_type in types:
                    type_struct_size += self.compute_type_size(field_type, types, constants)
                else:
                    type_struct_size += self.get_size(field_type, constants, types)
            return type_struct_size

    def scan_lines(self, lines, constants, types):
        self.notify("przetwarzam pliki")
        mem_areas = list(map(lambda line: self.scan_line(line, constants, types), lines))
        mem_areas.sort(key=lambda area: area['var_name'].lower())
        mem_areas.sort(key=lambda area: area['offset'])

        mem_map = {}
        for area in mem_areas:
            for current_adr in range(area['offset'], area['offset'] + area['size']):
                if current_adr not in mem_map:
                    mem_map[current_adr] = area['var_name']
                else:
                    mem_map[current_adr] += ", {}".format(area['var_name'])

        self.notify("")
        return mem_areas, mem_map

    def scan_line(self, line, constants, types):
        area = self.get_memory_area()
        area['var_name'] = line[0]
        area['offset'] = int(line[1])
        area['type_name'] = line[2]
        area['size'] = self.get_size(area['type_name'], constants, types)
        return area

    def get_size(self, type_name, constants, types):
        if type_name.startswith("POINTER"):
            return types["POINTER"]['size']
        elif type_name.startswith("ARRAY"):
            return self.get_array_size(type_name, constants, types)
        elif type_name.startswith("STRING"):
            return self.get_string_size(type_name, constants)
        elif type_name in types:
            return types[type_name]['size']
        else:
            return 0

    def get_array_size(self, type_name, constants, types):
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
        array_type_size = self.get_size(array_type, constants, types)
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
