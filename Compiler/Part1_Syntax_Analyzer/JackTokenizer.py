from pathlib import Path
import re
import argparse


class JackTokenizer:
    SYMBOLS = ['{', '}', '(', ')', '[', ']', ',', ';', '+', '-', '*', '/', '&', '|', '>', '<', '=', '~', '.']
    KEYWORDS = ['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean',
                'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return']

    SYMBOLS_REGEX = '[\\' + '\\'.join(SYMBOLS) + ']'
    KEYWORDS_REGEX = r'\b(' + '|'.join(KEYWORDS) + r')\b'
    STRING_REGEX = r'"[^"\n]*"'
    INT_REGEX = r"\d+"
    IDENTIFIER_REGEX = r'[a-zA-Z_][a-zA-Z0-9_]*'

    TOKEN_REGEX = rf'{KEYWORDS_REGEX}|({SYMBOLS_REGEX})|({INT_REGEX})|({STRING_REGEX})|({IDENTIFIER_REGEX})'
    TOKEN_REGEX = re.compile(TOKEN_REGEX)
    symbol_xml_format = {'&': '&amp;', '>': '&gt;', '<': '&lt;', '"': '&quot;'}

    def __init__(self, _input_file: Path):
        self.tokens = []
        self.types = []
        self.current_token = None
        self.current_type = None
        with open(_input_file, 'r') as file:
            self.input = file.read()
        self.remove_comments()
        self.tokenize()

    def format_to_xml(self, out_path: Path):
        with open(out_path, 'w') as file:
            file.write("<tokens>\n")
            while self.has_more_tokens():
                self.advance()
                file.write(f"<{self.current_type}> {self.current_token} </{self.current_type}>\n")
            file.write("</tokens>\n")

    def remove_comments(self):
        text = ""
        index = 0
        while index < len(self.input):
            if self.input[index] == '"':
                end = self.input.find('"', index + 1)
                text += self.input[index:end + 1]
                index = end + 1
            elif self.input[index] == '/':
                if self.input[index + 1] == '/':
                    end = self.input.find('\n', index)
                    text += ' '
                    index = end + 1
                elif self.input[index + 1] == '*':
                    end = self.input.find('*/', index)
                    text += ' '
                    index = end + 2
                else:
                    text += self.input[index]
                    index += 1
            else:
                text += self.input[index]
                index += 1
        self.input = text

    def tokenize(self):
        for match in JackTokenizer.TOKEN_REGEX.finditer(self.input):
            # Check which group matched
            if match.group(1):
                token_type = "keyword"
                token_value = match.group(1)
            elif match.group(2):
                token_type = "symbol"
                token_value = JackTokenizer.symbol_xml_format.get(match.group(2), match.group(2))
            elif match.group(3):
                token_type = "integerConstant"
                token_value = int(match.group(3))
                if not (0 <= token_value <= 32767):
                    raise SyntaxError(f"Integer must be included in [0;32767] but: '{self.current_token}' was found.")
            elif match.group(4):
                token_type = "stringConstant"
                token_value = match.group(4).strip('"')
            elif match.group(5):
                token_type = "identifier"
                token_value = match.group(5)
            else:
                raise SyntaxError("Unexpected match")

            self.tokens.append(token_value)
            self.types.append(token_type)

    def has_more_tokens(self) -> bool:
        # CHECK IF MORE TOKENS
        return len(self.tokens) > 0

    def advance(self) -> None:
        self.current_token = self.tokens.pop(0)
        self.current_type = self.types.pop(0)

    def peek_token(self) -> str:
        return self.tokens[0]

    def peek_type(self) -> str:
        return self.types[0]


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
