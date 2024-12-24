from pathlib import Path
import re
import argparse


class JackTokenizer:

    SYMBOLS = ['{', '}', '(', ')', '[', ']', ',', ';', '+', '-', '*', '/', '&', '|', '>', '<', '=', '~', '.']
    KEYWORDS = ['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean',
                'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return']
    IDENTIFIER = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    STRING_CONSTANT = r'^"[^"\n]*"$'

    symbol_xml_format = {'&': '&amp;', '>': '&gt;', '<': '&lt;', '"': '&quot;'}

    def __init__(self, _input_file: Path):
        self.file_path = _input_file
        with open(_input_file, 'r') as file:
            self.input = file.read()
        self.tokens = []
        self.current_token = None

    def format_to_xml(self, out_path: Path):
        with open(out_path, 'w') as file:
            file.write("<tokens>\n")
            while self.has_more_tokens():
                self.advance()

                match self.token_type():
                    case "SYMBOL":
                        _type = "symbol"
                        _value = self.symbol()
                    case "KEYWORD":
                        _type = "keyword"
                        _value = self.keyword()         # only lower for xml output
                    case "IDENTIFIER":
                        _type = "identifier"
                        _value = self.identifier()
                    case "STRING_CONST":
                        _type = "stringConstant"
                        _value = self.string_val()
                    case "INT_CONST":
                        _type = "integerConstant"
                        _value = self.int_val()

                file.write(f"<{_type}> {_value} </{_type}>\n")
            file.write("</tokens>\n")

    def has_more_tokens(self) -> bool:
        # REMOVE LEADING COMMENTS
        self.input = self.input.lstrip()
        com_prefix = self.input[0:2]
        while len(self.input) > 1 and com_prefix in ["//", "/*"]:
            if com_prefix == "//":
                end = self.input.find("\n")
            if com_prefix == "/*":
                end = self.input.find("*/") + 1
            self.input = self.input[end+1:].strip()
            com_prefix = self.input[0:2]

        # CHECK IF MORE TOKENS
        return len(self.input) > 0

    def advance(self) -> None:
        i = 1
        # CHECK FOR STRING CONSTANT
        if self.input[0] == '"':
            while self.input[i] != '"':
                i += 1
            self.current_token = self.input[0:i+1]
            self.input = self.input[i+1:]
            return
        # CHECK FOR SYMBOLS
        if self.input[0] in JackTokenizer.SYMBOLS:
            self.current_token = self.input[0]
            self.input = self.input[1:]
            return
        # CHECK FOR EVERYTHING ELSE
        while i < len(self.input):
            if self.input[i] in [' ', '\n'] + JackTokenizer.SYMBOLS:
                self.current_token = self.input[0:i]
                self.input = self.input[i:]
                return
            i += 1

    def token_type(self) -> str:
        if self.current_token in JackTokenizer.SYMBOLS:
            return "SYMBOL"
        if self.current_token in JackTokenizer.KEYWORDS:
            return "KEYWORD"
        if re.match(JackTokenizer.IDENTIFIER, self.current_token):
            return "IDENTIFIER"
        if re.match(JackTokenizer.STRING_CONSTANT, self.current_token):
            return "STRING_CONST"
        if self.current_token.isnumeric():
            number = int(self.current_token)
            if 0 <= number <= 32767:
                return "INT_CONST"
            raise SyntaxError("Int constant must be included in [0;32767] but: '{self.current_token}' was found.")
        raise SyntaxError(f"Unrecognized token: '{self.current_token}'.")

    def keyword(self) -> str:
        return self.current_token

    def symbol(self, op: str = None) -> chr:
        if op is None:
            op = self.current_token
        return JackTokenizer.symbol_xml_format.get(op, op)

    def identifier(self) -> str:
        return self.current_token

    def int_val(self) -> int:
        return int(self.current_token)

    def string_val(self) -> str:
        return self.current_token.strip('"')


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="Jack Tokenizer")
    arg_parser.add_argument('input', type=str, nargs="?",
                            default=None, help="Path to the input .jack file")

    args = arg_parser.parse_args()

    if args.input is None:
        input_path = input("Enter the input .jack file path\n>")
    else:
        input_path = args.input
    path = Path(input_path)
    jack_tokenizer = JackTokenizer(path)
    output_path = path.parent / (path.stem + "_token.xml")

    jack_tokenizer.format_to_xml(output_path)
