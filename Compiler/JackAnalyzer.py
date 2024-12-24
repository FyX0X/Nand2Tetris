from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine
import argparse
from pathlib import Path


class JackAnalyzer:

    def __init__(self, _input: str):
        if self.is_valid_file(_input):
            files = [Path(_input)]
        elif self.is_valid_dir(_input):
            files = list(Path(_input).glob('**/*.jack'))
        else:
            raise ValueError(f"Invalid input path: {_input} is not a directory or .jack file.")

        for file in files:
            print("=============================")
            print(file)
            print("=============================")
            tokenizer = JackTokenizer(file)
            compilation_engine = CompilationEngine(tokenizer)
            compilation_engine.write_file(file.parent / (file.stem + "_.xml"))

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


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(description="Jack Analyzer")
    arg_parser.add_argument('input', type=str, nargs="?",
                            default=None, help="Path to the input .jack file or directory")

    args = arg_parser.parse_args()

    if args.input is None:
        _input = input("Enter the input .jack file or directory path\n>")
    else:
        _input = args.input

    jack_analyzer = JackAnalyzer(_input)