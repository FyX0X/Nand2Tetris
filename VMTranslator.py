from pathlib import Path
import argparse


class Parser:

    def __init__(self, input_file: Path):
        with open(input_file, 'r') as file:
            self.preprocessed = self.preprocessing(file.readlines())
        self.index = 0
        self.current_line = self.preprocessed[0]

    @staticmethod
    def preprocessing(lines: list) -> list:
        """
        Preprocesses the vm code by removing comments, whitespace, and empty lines.

        Iterates through the lines of the vm code, discards comments and trims
        unnecessary whitespace.

        Args:
            lines (list): A list containing all the raw lines from the input vm code file.

        Returns:
             list: the cleaned instructions
        """
        preprocessed = []
        for line in lines:
            cmd, *comments = line.split('//')
            instruction = cmd.strip()
            if instruction != "":
                preprocessed.append(instruction)
        return preprocessed

    def has_more_commands(self) -> bool:
        return self.index < len(self.preprocessed)

    def advance(self) -> None:
        self.current_line = self.preprocessed[self.index]
        self.index += 1

    def get_command_type(self) -> str:
        cmd_type = self.current_line.split()[0]
        match cmd_type:
            case "push":
                return "C_PUSH"
            case "pop":
                return "C_POP"
            case "label":
                return "C_LABEL"
            case "goto":
                return "C_GOTO"
            case "if-goto":
                return "C_IF"
            case "function":
                return "C_FUNCTION"
            case "call":
                return "C_CALL"
            case "return":
                return "C_RETURN"
            case default:
                if cmd_type in ["add", "sub", "neg", "eq", "lt", "gt", "and", "or", "not"]:
                    return "C_ARITHMETIC"

        raise SyntaxError(f"Unknown command type: {cmd_type}.")

    def arg1(self) -> str:
        if self.get_command_type() == "C_RETURN":
            raise Exception("arg1 should not be called with C_RETURN command.")

        if self.get_command_type() == "C_ARITHMETIC":
            return self.current_line.split()[0]
        return self.current_line.split()[1]

    def arg2(self) -> int:
        if self.get_command_type() in ["C_PUSH", "C_POP", "C_FUNCTION", "C_CALL"]:
            return int(self.current_line.split()[2])

        raise Exception(f"arg2 should only be called with C_PUSH, C_POP, C_FUNCTION or C_CALL but was called with {self.get_command_type()}")


class CodeWriter:

    segment_pointer = {
        "local":    "LCL",
        "argument": "ARG",
        "this":     "THIS",
        "that":     "THAT"
    }

    add_sub_instruction = {
        "add": "M=D+M",
        "sub": "M=M-D"
    }

    comparison_instruction = {
        "eq": "D;JEQ",
        "gt": "D;JGT",
        "lt": "D;JLT"
    }

    logic_instruction = {
        "and":  "M=D&M",
        "or":   "M=D|M"
    }

    def __init__(self, output_file_name: str, path: Path):
        self.output_file_name = output_file_name
        self.output_path = path
        self.output = []
        self.next_instruction = 0
        self.call_dictionary = {}
        self.current_function = ".."
        self.current_filename = None

    def set_curr_filename(self, filename: str) -> None:
        self.current_filename = filename

    def write(self, string: str = "", tab: bool = True) -> None:
        s = "    " if tab else ""
        s += string + '\n'
        self.output.append(s)

    def write_init(self) -> None:
        self.write("    // bootstrap")
        # set SP to 256
        self.write("@256")
        self.write("D=A")
        self.write("@SP")
        self.write("M=D")
        # call Sys.init
        self.write_call("Sys.init", 0)
        self.write()

    def write_label(self, label: str) -> None:
        self.write(f"    // label {label}")
        self.write(f"({self.current_function}${label})", tab=False)

    def write_goto(self, label: str) -> None:
        self.write(f"    // goto {label}")
        self.write(f"@{self.current_function}${label}")
        self.write("0;JMP")
        self.write()

    def write_if(self, label: str) -> None:
        self.write(f"    // if-goto {label}")
        self.write("@SP")
        self.write("M=M-1")         # SP = SP-1 => "pops" STACK TOP
        self.write("A=M")           # goes to STACK TOP
        self.write("D=M")
        self.write(f"@{self.current_function}${label}")
        self.write("D;JNE")         # if STACK TOP != 0 => JMP
        self.write()

    def write_function(self, function: str, n_var: int):
        self.write(f"    // function {function} {n_var}")
        self.write(f"({function})", tab=False)
        # function initialisation set all local variables to 0
        self.write("@SP")
        self.write("A=M")
        for i in range(n_var):
            self.write("M=0")
            self.write("@SP")
            self.write("AM=M+1")
        # function start
        self.write()
        self.current_function = function

    def write_call(self, function: str, n_args: int):
        # get call number for return address
        return_number = self.call_dictionary.get(function, 0)
        self.call_dictionary[function] = return_number + 1
        self.write(f"    // call {function} {n_args}")
        # push return address
        self.write(f"@{function}$ret.{return_number}")
        self.write("D=A")
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("M=M+1")
        self.write("")
        self.write("")
        self.write("")
        # save LCL of caller
        self.write("@LCL")
        self.write("D=M")
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("M=M+1")
        # save ARG of caller
        self.write("@ARG")
        self.write("D=M")
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("M=M+1")
        # save THIS of caller
        self.write("@THIS")
        self.write("D=M")
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("M=M+1")
        # save THAT of caller
        self.write("@THAT")
        self.write("D=M")
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("AM=M+1")
        # ARG = SP - 5 - n_args
        self.write("D=A")       # SP
        self.write("@5")
        self.write("D=D-A")     # SP - 5
        self.write(f"@{n_args}")
        self.write("D=D-A")     # SP - 5 - n_args
        self.write("@ARG")
        self.write("M=D")
        # LCL = SP
        self.write("@SP")
        self.write("D=M")
        self.write("@LCL")
        self.write("M=D")
        # goto function
        self.write(f"@{function}")
        self.write("0;JMP")
        # return address label
        self.write(f"({function}$ret.{return_number})", tab=False)
        self.write()

    def write_return(self):
        self.write("    // return")
        # temp var: end_frame = LCL
        self.write("// end_frame")
        self.write("@LCL")
        self.write("D=M")
        self.write("@R13")
        self.write("M=D")
        # temp var: return_address = end_frame - 5
        self.write("// return_address")
        self.write("@5")
        self.write("A=D-A")     # A: end_frame - 5
        self.write("D=M")
        self.write("@R14")
        self.write("M=D")
        # set CALLER STACK TOP to pop() (CALLEE STACK TOP)
        self.write("// pop()")
        self.write("@SP")
        self.write("A=M-1")
        self.write("D=M")
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")
        # SP = ARG + 1
        self.write("// SP = ARG+1")
        self.write("@ARG")
        self.write("D=M+1")
        self.write("@SP")
        self.write("M=D")
        # THAT = *(end_frame-1)
        self.write("// THAT = *(end_frame-1)")
        self.write("@R13")
        self.write("A=M-1")
        self.write("D=M")
        self.write("@THAT")
        self.write("M=D")
        # THIS = *(end_frame-2)
        self.write("// THAT = *(end_frame-1)")
        self.write("@R13")
        self.write("A=M-1")     # -1
        self.write("A=A-1")     # -1
        self.write("D=M")
        self.write("@THIS")
        self.write("M=D")
        # ARG = *(end_frame-3)
        self.write("// THAT = *(end_frame-1)")
        self.write("@R13")
        self.write("D=M")
        self.write("@3")
        self.write("A=D-A")     # end_frame - 3
        self.write("D=M")
        self.write("@ARG")
        self.write("M=D")
        # LCL = *(end_frame-4)
        self.write("// THAT = *(end_frame-1)")
        self.write("@R13")
        self.write("D=M")
        self.write("@4")
        self.write("A=D-A")     # end_frame - 4
        self.write("D=M")
        self.write("@LCL")
        self.write("M=D")
        # goto return address
        self.write("// goto return_address")
        self.write("@R14")
        self.write("A=M")
        self.write("0;JMP")
        self.write()

    def write_arithmetic(self, instruction: str) -> None:
        if instruction in CodeWriter.add_sub_instruction:
            instr = CodeWriter.add_sub_instruction[instruction]
            self.write(f"    // {instruction}")
            self.write("@SP")
            self.write("AM=M-1")       # STACK TOP
            self.write("D=M")
            self.write("A=A-1")     # STACK SECOND
            self.write(instr)
            self.write()
        elif instruction == "neg":
            self.write("    // neg")
            self.write("@SP")
            self.write("A=M-1")
            self.write("M=-M")
            self.write()
        elif instruction in CodeWriter.comparison_instruction:
            comp = CodeWriter.comparison_instruction[instruction]
            self.write(f"   // {instruction}")
            self.write("@SP")
            self.write("AM=M-1")       # STACK TOP
            self.write("D=M")
            self.write("A=A-1")     # STACK SECOND
            self.write("D=M-D")     # D = X - Y
            self.write("M=-1")      # *[SP-1] = -1 TRUE
            self.write(f"@INSTRUCTION_END_{self.next_instruction}")
            self.write(comp)        # jump if TRUE
            self.write("@SP")
            self.write("A=M-1")
            self.write("M=0")      # *[SP-1] = 0; FALSE
            self.write(f"(INSTRUCTION_END_{self.next_instruction})", tab=False)
            self.write()
            self.next_instruction += 1
        elif instruction in CodeWriter.logic_instruction:
            logic = CodeWriter.logic_instruction[instruction]
            self.write(f"    // {instruction}")
            self.write("@SP")
            self.write("AM=M-1")       # STACK TOP
            self.write("D=M")       # Y
            self.write("A=A-1")     # STACK SECOND  (M is X)
            self.write(logic)
            self.write()
        elif instruction == "not":
            self.write("    // not")
            self.write("@SP")
            self.write("A=M-1")     # STACK TOP
            self.write("M=!M")
            self.write()

    def write_push(self, segment: str, index: int) -> None:
        if segment == "constant":
            self.write(f"    // push constant {index}")
            self.write(f"@{index}")
            self.write("D=A")
            self.write("@SP")
            self.write("A=M")
            self.write("M=D")
            self.write("@SP")
            self.write("M=M+1")
            self.write()
        elif segment in CodeWriter.segment_pointer:
            seg = CodeWriter.segment_pointer[segment]
            self.write(f"    // push {segment} {index}")
            # addr = seg + i
            self.write(f"@{index}")
            self.write("D=A")
            self.write(f"@{seg}")
            self.write("A=D+M")
            self.write("D=M")       # Value of seg(i)
            # SP ++
            self.write("@SP")
            self.write("M=M+1")
            # *[SP-1] = *addr
            self.write("A=M-1")     # STACK TOP
            self.write("M=D")
            self.write()
        elif segment == "temp":
            self.write(f"    // push temp {index}")
            # addr = seg + i
            self.write(f"@{index}")
            self.write("D=A")
            self.write("@5")
            self.write("A=D+A")     # A=D+A instead of D+M because 5 is hard coded and not stored in memory
            self.write("D=M")
            # SP ++
            self.write("@SP")
            self.write("M=M+1")
            # *[SP-1] = *addr
            self.write("A=M-1")     # STACK TOP
            self.write("M=D")
            self.write()
        elif segment == "static":
            # stored in global space as symbolic variables @Foo.i
            self.write(f"    // push static {index}")
            self.write(f"@{self.current_filename}.{index}")
            self.write("D=M")       # Value of static(i)
            # SP++
            self.write("@SP")
            self.write("M=M+1")
            # *[SP-1]
            self.write("A=M-1")
            self.write("M=D")
            self.write()
        elif segment == "pointer":
            if index == 0:
                point = "THIS"
            elif index == 1:
                point = "THAT"
            else:
                raise SyntaxError(f"push pointer i command only accepts 0/1 as i but {index} was supplied")
            self.write(f"    // push pointer {index}")
            self.write(f"@{point}")
            self.write("D=M")       # Value of Pointer (This or That)
            self.write("@SP")
            self.write("M=M+1")
            self.write("A=M-1")
            self.write("M=D")
            self.write()

    def write_pop(self, segment: str, index: int) -> None:
        if segment == "constant":
            raise SyntaxError("Cannot pop on constant memory segment")
        elif segment in CodeWriter.segment_pointer:
            seg = CodeWriter.segment_pointer[segment]
            self.write(f"    // pop {segment} {index}")
            # addr = seg(i) -> D
            self.write(f"@{index}")
            self.write("D=A")
            self.write(f"@{seg}")
            self.write("D=D+M")

            self.write("@SP")
            self.write("AM=M-1")    # move to STACK TOP
            self.write("D=D+M")     # addr + val -> D
            # write value
            self.write("A=D-M")     # D - val = addr -> A
            self.write("M=D-A")     # D - addr = val -> Ram[addr]
            self.write()

        elif segment == "temp":
            self.write(f"    // pop temp {index}")
            # addr = seg(i) -> D
            self.write(f"@{index}")
            self.write("D=A")
            self.write(f"@5")
            self.write("D=D+A")

            self.write("@SP")
            self.write("AM=M-1")  # move to STACK TOP
            self.write("D=D+M")  # addr + val -> D
            # write value
            self.write("A=D-M")  # D - val = addr -> A
            self.write("M=D-A")  # D - addr = val -> Ram[addr]
            self.write()
        elif segment == "static":
            # stored in global space as symbolic variables @Foo.i
            self.write(f"    // pop static {index}")
            self.write("@SP")
            self.write("AM=M-1")
            self.write("D=M")
            self.write(f"@{self.current_filename}.{index}")
            self.write("M=D")
            self.write()
        elif segment == "pointer":
            if index == 0:
                pointer = "THIS"
            elif index == 1:
                pointer = "THAT"
            else:
                raise SyntaxError(f"pop pointer i command only accepts 0/1 as i but {index} was supplied")
            self.write(f"    // pop pointer {index}")
            self.write("@SP")
            self.write("AM=M-1")
            self.write("D=M")
            self.write(f"@{pointer}")
            self.write("M=D")
            self.write()

    def write_file(self):
        with open(self.output_path / (self.output_file_name + ".asm"), 'w') as file:
            file.writelines(self.output)


class VMTranslator:
    def __init__(self, input: str):
        if self.is_valid_file(input):
            files = [Path(input)]
        elif self.is_valid_dir(input):
            files = list(Path(input).glob('**/*.vm'))
        else:
            raise ValueError(f"Invalid input path: {input} is not a directory or .vm file.")

        out_filename = Path(input).stem
        out_directory = Path(input).parent

        self.code_writer = CodeWriter(out_filename, out_directory)
        self.code_writer.write_init()
        for file in files:
            self.parser = Parser(file)
            self.code_writer.set_curr_filename(file.stem)
            self.translate()

        self.code_writer.write_file()

    @staticmethod
    def is_valid_file(file):
        path = Path(file)
        if path.is_file() and path.suffix == ".vm":
            return True
        return False

    @staticmethod
    def is_valid_dir(dir):
        path = Path(dir)
        if path.is_dir():
            return True
        return False

    def translate(self):
        while self.parser.has_more_commands():
            self.parser.advance()
            cmd = self.parser.get_command_type()
            match cmd:
                case "C_ARITHMETIC":
                    instruction = self.parser.arg1()
                    self.code_writer.write_arithmetic(instruction)
                case "C_PUSH":
                    segment = self.parser.arg1()
                    index = self.parser.arg2()
                    self.code_writer.write_push(segment, index)
                case "C_POP":
                    segment = self.parser.arg1()
                    index = self.parser.arg2()
                    self.code_writer.write_pop(segment, index)
                case "C_LABEL":
                    label = self.parser.arg1()
                    self.code_writer.write_label(label)
                case "C_GOTO":
                    label = self.parser.arg1()
                    self.code_writer.write_goto(label)
                case "C_IF":
                    label = self.parser.arg1()
                    self.code_writer.write_if(label)
                case "C_FUNCTION":
                    function = self.parser.arg1()
                    n_var = self.parser.arg2()
                    self.code_writer.write_function(function, n_var)
                case "C_RETURN":
                    self.code_writer.write_return()
                case "C_CALL":
                    function = self.parser.arg1()
                    n_args = self.parser.arg2()
                    self.code_writer.write_call(function, n_args)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(description="Hack VM Translator")
    arg_parser.add_argument('input_file', type=str, nargs="?",
                            default=None, help="Path to the input .asm file")

    args = arg_parser.parse_args()

    if args.input_file is None:
        input_file = input("Enter the input VM code file path\n>")
    else:
        input_file = args.input_file

    vmt = VMTranslator(input_file)
