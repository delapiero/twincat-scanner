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

    def test_process_content(self):
        lines = self.scanner.process_content(self.content)
        self.assertEqual(1, self.scanner.global_constants["Const1"])
        self.assertEqual(5, self.scanner.global_constants["Const2"])
        self.assertEqual(2, self.scanner.type_sizes["ST1"])
        self.assertEqual(4, self.scanner.type_sizes["ST2"])
        self.assertEqual(9, len(lines))

    def test_remove_comments(self):
        content = "out1 (* comment1 *) out2 (* comment2 *) out3"
        content = self.scanner.remove_comments(content)
        self.assertEqual("out1  out2  out3", content)

    def test_scan_global_constants(self):
        self.scanner.scan_global_constants(self.constants)
        self.assertEqual(1, self.scanner.global_constants["Const1"])
        self.assertEqual(5, self.scanner.global_constants["Const2"])

    def test_scan_type_structs(self):
        self.scanner.scan_type_structs(self.types)
        self.assertEqual(2, self.scanner.type_sizes["ST1"])
        self.assertEqual(4, self.scanner.type_sizes["ST2"])

    def test_get_text_blocks(self):
        blocks = self.scanner.get_text_blocks(self.types, "TYPE", "END_TYPE")
        self.assertEqual(self.type1.strip(), blocks[0])
        self.assertEqual(self.type2.strip(), blocks[1])

    def test_get_type_struct_info(self):
        name1, size1 = self.scanner.get_type_struct_info(self.type1)
        self.assertEqual("ST1", name1)
        self.assertEqual(2, size1)

        name2, size2 = self.scanner.get_type_struct_info(self.type2)
        self.assertEqual("ST2", name2)
        self.assertEqual(4, size2)

    def test_process_lines(self):
        lines = self.scanner.process_content(self.content)
        areas = self.scanner.process_lines(lines)

        self.compare(areas[0], "Variable1", 100, "ST1", self.var[1], 2)
        self.compare(areas[1], "Variable2", 102, "ST2", self.var[2], 4)
        self.compare(areas[2], "Variable3", 106, "ARRAY [1..4] OF UINT", self.var[3], 8)
        self.compare(areas[3], "Variable4", 114, "ARRAY [1..Const2] OF UINT", self.var[4], 10)
        self.compare(areas[4], "Variable5", 124, "ARRAY [Const1..2,1..Const2] OF REAL", self.var[5], 40)
        self.compare(areas[5], "Variable6", 164, "POINTER TO BYTE", self.var[6], 4)
        self.compare(areas[6], "Variable7", 168, "STRING(9)", self.var[7], 10)
        self.compare(areas[7], "Variable8", 178, "STRING", self.var[8], 81)
        self.compare(areas[8], "Variable9", 300, "STRING(MAX_STRING_LENGTH)", self.var[9], 256)

    def test_process_memory(self):
        line1 = "Variable1 AT%MB101 : Type1;"
        area1 = self.scanner.process_memory(line1)
        self.assertEqual("Variable1", area1.var_name)
        self.assertEqual(101, area1.offset)
        self.assertEqual("Type1", area1.type_name)
        self.assertEqual(line1, area1.buffer)

        line2 = "Variable2 AT %MB102 : Type2;"
        area2 = self.scanner.process_memory(line2)
        self.assertEqual("Variable2", area2.var_name)
        self.assertEqual(102, area2.offset)
        self.assertEqual("Type2", area2.type_name)
        self.assertEqual(line2, area2.buffer)

    def compare(self, area, var_name, offset, type_name, buffer, size=0):
        message = "{} != {}"
        self.assertEqual(var_name, area.var_name, message.format(var_name, area.var_name))
        self.assertEqual(offset, area.offset, message.format(offset, area.offset))
        self.assertEqual(type_name, area.type_name, message.format(type_name, area.type_name))
        self.assertEqual(buffer, area.buffer, message.format(buffer, area.buffer))
        if size > 0:
            self.assertEqual(size, area.size, message.format(size, area.size))

    def test_get_size(self):
        self.assertEqual(1, self.scanner.get_size("BOOL"))
        self.assertEqual(4, self.scanner.get_size("POINTER TO BOOL"))

    def test_get_array_size(self):
        self.assertEqual(2, self.scanner.get_array_size("ARRAY [1..2] OF BOOL"))
        self.assertEqual(4, self.scanner.get_array_size("ARRAY [1..2] OF UINT"))
        self.assertEqual(4, self.scanner.get_array_size("ARRAY [1..2,1..2] OF BOOL"))
        self.assertEqual(8, self.scanner.get_array_size("ARRAY [1..2,1..2] OF UINT"))

    def test_get_string_size(self):
        self.assertEqual(81, self.scanner.get_string_size("STRING"))
        self.assertEqual(26, self.scanner.get_string_size("STRING(25)"))
        self.assertEqual(256, self.scanner.get_string_size("STRING(MAX_STRING_LENGTH)"))

    def test_get_map(self):
        memmap = self.scanner.get_map(3, 2)
        self.assertEqual("   ##", memmap)

unittest.main()