import unittest
import models

class TwinCatScannerTests(unittest.TestCase):

    def setUp(self):
        self.scanner = models.TwinCatScanner()
        self.constants = """
            VAR_GLOBAL CONSTANT
                Const1 : INT := 1;
                Const2 : INT := 5;
            END_VAR
            """
        self.type1 = """
            TYPE ST1 :
            STRUCT
                Field1: BOOL;
                /// Comment
                Field2 :BOOL;
            END_STRUCT
            END_TYPE
            """
        self.type2 = """
            TYPE ST2:
            STRUCT
                Field3:UINT;
                Field4 : UINT;
            END_STRUCT
            END_TYPE
            """
        self.types = self.type1 + self.type2
        self.var = {}
        self.var[0] = "Variable0          : BOOL"
        self.var[1] = "Variable1 AT%MB100 : ST1"
        self.var[2] = "Variable2 AT%MB102 : ST2"
        self.var[3] = "Variable3 AT%MB106 : ARRAY [1..4] OF UINT"
        self.var[4] = "Variable4 AT%MB114 : ARRAY [1..Const2] OF UINT"
        self.var[5] = "Variable5 AT%MB124 : ARRAY [Const1..2,1..Const2] OF REAL"
        self.var[6] = "Variable6 AT%MB164 : POINTER TO BYTE"
        self.var[7] = "Variable7 AT%MB168 : STRING(9)"
        self.var[8] = "Variable8 AT%MB178 : STRING"
        self.var[9] = "Variable9 AT%MB300 : STRING(MAX_STRING_LENGTH)"
        self.content = self.constants + self.type1 + self.type2
        for variable in self.var:
            self.content += self.var[variable] + ";\n"

    def test_scan_file(self):
        lines, constants, types = self.scanner.scan_file(self.content)
        types = self.scanner.compute_type_sizes(types, constants)
        self.assertEqual(1, constants["Const1"])
        self.assertEqual(5, constants["Const2"])
        self.assertEqual(2, types["ST1"]['size'])
        self.assertEqual(4, types["ST2"]['size'])
        self.assertEqual(9, len(lines))

    def test_remove_comments(self):
        content = "out1 (* comment1 *) out2 (* comment2 *) out3"
        content = self.scanner.remove_comments(content)
        self.assertEqual("out1  out2  out3", content)

    def test_scan_global_constants(self):
        constants = self.scanner.scan_global_constants(self.constants)
        self.assertEqual(1, constants["Const1"])
        self.assertEqual(5, constants["Const2"])

    def test_scan_type_structs(self):
        constants = self.scanner.get_defualt_constants()
        types = self.scanner.scan_type_structs(self.types)
        types = self.scanner.compute_type_sizes(types, constants)
        self.assertEqual(2, types["ST1"]['size'])
        self.assertEqual(4, types["ST2"]['size'])

    def test_scan_lines(self):
        lines, constants, types = self.scanner.scan_file(self.content)
        types = self.scanner.compute_type_sizes(types, constants)
        mem_areas, _ = self.scanner.scan_lines(lines, constants, types)

        self.compare(mem_areas[0], "Variable1", 100, "ST1", 2)
        self.compare(mem_areas[1], "Variable2", 102, "ST2", 4)
        self.compare(mem_areas[2], "Variable3", 106, "ARRAY [1..4] OF UINT", 8)
        self.compare(mem_areas[3], "Variable4", 114, "ARRAY [1..Const2] OF UINT", 10)
        self.compare(mem_areas[4], "Variable5", 124, "ARRAY [Const1..2,1..Const2] OF REAL", 40)
        self.compare(mem_areas[5], "Variable6", 164, "POINTER TO BYTE", 4)
        self.compare(mem_areas[6], "Variable7", 168, "STRING(9)", 10)
        self.compare(mem_areas[7], "Variable8", 178, "STRING", 81)
        self.compare(mem_areas[8], "Variable9", 300, "STRING(MAX_STRING_LENGTH)", 256)

    def compare(self, area, var_name, offset, type_name, size=0):
        message = "{} != {}"
        self.assertEqual(var_name, area['var_name'], message.format(var_name, area['var_name']))
        self.assertEqual(offset, area['offset'], message.format(offset, area['offset']))
        self.assertEqual(type_name, area['type_name'], message.format(type_name, area['type_name']))
        if size > 0:
            self.assertEqual(size, area['size'], message.format(size, area['size']))

    def test_get_size(self):
        constants = self.scanner.get_defualt_constants()
        types = self.scanner.get_default_types()
        self.assertEqual(1, self.scanner.get_size("BOOL", constants, types))
        self.assertEqual(4, self.scanner.get_size("POINTER TO BOOL", constants, types))

    def test_get_array_size(self):
        types = self.scanner.get_default_types()
        constants = self.scanner.get_defualt_constants()
        self.assertEqual(2, self.scanner.get_array_size("ARRAY [1..2] OF BOOL", constants, types))
        self.assertEqual(4, self.scanner.get_array_size("ARRAY [1..2] OF UINT", constants, types))
        self.assertEqual(4, self.scanner.get_array_size("ARRAY [1..2,1..2] OF BOOL", constants, types))
        self.assertEqual(8, self.scanner.get_array_size("ARRAY [1..2,1..2] OF UINT", constants, types))

    def test_get_string_size(self):
        constants = self.scanner.get_defualt_constants()
        self.assertEqual(81, self.scanner.get_string_size("STRING", constants))
        self.assertEqual(26, self.scanner.get_string_size("STRING(25)", constants))
        self.assertEqual(256, self.scanner.get_string_size("STRING(MAX_STRING_LENGTH)", constants))

unittest.main()