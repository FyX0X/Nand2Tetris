from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine
import argparse
from pathlib import Path
import shutil


class JackCompiler:

    def __init__(self, input_path: Path):
        if type(input_path) is not Path:
            input_path = Path(input_path)
        if self.is_valid_file(input_path):
            files = [Path(input_path)]
            JackCompiler.include_jack_os(input_path.parent)
        elif self.is_valid_dir(input_path):
            files = list(Path(input_path).glob('**/*.jack'))
            JackCompiler.include_jack_os(input_path)
        else:
            raise ValueError(f"Invalid input path: {_input} is not a directory or .jack file.")

        for file in files:
            tokenizer = JackTokenizer(file)
            output_path = file.parent / (file.stem + ".vm")
            compilation_engine = CompilationEngine(tokenizer, output_path)

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

    @staticmethod
    def include_jack_os(output_path: Path):
        jack_os_path = Path("JACK_OS")
        shutil.copytree(jack_os_path, output_path / "Jack_OS", dirs_exist_ok=True)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(description="Jack Analyzer")
    arg_parser.add_argument('input', type=str, nargs="?",
                            default=None, help="Path to the input .jack file or directory")

    args = arg_parser.parse_args()

    if args.input is None:
        _input = input("Enter the input .jack file or directory path\n>")
    else:
        _input = args.input

    jack_compiler = JackCompiler(Path(_input))