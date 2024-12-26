from assembler import Assembler
import unittest


class TestAssembler(unittest.TestCase):

    def setUp(self):
        self.assembler = Assembler()

    def test_is_label(self):
        self.assertEqual(True, Assembler.is_label("(LABEL)"), msg="test_is_label0")
        self.assertEqual(False, Assembler.is_label("D=M"), msg="test_is_label1")
        self.assertEqual(False, Assembler.is_label("@LABEL"), msg="test_is_label2")
        self.assertEqual(False, Assembler.is_label("(0LABEL)"), msg="test_is_label3")

    def test_is_symbol(self):
        self.assertEqual(True, Assembler.is_symbol("LABEL"), msg="test_is_symbol0")
        self.assertEqual(False, Assembler.is_symbol("D=M"), msg="test_is_symbol1")
        self.assertEqual(False, Assembler.is_symbol("@LABEL"), msg="test_is_symbol2")
        self.assertEqual(False, Assembler.is_symbol("0LABEL"), msg="test_is_symbol3")

    def test_load_assembly_file(self):
        comparison = [
            "@test\n",
            "@var\n",
            "\n",
            "// comment\n",
            "D=M  // comment\n",
            "(LABEL0)\n",
            "(LABEL1)\n",
            "@20\n"
        ]
        self.assembler.load_assembly_file("test_files/test.asm")
        self.assertEqual(comparison, self.assembler.asm_source, msg="test_load_assembly_file")

    def test_preprocessing(self):
        comparison = [
            "@test",
            "@var",
            "D=M",
            "(LABEL0)",
            "(LABEL1)",
            "@20"
        ]
        self.assembler.load_assembly_file("test_files/test.asm")
        self.assembler.preprocessing()
        self.assertEqual(comparison, self.assembler.preprocessed, msg="test_preprocessing")

    def test_int16_to_binary(self):
        self.assertEqual("0000000000000000", Assembler.int16_to_binary(0), msg="test_int16_to_binary0")
        self.assertEqual("0000000000010000", Assembler.int16_to_binary(16), msg="test_int16_to_binary1")
        self.assertEqual("0000000000100010", Assembler.int16_to_binary(34), msg="test_int16_to_binary2")
        self.assertEqual("0011110110101010", Assembler.int16_to_binary(15786), msg="test_int16_to_binary3")
        self.assertEqual("1111111111111111", Assembler.int16_to_binary(-1), msg="test_int16_to_binary4")
        self.assertEqual("1111100111100100", Assembler.int16_to_binary(-1564), msg="test_int16_to_binary5")

    def test_decode_a_instruction(self):
        self.assembler.symbols["test"] = 10
        self.assembler.symbols["test1"] = 100
        self.assertEqual("0000000000001010", self.assembler.decode_a_instruction("@test"),
                         msg="test_decode_a_instruction0")
        self.assertEqual("0000010101001100", self.assembler.decode_a_instruction("@1356"),
                         msg="test_decode_a_instruction1")
        self.assertEqual("0000000000001010", self.assembler.decode_a_instruction("@test"),
                         msg="test_decode_a_instruction2")
        self.assertEqual("0000000001100100", self.assembler.decode_a_instruction("@test1"),
                         msg="test_decode_a_instruction3")


    def test_decode_c_instruction(self):
        self.assertEqual("1111110000010000", self.assembler.decode_c_instruction("D=M"),
                         msg="test_decode_c_instruction0")
        self.assertEqual("1110101010001111", self.assembler.decode_c_instruction("M=0;JMP"),
                         msg="test_decode_c_instruction1")
        self.assertEqual("1111010101111001", self.assembler.decode_c_instruction("AMD=D|M;JGT"),
                         msg="test_decode_c_instruction2")
        with self.assertRaises(SyntaxError, msg="test_decode_c_instruction3"):
                               self.assembler.decode_c_instruction("@qrrhcgza")

    def test_translate(self):
        self.assembler.translate("test_files/test.asm", "test_files")
        with open("test_files/out_test.hack", 'r') as out, open("test_files/test.hack", 'r') as compare_file:
            output = out.readlines()
            compare = compare_file.readlines()
            self.assertEqual(compare, output, msg="test_translate_0")
        self.assembler.translate("test_files/fill.asm", "test_files")
        with open("test_files/out_fill.hack", 'r') as out, open("test_files/fill.hack", 'r') as compare_file:
            output = out.readlines()
            compare = compare_file.readlines()
            self.assertEqual(compare, output, msg="test_translate_1")



