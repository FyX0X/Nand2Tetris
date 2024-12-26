from pathlib import Path
from JackTokenizer import JackTokenizer


class CompilationEngine:
    UNARY_OP = ['~', '-']
    BINARY_OP = ['+', '-', '*', '/', '&amp;', '|', '&lt;', '&gt;', '=']
    KEYWORD_CONST = ["true", "false", "null", "this"]
    CLASS_VAR_DEC_KW = ["static", "field"]
    SUBROUTINE_DEC_KW = ["constructor", "function", "method"]
    TYPE_KW = ["int", "char", "boolean"]
    RETURN_TYPE_KW = ["int", "char", "boolean", "void"]
    STATEMENT_KW = ["while", "if", "let", "return", "do"]

    def __init__(self, tokenizer: JackTokenizer):
        self.tokenizer = tokenizer
        self.output = ""
        self.indentation = 0
        self.compile_class()

    def write_file(self, output_path: Path) -> None:
        with open(output_path, 'w') as file:
            file.writelines(self.output)

    def write(self, type: str, value: str | int) -> None:
        self.output += "\t" * self.indentation + f"<{type}> {value} </{type}>\n"

    def write_non_terminal(self, string: str, entry: bool) -> None:
        if entry:
            self.output += "\t" * self.indentation + f"<{'/' * (not entry)}{string}>\n"
            self.indentation += 1
        else:
            self.indentation -= 1
            self.output += "\t" * self.indentation + f"<{'/' * (not entry)}{string}>\n"

    def next(self) -> None:
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def eat(self, expected: str | list) -> None:
        if not self.check(expected):
            raise SyntaxError(f"Expected {expected} but {self.tokenizer.current_token} was found.")
        _type = self.tokenizer.current_type
        token = self.tokenizer.current_token
        self.write(_type, token)
        self.next()

    def eat_type(self, expected: str | list) -> None:
        if not self.check_type(expected):
            raise SyntaxError(f"Expected {expected} but {self.tokenizer.current_type} was found.")
        _type = self.tokenizer.current_type
        token = self.tokenizer.current_token
        self.write(_type, token)
        self.next()

    def check(self, expected: str | list) -> bool:
        if type(expected) is not list:
            expected = [expected]
        return self.tokenizer.current_token in expected

    def check_type(self, expected: str | list) -> bool:
        if type(expected) is not list:
            expected = [expected]
        return self.tokenizer.current_type in expected

    def compile_class(self):
        self.write_non_terminal("class", True)
        self.next()

        self.eat("class")
        self.eat_type("identifier")     # class_name
        self.eat('{')
        while self.check(CompilationEngine.CLASS_VAR_DEC_KW):   # classVarDec*
            self.compile_class_var_dec()
        while self.check(CompilationEngine.SUBROUTINE_DEC_KW):  # subroutineDec*
            self.compile_subroutine_dec()
        self.eat('}')

        self.write_non_terminal("class", False)

    def compile_class_var_dec(self):
        self.write_non_terminal("classVarDec", True)

        self.eat(CompilationEngine.CLASS_VAR_DEC_KW)            # static / field
        if self.check_type("keyword"):
            self.eat(CompilationEngine.TYPE_KW)                 # type | className
        elif self.check_type("identifier"):
            self.eat_type("identifier")
        else:
            raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

        self.eat_type("identifier")         # varName
        while not self.check(';'):          # (, varName)*
            self.eat(',')
            self.eat_type("identifier")     # varName
        self.eat(';')

        self.write_non_terminal("classVarDec", False)

    def compile_subroutine_dec(self):
        self.write_non_terminal("subroutineDec", True)

        self.eat(CompilationEngine.SUBROUTINE_DEC_KW)   # constructor | method | function
        if self.check_type("keyword"):
            self.eat(CompilationEngine.RETURN_TYPE_KW)  # type | className
        elif self.check_type("identifier"):
            self.eat_type("identifier")
        else:
            raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

        self.eat_type("identifier")         # subroutineName
        self.eat('(')
        self.compile_parameter_list()
        self.eat(')')
        self.compile_subroutine_body()

        self.write_non_terminal("subroutineDec", False)

    def compile_parameter_list(self):
        self.write_non_terminal("parameterList", True)

        if not self.check(')'):             # optional
            if self.check_type("keyword"):  # type | className
                self.eat(CompilationEngine.TYPE_KW)
            elif self.check_type("identifier"):
                self.eat_type("identifier")
            else:
                raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

            self.eat_type("identifier")             # varName
            while not self.check(')'):              # (, type varName)*
                self.eat(',')
                if self.check_type("keyword"):      # type | className
                    self.eat(CompilationEngine.TYPE_KW)
                elif self.check_type("identifier"):
                    self.eat_type("identifier")
                else:
                    raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

                self.eat_type("identifier")         # varName
        
        self.write_non_terminal("parameterList", False)

    def compile_subroutine_body(self):
        self.write_non_terminal("subroutineBody", True)

        self.eat('{')
        while self.check("var"):        # varDec*
            self.compile_var_dec()
        self.compile_statements()
        self.eat('}')
        
        self.write_non_terminal("subroutineBody", False)

    def compile_var_dec(self):
        self.write_non_terminal("varDec", True)

        self.eat("var")
        if self.check_type("keyword"):      # type | className
            self.eat(CompilationEngine.TYPE_KW)
        elif self.check_type("identifier"):
            self.eat_type("identifier")
        else:
            raise SyntaxError(f"Excepted variable type but found : {self.tokenizer.current_token}")

        self.eat_type("identifier")         # varName
        while not self.check(';'):          # (, varName)*
            self.eat(',')
            self.eat_type("identifier")     # varName
        self.eat(';')

        self.write_non_terminal("varDec", False)

    def compile_statements(self):
        self.write_non_terminal("statements", True)
        
        while self.check(CompilationEngine.STATEMENT_KW):
            match self.tokenizer.current_token:
                case "while":
                    self.compile_while()
                case "if":
                    self.compile_if()
                case "let":
                    self.compile_let()
                case "return":
                    self.compile_return()
                case "do":
                    self.compile_do()
        
        self.write_non_terminal("statements", False)

    def compile_let(self):
        self.write_non_terminal("letStatement", True)

        self.eat("let")
        self.eat_type("identifier")         # varName
        if self.check('['):                 # optional
            self.eat('[')
            self.compile_expression()
            self.eat(']')
        self.eat('=')
        self.compile_expression()
        self.eat(';')

        self.write_non_terminal("letStatement", False)

    def compile_if(self):
        self.write_non_terminal("ifStatement", True)

        self.eat("if")
        self.eat('(')
        self.compile_expression()
        self.eat(')')
        self.eat('{')
        self.compile_statements()
        self.eat('}')
        if self.check("else"):              # optional else
            self.eat('else')
            self.eat('{')
            self.compile_statements()
            self.eat('}')
        
        self.write_non_terminal("ifStatement", False)

    def compile_while(self):
        self.write_non_terminal("whileStatement", True)

        self.eat("while")
        self.eat('(')
        self.compile_expression()
        self.eat(')')
        self.eat('{')
        self.compile_statements()
        self.eat('}')
        
        self.write_non_terminal("whileStatement", False)

    def compile_do(self):
        self.write_non_terminal("doStatement", True)

        self.eat("do")
        self.write_subroutine_call()
        self.eat(';')
        
        self.write_non_terminal("doStatement", False)

    def write_subroutine_call(self):
        self.eat_type("identifier")     # subroutineName or className | varName
        if self.check('.'):             # optional .
            self.eat('.')
            self.eat_type("identifier")
        self.eat('(')
        self.compile_expression_list()
        self.eat(')')

    def compile_return(self):
        self.write_non_terminal("returnStatement", True)

        self.eat("return")
        if not self.check(';'):         # check beforehand to not generate empty branches
            self.compile_expression()
        self.eat(';')
        
        self.write_non_terminal("returnStatement", False)

    def compile_expression(self):
        self.write_non_terminal("expression", True)

        self.compile_term()
        while self.check(CompilationEngine.BINARY_OP):  # optional operation
            self.eat(CompilationEngine.BINARY_OP)
            self.compile_term()

        self.write_non_terminal("expression", False)

    def compile_term(self):
        self.write_non_terminal("term", True)

        if self.check_type(["integerConstant", "stringConstant"]):
            self.eat_type(["integerConstant", "stringConstant"])
        elif self.check(CompilationEngine.KEYWORD_CONST):
            self.eat(CompilationEngine.KEYWORD_CONST)
        elif self.check('('):       # '(' expr ')'
            self.eat('(')
            self.compile_expression()
            self.eat(')')
        elif self.check(CompilationEngine.UNARY_OP):
            self.eat(CompilationEngine.UNARY_OP)
            self.compile_term()
        elif self.check_type("identifier"):
            if self.tokenizer.peek_token() == '[':              # array entry
                self.eat_type("identifier")                     # variableName
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            elif self.tokenizer.peek_token() in ['(', '.']:     # subroutineCall
                self.write_subroutine_call()
            else:                                               # variableName
                self.eat_type("identifier")

        self.write_non_terminal("term", False)

    def compile_expression_list(self):
        self.write_non_terminal("expressionList", True)

        if not self.check(')'):             # check beforehand to not generate empty branches
            self.compile_expression()
            while self.check(','):          # (, expression)*
                self.eat(',')
                self.compile_expression()
        
        self.write_non_terminal("expressionList", False)
