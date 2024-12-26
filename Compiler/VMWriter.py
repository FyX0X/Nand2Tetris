from pathlib import Path


class VMWriter:

    SEGMENTS = ["constant", "argument", "local", "static", "this", "that", "pointer", "temp"]
    OPERATIONS = ["add", "sub", "neg", "eq", "lt", "gt", "and", "or", "not"]

    def __init__(self, output: Path):
        self.output = ""
        self.output_path = output

    def write_push(self, segment: str, index: int):
        if segment not in VMWriter.SEGMENTS:
            raise ValueError(f"Unexpected push segment: {segment}")
        self.output += f"\tpush {segment} {index}\n"

    def write_pop(self, segment: str, index: int):
        if segment not in VMWriter.SEGMENTS[1:]:    # without const
            raise ValueError(f"Unexpected pop segment: {segment}")
        self.output += f"\tpop {segment} {index}\n"

    def write_arithmetic(self, operation: str):
        if operation not in VMWriter.OPERATIONS:
            raise ValueError(f"Unexpected operation: {operation}")
        self.output += f"\t{operation}\n"

    def write_label(self, label: str):
        self.output += f"label {label}\n"

    def write_goto(self, label: str):
        self.output += f"\tgoto {label}\n"

    def write_if(self, label: str):
        self.output += f"\tif-goto {label}\n"

    def write_call(self, name: str, n_args: int):
        self.output += f"\tcall {name} {n_args}\n"

    def write_function(self, name: str, n_var: int):
        self.output += f"function {name} {n_var}\n"

    def write_return(self):
        self.output += f"\treturn\n"

    def write_file(self):
        with open(self.output_path, 'w') as file:
            file.writelines(self.output)
