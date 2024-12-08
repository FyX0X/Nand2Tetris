import re
import argparse
from pathlib import Path


class Assembler:
    """
        Assembler for the Hack computer architecture, converting assembly language programs
        into machine code (binary) suitable for execution on the Hack machine.

        This class handles the translation of Hack assembly language files into Hack machine
        language, which is a binary representation of the code. It processes both A-instructions
        (which reference variables or memory locations) and C-instructions (which define computations
        and control flow).

        Class Attributes:
            PRE_DEFINED_SYMBOLS (dict): A dictionary containing pre-defined symbols and their corresponding values.
            DEST (dict): A dictionary mapping destination mnemonics to their binary representations.
            COMP (dict): A dictionary mapping computation mnemonics to their binary representations.
            JUMP (dict): A dictionary mapping jump mnemonics to their binary representations.
            LABEL_PATTERN (str): Regular expression pattern for detecting label symbols.
            SYMBOL_PATTERN (str): Regular expression pattern for detecting general symbols (without parenthesis).

        Instances Attributes:
            asm_source (list): List of lines from the input assembly file.
            preprocessed (list): List of preprocessed assembly instructions (without comments and whitespace).
            unlabeled (list): List of instructions without labels.
            symbols (dict): Dictionary containing user-defined symbols and their corresponding values.
            translated (list): List of translated binary instructions.
            next_variable (int): The next available variable number for undefined symbols.
            filename (str): The name of the output file.
    """

    PRE_DEFINED_SYMBOLS = {
        "R0": 0, "R1": 1, "R2": 2, "R3": 3,
        "R4": 4, "R5": 5, "R6": 6, "R7": 7,
        "R8": 8, "R9": 9, "R10": 10, "R11": 11,
        "R12": 12, "R13": 13, "R14": 14, "R15": 15,
        "SCREEN": 16384,
        "KBD": 24576,
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4
    }

    DEST = {
        None:   "000",
        "M":    "001",
        "D":    "010",
        "MD":   "011",
        "A":    "100",
        "AM":   "101",
        "AD":   "110",
        "AMD":  "111"
    }

    COMP = {
        "0":    "0101010",  # a=0, c1=0, c2=1, c3=0, c4=1, c5=0, c6=1
        "1":    "0111111",  # a=0, c1=0, c2=1, c3=1, c4=1, c5=1, c6=1
        "-1":   "0111010",  # a=0, c1=0, c2=1, c3=1, c4=1, c5=0, c6=1
        "D":    "0001100",  # a=0, c1=0, c2=0, c3=0, c4=1, c5=1, c6=0
        "A":    "0110000",  # a=0, c1=0, c2=1, c3=1, c4=0, c5=0, c6=0
        "!D":   "0001101",  # a=0, c1=0, c2=0, c3=0, c4=1, c5=1, c6=1
        "!A":   "0110001",  # a=0, c1=0, c2=1, c3=1, c4=0, c5=0, c6=1
        "-D":   "0001111",  # a=0, c1=0, c2=0, c3=0, c4=1, c5=1, c6=1
        "-A":   "0110011",  # a=0, c1=0, c2=1, c3=1, c4=0, c5=0, c6=1
        "D+1":  "0011111",  # a=0, c1=0, c2=0, c3=1, c4=1, c5=1, c6=1
        "A+1":  "0110111",  # a=0, c1=0, c2=1, c3=1, c4=0, c5=1, c6=1
        "D-1":  "0001110",  # a=0, c1=0, c2=0, c3=0, c4=1, c5=1, c6=0
        "A-1":  "0110010",  # a=0, c1=0, c2=1, c3=1, c4=0, c5=0, c6=0
        "D+A":  "0000010",  # a=0, c1=0, c2=0, c3=0, c4=0, c5=1, c6=0
        "D-A":  "0010011",  # a=0, c1=0, c2=0, c3=1, c4=0, c5=0, c6=1
        "A-D":  "0000111",  # a=0, c1=0, c2=0, c3=0, c4=0, c5=1, c6=1
        "D&A":  "0000000",  # a=0, c1=0, c2=0, c3=0, c4=0, c5=0, c6=0
        "D|A":  "0010101",  # a=0, c1=0, c2=0, c3=1, c4=0, c5=1, c6=0
        "M":    "1110000",  # a=1, c1=1, c2=1, c3=1, c4=0, c5=0, c6=0
        "!M":   "1110001",  # a=1, c1=1, c2=1, c3=1, c4=0, c5=0, c6=1
        "-M":   "1110011",  # a=1, c1=1, c2=1, c3=1, c4=0, c5=0, c6=1
        "M+1":  "1110111",  # a=1, c1=1, c2=1, c3=1, c4=0, c5=1, c6=1
        "M-1":  "1110010",  # a=1, c1=1, c2=1, c3=1, c4=0, c5=0, c6=0
        "D+M":  "1000010",  # a=1, c1=1, c2=0, c3=0, c4=0, c5=1, c6=0
        "D-M":  "1010011",  # a=1, c1=1, c2=0, c3=1, c4=0, c5=0, c6=1
        "M-D":  "1000111",  # a=1, c1=1, c2=0, c3=0, c4=0, c5=1, c6=1
        "D&M":  "1000000",  # a=1, c1=1, c2=0, c3=0, c4=0, c5=0, c6=0
        "D|M":  "1010101",  # a=1, c1=1, c2=0, c3=1, c4=0, c5=1, c6=0
    }

    JUMP = {
        None: "000",  # No jump
        "JGT":  "001",  # Jump if out > 0
        "JEQ":  "010",  # Jump if out == 0
        "JGE":  "011",  # Jump if out >= 0
        "JLT":  "100",  # Jump if out < 0
        "JNE":  "101",  # Jump if out != 0
        "JLE":  "110",  # Jump if out <= 0
        "JMP":  "111",  # Unconditional jump
    }

    LABEL_PATTERN = r"^\([a-zA-Z$._:][a-zA-Z0-9$._:]*\)$"
    SYMBOL_PATTERN = r"^[a-zA-Z$._:][a-zA-Z0-9$._:]*$"

    def __init__(self):
        """Initializes the assembler with default values for instance variables."""
        self.asm_source = None
        self.preprocessed = []
        self.unlabeled = []
        self.symbols = {}
        self.translated = []
        self.next_variable = 16

        self.filename = ""

    def translate(self, source_file_name: str, output_directory: str = "") -> None:
        """
        Translates an assembly file into a machine code file.

        This method performs the full translation process, which includes:
        1. Initializing symbols and other internal state variables.
        2. Loading the assembly source code from the specified file.
        3. Preprocessing the source code to remove comments and whitespace.
        4. Extracting and resolving labels into memory addresses.
        5. Translating instructions into binary machine code.
        6. Writing the final machine code to the destination file.

        Args:
            source_file_name (str): The path to the input assembly file.
            output_directory (str): The path to the output machine code file.
        """

        self.symbols = Assembler.PRE_DEFINED_SYMBOLS
        self.preprocessed = []
        self.unlabeled = []
        self.translated = []
        self.next_variable = 16

        self.load_assembly_file(source_file_name)
        self.preprocessing()
        self.get_labels()
        self.transcription()
        self.write_hack_file(output_directory)

    def load_assembly_file(self, filename: str) -> None:
        """Loads the contents of an assembly file into `asm_source`."""
        if not filename.endswith(".asm"):
            raise ValueError(f"The file {filename} is not of type .asm")
        self.filename = Path(filename).stem
        with open(filename, 'r') as file:
            self.asm_source = file.readlines()

    def preprocessing(self) -> None:
        """
        Preprocesses the assembly source by removing comments, whitespace, and empty lines.

        Iterates through the lines of the assembly source, discards comments and trims
        unnecessary whitespace. Stores the cleaned instructions in the `preprocessed` list.
        """

        for line in self.asm_source:
            cmd, *comments = line.split('//')
            instruction = cmd.strip()
            if instruction != "":
                self.preprocessed.append(instruction)

    @staticmethod
    def is_label(instruction: str) -> bool:
        """Checks if the given instruction matches the label pattern."""
        return bool(re.match(Assembler.LABEL_PATTERN, instruction))

    @staticmethod
    def is_symbol(symbol: str) -> bool:
        """Checks if the given string matches the valid symbol pattern."""
        return bool(re.match(Assembler.SYMBOL_PATTERN, symbol))

    def get_labels(self) -> None:
        """
        Processes the preprocessed assembly instructions to extract and store labels.

        This method iterates over the list of preprocessed instructions. If an instruction is a label
        (i.e., it matches the label pattern), it is added to the symbol table with its corresponding
        line number. Otherwise, the instruction is added to the list of unlabeled instructions.

        Labels are defined as instructions enclosed in parentheses, and they are stored in the
        `symbols` dictionary with their line numbers.
        """

        line_number = -1
        for i in range(len(self.preprocessed)):
            instruction = self.preprocessed[i]

            # check for instruction
            if not Assembler.is_label(instruction):
                line_number += 1
                self.unlabeled.append(instruction)
            else:
                self.add_symbol(instruction.strip('()'), line_number + 1)

    def add_symbol(self, symbol: str, reference: int) -> None:
        """Adds a symbol and its reference to the ´symbols´ dictionary."""

        self.symbols[symbol] = reference

    def new_variable(self, var: str) -> None:
        """Adds a new variable to the symbol table with the next available address."""

        self.symbols[var] = self.next_variable
        self.next_variable += 1

    @staticmethod
    def int16_to_binary(number: int) -> str:
        """
        Converts a given integer to a 16-bit binary string using two's complement for negative numbers.

        This method ensures that the result is always a 16-bit binary string, where negative numbers are
        represented using two's complement. The binary string is returned as a string of '0's and '1's,
        with the most significant bit on the left.

        Args:
            number (int): The integer to convert to binary.

        Returns:
            str: A 16-bit binary string representation of the input integer.
        """
        # 2's complement for negative number:
        if number < 0:
            number += 2**16

        _bin = ["0"]*16
        for i in range(15, -1, -1):
            if number >= 2 ** i:
                number -= 2 ** i
                _bin[15 - i] = "1"
        bin_str = "".join(_bin)
        return bin_str

    def decode_a_instruction(self, instruction: str) -> str:
        """
        Decodes an A-instruction into a 16-bit binary string.

        An A-instruction is identified by its "@" prefix, and the method handles both symbolic
        and numeric values. If the value is symbolic and not already in the symbol table, it is
        added as a new variable. Numeric values are validated to ensure they fit within the
        15-bit range (0 to 32767). The result is returned as a 16-bit binary string.

        Args:
            instruction (str): The A-instruction to decode (e.g., "@2" or "@variable").

        Returns:
            str: The 16-bit binary string representation of the instruction.

        Raises:
            SyntaxError: If the numeric value exceeds the 15-bit range.
        """
        value = instruction[1:]
        if Assembler.is_symbol(value):
            if value not in self.symbols:
                # value is a new variable
                self.new_variable(value)
            # value is now a variable or a label
            number = self.symbols[value]
        else:
            number = int(value)
            # check number is less that 2^15
            if number >= 32768:
                raise SyntaxError(f"A-instruction: @value with  0 <= value <= 32767 but found value {number}")
        return Assembler.int16_to_binary(number)

    @staticmethod
    def decode_c_instruction(instruction) -> str:
        """
        Decodes a C-instruction into a 16-bit binary string.

        A C-instruction specifies computation, destination, and jump conditions. This method
        parses the instruction, validates the components, and converts them to binary
        using predefined tables for destination (`DEST`), computation (`COMP`), and jump (`JUMP`).

        Args:
            instruction (str): The C-instruction to decode (e.g., "D=A", "M;JMP").

        Returns:
            str: The 16-bit binary string representation of the C-instruction.

        Raises:
            SyntaxError: If the instruction syntax is invalid or if any component
                         (destination, computation, or jump) is not recognized.
        """
        *dest, end = instruction.split("=")
        comp, *jump = end.split(';')
        if len(dest) > 1 or len(jump) > 1:
            raise SyntaxError("C-instruction: dest=comp;jump => syntax was not respected")
        dest = dest[0] if len(dest) == 1 else None
        jump = jump[0] if len(jump) == 1 else None
        dest_bit = Assembler.DEST.get(dest)
        if dest_bit is None: raise SyntaxError(f"C-instruction: unknown dest: {dest}")
        comp_bit = Assembler.COMP.get(comp)
        if comp_bit is None: raise SyntaxError(f"C-instruction: unknown comp: {comp}")
        jump_bit = Assembler.JUMP.get(jump)
        if jump_bit is None: raise SyntaxError(f"C-instruction: unknown jump: {jump}")

        return "111"+comp_bit+dest_bit+jump_bit

    def transcription(self):
        """
        Translates the assembly instructions into binary code.

        Processes each instruction in the `unlabeled` list, determines if it is an
        A-instruction or a C-instruction, and converts it into its 16-bit binary representation.
        The binary instructions are stored in the `translated` list.

        Raises:
            SyntaxError: If an invalid instruction is encountered during translation.
        """

        for instruction in self.unlabeled:
            if instruction[0] == "@":
                # A-instruction
                self.translated.append(self.decode_a_instruction(instruction) + '\n')
            else:
                # C-instruction
                self.translated.append(self.decode_c_instruction(instruction) + '\n')

    def write_hack_file(self, directory: str) -> None:
        """Writes the translated binary instructions to a .hack file."""

        path = Path(directory) / (self.filename + ".hack")
        with open(path, 'w') as file:
            self.translated[-1] = self.translated[-1].strip()       # remove last \n
            file.writelines(self.translated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hack Assembler")
    parser.add_argument('input_file', type=str, help="Path to the input .asm file")
    # Output file is optional, default to a name based on the input file
    parser.add_argument('output_directory', type=str, nargs='?',
                        default="", help="Path to the output .hack file (optional)")

    args = parser.parse_args()

    assembler = Assembler()
    assembler.translate(args.input_file, args.output_directory)
